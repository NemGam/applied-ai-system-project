from typing import Any, Dict, List, Tuple

from .common import _append_unique, _average_targets, _merge_targets, _phrase_in_text, _tokenize
from .constants import (
    AGENT_CLARIFICATION_CHOICES,
    CONTEXT_CUES,
    FLAG_KEYS,
    FREEFORM_FEATURE_CUES,
    GENRE_ALIASES,
    LIST_KEYS,
    MUSIC_DOMAIN_TERMS,
    MOOD_CUES,
    NUMERIC_KEYS,
    OUT_OF_SCOPE_CUES,
)
from .gemini import _post_to_gemini


def heuristic_parse_preferences(user_text: str) -> Dict[str, Any]:
    import re

    text = re.sub(r"\s+", " ", user_text.lower()).strip()
    tokens = set(_tokenize(text))
    favorite_genres: List[str] = []
    favorite_moods: List[str] = []
    favorite_contexts: List[str] = []
    preferred_mood_tags: List[str] = []
    numeric_targets: Dict[str, List[float]] = {}

    for genre, aliases in GENRE_ALIASES.items():
        if any(_phrase_in_text(text, alias) or alias.replace(" ", "") in tokens for alias in aliases):
            _append_unique(favorite_genres, genre)

    for mood, config in MOOD_CUES.items():
        if any(_phrase_in_text(text, keyword) for keyword in config["keywords"]):
            _append_unique(favorite_moods, mood)
            _merge_targets(numeric_targets, config["targets"])
            for tag in config["tags"]:
                _append_unique(preferred_mood_tags, tag)

    for context, config in CONTEXT_CUES.items():
        if any(_phrase_in_text(text, keyword) for keyword in config["keywords"]):
            _append_unique(favorite_contexts, context)
            _merge_targets(numeric_targets, config["targets"])
            for tag in config["tags"]:
                _append_unique(preferred_mood_tags, tag)

    for phrase, additions in FREEFORM_FEATURE_CUES.items():
        if _phrase_in_text(text, phrase):
            _merge_targets(numeric_targets, additions)

    bpm_match = re.search(r"(\d{2,3})\s*bpm", text)
    if bpm_match:
        numeric_targets.setdefault("target_tempo_bpm", []).append(float(bpm_match.group(1)))

    if "late night" in text or "night" in tokens:
        _append_unique(preferred_mood_tags, "nocturnal")
    if "soft" in tokens:
        _append_unique(preferred_mood_tags, "gentle")
    if "warm" in tokens:
        _append_unique(preferred_mood_tags, "warm")

    parsed: Dict[str, Any] = {
        "favorite_genres": favorite_genres,
        "favorite_moods": favorite_moods,
        "favorite_contexts": favorite_contexts,
        "preferred_mood_tags": preferred_mood_tags,
    }
    parsed.update(_average_targets(numeric_targets))
    for key in FLAG_KEYS:
        if numeric_targets.get(key):
            parsed[key] = any(bool(value) for value in numeric_targets[key])
    return parsed


def _has_recommender_signal(user_prefs: Dict[str, Any]) -> bool:
    if any(user_prefs.get(key) for key in LIST_KEYS):
        return True
    if any(user_prefs.get(key) for key in FLAG_KEYS):
        return True
    return any(user_prefs.get(key) is not None for key in NUMERIC_KEYS)


def is_out_of_scope_music_request(user_text: str, parsed_prefs: Dict[str, Any]) -> bool:
    import re

    if _has_recommender_signal(parsed_prefs):
        return False

    text = re.sub(r"\s+", " ", user_text.lower()).strip()
    tokens = set(_tokenize(text))

    allowed_terms = set(MUSIC_DOMAIN_TERMS)
    allowed_terms.update(GENRE_ALIASES.keys())
    allowed_terms.update(MOOD_CUES.keys())
    allowed_terms.update(CONTEXT_CUES.keys())

    if any(term in tokens for term in allowed_terms):
        return False
    if any(_phrase_in_text(text, phrase) for phrase in allowed_terms if " " in phrase):
        return False

    return any(_phrase_in_text(text, cue) for cue in OUT_OF_SCOPE_CUES)


def parse_preferences_with_gemini(user_text: str) -> Tuple[Dict[str, Any], str]:
    prompt = f"""
You convert natural-language music requests into structured recommendation preferences.
Return strict JSON with these keys only:
- favorite_genres: string[]
- favorite_moods: string[]
- favorite_contexts: string[]
- preferred_mood_tags: string[]
- target_energy: number | null
- target_valence: number | null
- target_danceability: number | null
- target_acousticness: number | null
- target_tempo_bpm: number | null
- target_vocal_presence: number | null
- target_instrumental_focus: number | null
- exclude_lyrical_tracks: boolean

Allowed genres: ambient, electronic, hip hop, indie pop, jazz, lofi, pop, rock, synthwave
Allowed moods: chill, energetic, focused, happy, intense, moody, relaxed
Allowed contexts: cafe, commute, deep_work, dinner, night_drive, party, reading, sleep, study, walk, workout
Numeric values should be normalized to 0-1 except tempo in BPM.
Use empty arrays or null when the request does not imply a value.
If the request explicitly asks for no lyrics, lyricless music, or not to have vocals, set exclude_lyrical_tracks to true and push target_vocal_presence low with target_instrumental_focus high.

User request:
{user_text}
""".strip()

    try:
        parsed = _post_to_gemini(prompt, temperature=0.1)
        return normalize_recommender_preferences(parsed), "gemini"
    except Exception:
        return heuristic_parse_preferences(user_text), "heuristic"


def normalize_recommender_preferences(raw_prefs: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "favorite_genres": [],
        "favorite_moods": [],
        "favorite_contexts": [],
        "preferred_mood_tags": [],
    }

    for key in list(normalized):
        raw_value = raw_prefs.get(key, [])
        if isinstance(raw_value, str):
            raw_value = [item.strip() for item in raw_value.split(",")]
        normalized[key] = [str(item).strip().lower() for item in raw_value if str(item).strip()]

    for key in NUMERIC_KEYS:
        value = raw_prefs.get(key)
        if value is None or value == "":
            continue
        try:
            normalized[key] = round(float(value), 3)
        except (TypeError, ValueError):
            continue

    for key in FLAG_KEYS:
        value = raw_prefs.get(key)
        if isinstance(value, bool):
            normalized[key] = value
        elif isinstance(value, str):
            normalized[key] = value.strip().lower() in {"true", "1", "yes"}

    return normalized


def manual_preferences_to_recommender(manual_preferences: Dict[str, Any]) -> Dict[str, Any]:
    raw_tags = manual_preferences.get("preferred_mood_tags", [])
    if isinstance(raw_tags, str):
        raw_tags = [item.strip() for item in raw_tags.split(",")]

    normalized: Dict[str, Any] = {
        "favorite_genres": [manual_preferences["genre"].strip().lower()]
        if manual_preferences.get("genre")
        else [],
        "favorite_moods": [manual_preferences["mood"].strip().lower()]
        if manual_preferences.get("mood")
        else [],
        "favorite_contexts": [manual_preferences["listening_context"].strip().lower()]
        if manual_preferences.get("listening_context")
        else [],
        "preferred_mood_tags": [str(tag).strip().lower() for tag in raw_tags if str(tag).strip()],
    }

    numeric_field_map = {
        "energy": "target_energy",
        "valence": "target_valence",
        "danceability": "target_danceability",
        "acousticness": "target_acousticness",
        "tempo_bpm": "target_tempo_bpm",
        "vocal_presence": "target_vocal_presence",
        "instrumental_focus": "target_instrumental_focus",
    }
    for source_key, target_key in numeric_field_map.items():
        value = manual_preferences.get(source_key)
        if value is None:
            continue
        normalized[target_key] = round(float(value), 3)

    return normalized


def merge_recommender_preferences(
    manual_prefs: Dict[str, Any],
    parsed_prefs: Dict[str, Any],
) -> Dict[str, Any]:
    merged = normalize_recommender_preferences(parsed_prefs)

    for key in LIST_KEYS:
        manual_values = [str(item).strip().lower() for item in manual_prefs.get(key, []) if str(item).strip()]
        parsed_values = [str(item).strip().lower() for item in merged.get(key, []) if str(item).strip()]
        combined: List[str] = []
        for value in manual_values + parsed_values:
            if value and value not in combined:
                combined.append(value)
        merged[key] = combined

    for key in NUMERIC_KEYS:
        if key in manual_prefs and manual_prefs[key] is not None:
            merged[key] = round(float(manual_prefs[key]), 3)

    for key in FLAG_KEYS:
        merged[key] = bool(manual_prefs.get(key) or merged.get(key))

    return merged


def merge_clarification_preferences(
    base_prefs: Dict[str, Any],
    clarification_answer: str,
) -> Dict[str, Any]:
    clarification_prefs = heuristic_parse_preferences(clarification_answer)
    if not _has_recommender_signal(clarification_prefs):
        return normalize_recommender_preferences(base_prefs)
    return merge_recommender_preferences(
        manual_prefs=clarification_prefs,
        parsed_prefs=base_prefs,
    )


def evaluate_agent_confidence(
    user_prefs: Dict[str, Any],
    retrieved_candidates: List[Dict[str, Any]],
    ranked_songs: List[Tuple[Dict[str, Any], float, str]],
) -> Dict[str, Any]:
    normalized_prefs = normalize_recommender_preferences(user_prefs)
    list_signal_count = sum(1 for key in LIST_KEYS if normalized_prefs.get(key))
    numeric_signal_count = sum(1 for key in NUMERIC_KEYS if normalized_prefs.get(key) is not None)
    flag_signal_count = sum(1 for key in FLAG_KEYS if normalized_prefs.get(key))
    total_signal_count = list_signal_count + numeric_signal_count + flag_signal_count

    top_retrieval_score = round(float(retrieved_candidates[0]["retrieval_score"]), 4) if retrieved_candidates else 0.0
    top_rank_score = round(float(ranked_songs[0][1]), 4) if ranked_songs else 0.0
    score_gap = 0.0
    if len(ranked_songs) >= 2:
        score_gap = round(float(ranked_songs[0][1]) - float(ranked_songs[1][1]), 4)

    confidence = "high"
    if total_signal_count <= 1 or top_retrieval_score < 1.35:
        confidence = "low"
    elif total_signal_count <= 2 or top_retrieval_score < 1.8 or top_rank_score < 0.45:
        confidence = "medium"

    return {
        "confidence": confidence,
        "signal_count": total_signal_count,
        "list_signal_count": list_signal_count,
        "numeric_signal_count": numeric_signal_count,
        "flag_signal_count": flag_signal_count,
        "top_retrieval_score": top_retrieval_score,
        "top_rank_score": top_rank_score,
        "score_gap": score_gap,
    }


def choose_agent_clarification_question(user_prefs: Dict[str, Any]) -> Dict[str, Any] | None:
    normalized_prefs = normalize_recommender_preferences(user_prefs)

    if not normalized_prefs.get("favorite_contexts"):
        return {
            "slot": "listening_context",
            "question": "What are you listening for: studying, working out, or driving at night?",
            "choices": AGENT_CLARIFICATION_CHOICES["listening_context"],
        }
    if (
        normalized_prefs.get("target_vocal_presence") is None
        and normalized_prefs.get("target_instrumental_focus") is None
    ):
        return {
            "slot": "vocal_presence",
            "question": "Do you want mostly instrumental tracks, soft vocals, or strong vocals?",
            "choices": AGENT_CLARIFICATION_CHOICES["vocal_presence"],
        }
    if not normalized_prefs.get("favorite_moods"):
        return {
            "slot": "mood",
            "question": "Should this lean more chill, energetic, or moody?",
            "choices": AGENT_CLARIFICATION_CHOICES["mood"],
        }
    if not normalized_prefs.get("favorite_genres"):
        return {
            "slot": "genre",
            "question": "Do you want this closer to lofi, rock, or electronic?",
            "choices": AGENT_CLARIFICATION_CHOICES["genre"],
        }
    return None


def personalize_recommender_preferences(
    parsed_prefs: Dict[str, Any],
    taste_profile_prefs: Dict[str, Any],
    profile_numeric_weight: float = 0.2,
) -> Dict[str, Any]:
    personalized = normalize_recommender_preferences(parsed_prefs)
    normalized_profile = normalize_recommender_preferences(taste_profile_prefs)

    for key in LIST_KEYS:
        parsed_values = [
            str(item).strip().lower()
            for item in personalized.get(key, [])
            if str(item).strip()
        ]
        profile_values = [
            str(item).strip().lower()
            for item in normalized_profile.get(key, [])
            if str(item).strip()
        ]

        if parsed_values:
            personalized[key] = parsed_values
            continue

        personalized[key] = profile_values

    profile_weight = min(max(float(profile_numeric_weight), 0.0), 1.0)
    parsed_weight = 1.0 - profile_weight
    for key in NUMERIC_KEYS:
        parsed_value = personalized.get(key)
        profile_value = normalized_profile.get(key)

        if parsed_value is None and profile_value is None:
            continue
        if parsed_value is None:
            personalized[key] = round(float(profile_value), 3)
            continue
        if profile_value is None:
            personalized[key] = round(float(parsed_value), 3)
            continue

        personalized[key] = round(
            float(parsed_value) * parsed_weight + float(profile_value) * profile_weight,
            3,
        )

    for key in FLAG_KEYS:
        personalized[key] = bool(personalized.get(key) or normalized_profile.get(key))

    return personalized
