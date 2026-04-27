import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple


GENRE_ALIASES = {
    "ambient": ["ambient", "atmospheric"],
    "electronic": ["electronic", "edm"],
    "hip hop": ["hip hop", "hiphop", "rap"],
    "indie pop": ["indie", "indie pop"],
    "jazz": ["jazz"],
    "lofi": ["lofi", "lo-fi"],
    "pop": ["pop"],
    "rock": ["rock"],
    "synthwave": ["synthwave", "retro wave", "retrowave"],
}

MOOD_CUES = {
    "chill": {
        "keywords": ["chill", "calm", "soft", "easygoing", "laid back"],
        "targets": {
            "target_energy": 0.30,
            "target_danceability": 0.38,
            "target_acousticness": 0.76,
            "target_valence": 0.58,
            "target_tempo_bpm": 78.0,
        },
        "tags": ["calm", "gentle", "soft"],
    },
    "focused": {
        "keywords": ["focus", "focused", "study", "studying", "deep work", "coding"],
        "targets": {
            "target_energy": 0.34,
            "target_acousticness": 0.74,
            "target_tempo_bpm": 82.0,
            "target_vocal_presence": 0.24,
            "target_instrumental_focus": 0.82,
        },
        "tags": ["focused", "steady", "immersive"],
    },
    "happy": {
        "keywords": ["happy", "bright", "sunny", "uplifting", "cheerful"],
        "targets": {
            "target_energy": 0.80,
            "target_danceability": 0.82,
            "target_valence": 0.88,
            "target_tempo_bpm": 120.0,
        },
        "tags": ["uplifting", "bright"],
    },
    "intense": {
        "keywords": ["intense", "aggressive", "hard", "power", "workout", "gym"],
        "targets": {
            "target_energy": 0.90,
            "target_danceability": 0.74,
            "target_valence": 0.62,
            "target_tempo_bpm": 138.0,
            "target_vocal_presence": 0.78,
        },
        "tags": ["aggressive", "explosive"],
    },
    "moody": {
        "keywords": ["moody", "dark", "late night", "night drive", "brooding"],
        "targets": {
            "target_energy": 0.68,
            "target_danceability": 0.68,
            "target_valence": 0.42,
            "target_tempo_bpm": 108.0,
        },
        "tags": ["nocturnal", "cinematic", "brooding"],
    },
    "relaxed": {
        "keywords": ["relaxed", "cozy", "warm", "gentle", "quiet"],
        "targets": {
            "target_energy": 0.32,
            "target_acousticness": 0.84,
            "target_danceability": 0.42,
            "target_valence": 0.64,
            "target_tempo_bpm": 74.0,
        },
        "tags": ["warm", "cozy", "gentle"],
    },
    "energetic": {
        "keywords": ["energetic", "hype", "party", "pump up"],
        "targets": {
            "target_energy": 0.86,
            "target_danceability": 0.84,
            "target_valence": 0.76,
            "target_tempo_bpm": 126.0,
        },
        "tags": ["bright", "motivational"],
    },
}

CONTEXT_CUES = {
    "study": {
        "keywords": ["study", "studying", "homework", "reading", "focus", "late-night studying"],
        "targets": {
            "target_energy": 0.32,
            "target_acousticness": 0.78,
            "target_tempo_bpm": 80.0,
            "target_vocal_presence": 0.26,
            "target_instrumental_focus": 0.84,
        },
        "tags": ["focused", "steady", "nocturnal"],
    },
    "deep_work": {
        "keywords": ["deep work", "coding", "programming", "heads down"],
        "targets": {
            "target_energy": 0.38,
            "target_tempo_bpm": 82.0,
            "target_vocal_presence": 0.18,
            "target_instrumental_focus": 0.90,
        },
        "tags": ["immersive", "clear-headed", "steady"],
    },
    "sleep": {
        "keywords": ["sleep", "fall asleep", "bedtime"],
        "targets": {
            "target_energy": 0.22,
            "target_acousticness": 0.88,
            "target_tempo_bpm": 64.0,
            "target_vocal_presence": 0.12,
            "target_instrumental_focus": 0.92,
        },
        "tags": ["weightless", "gentle", "ethereal"],
    },
    "reading": {
        "keywords": ["reading", "book", "library"],
        "targets": {
            "target_energy": 0.34,
            "target_acousticness": 0.86,
            "target_tempo_bpm": 74.0,
            "target_vocal_presence": 0.18,
            "target_instrumental_focus": 0.86,
        },
        "tags": ["nostalgic", "gentle", "rainy"],
    },
    "cafe": {
        "keywords": ["cafe", "coffee shop", "coffeehouse"],
        "targets": {
            "target_energy": 0.42,
            "target_acousticness": 0.76,
            "target_tempo_bpm": 92.0,
            "target_vocal_presence": 0.42,
        },
        "tags": ["warm", "cozy", "unhurried"],
    },
    "night_drive": {
        "keywords": ["night drive", "driving at night", "after dark", "late night drive"],
        "targets": {
            "target_energy": 0.72,
            "target_danceability": 0.70,
            "target_valence": 0.46,
            "target_tempo_bpm": 110.0,
        },
        "tags": ["nocturnal", "cinematic", "neon"],
    },
    "workout": {
        "keywords": ["workout", "gym", "run", "running", "training"],
        "targets": {
            "target_energy": 0.92,
            "target_danceability": 0.82,
            "target_valence": 0.74,
            "target_tempo_bpm": 136.0,
            "target_vocal_presence": 0.82,
        },
        "tags": ["motivational", "adrenaline", "confident"],
    },
    "party": {
        "keywords": ["party", "pregame", "celebration"],
        "targets": {
            "target_energy": 0.88,
            "target_danceability": 0.86,
            "target_valence": 0.82,
            "target_tempo_bpm": 124.0,
        },
        "tags": ["carefree", "uplifting", "bright"],
    },
    "commute": {
        "keywords": ["commute", "morning train", "bus ride"],
        "targets": {
            "target_energy": 0.70,
            "target_danceability": 0.72,
            "target_valence": 0.74,
            "target_tempo_bpm": 112.0,
        },
        "tags": ["bright", "steady"],
    },
    "walk": {
        "keywords": ["walk", "walking", "stroll"],
        "targets": {
            "target_energy": 0.58,
            "target_danceability": 0.60,
            "target_valence": 0.70,
            "target_tempo_bpm": 102.0,
        },
        "tags": ["carefree", "warm"],
    },
    "dinner": {
        "keywords": ["dinner", "meal", "cooking"],
        "targets": {
            "target_energy": 0.40,
            "target_acousticness": 0.68,
            "target_tempo_bpm": 88.0,
            "target_vocal_presence": 0.48,
        },
        "tags": ["warm", "unhurried"],
    },
}

FREEFORM_FEATURE_CUES = {
    "acoustic": {"target_acousticness": 0.90, "target_instrumental_focus": 0.70},
    "acousticness": {"target_acousticness": 0.90},
    "instrumental": {"target_instrumental_focus": 0.94, "target_vocal_presence": 0.08},
    "lyricless": {"target_instrumental_focus": 0.94, "target_vocal_presence": 0.08},
    "vocals": {"target_vocal_presence": 0.70},
    "vocal": {"target_vocal_presence": 0.70},
    "singing": {"target_vocal_presence": 0.72},
    "soft vocals": {"target_vocal_presence": 0.42},
    "danceable": {"target_danceability": 0.82},
    "upbeat": {"target_energy": 0.82, "target_valence": 0.78},
    "slow": {"target_tempo_bpm": 72.0},
    "fast": {"target_tempo_bpm": 132.0},
}

NUMERIC_KEYS = [
    "target_energy",
    "target_valence",
    "target_danceability",
    "target_acousticness",
    "target_tempo_bpm",
    "target_vocal_presence",
    "target_instrumental_focus",
]

LIST_KEYS = [
    "favorite_genres",
    "favorite_moods",
    "favorite_contexts",
    "preferred_mood_tags",
]

DISPLAY_KEY_ORDER = [
    "genres",
    "moods",
    "contexts",
    "mood_tags",
    "energy",
    "danceability",
    "acousticness",
    "vocal_presence",
    "instrumental_focus",
    "valence",
    "tempo_bpm",
]

MUSIC_DOMAIN_TERMS = {
    "music",
    "song",
    "songs",
    "track",
    "tracks",
    "playlist",
    "playlists",
    "album",
    "albums",
    "artist",
    "artists",
    "band",
    "bands",
    "genre",
    "genres",
    "lyrics",
    "lyric",
    "listen",
    "listening",
    "vibe",
    "vibes",
    "bpm",
    "melody",
    "melodies",
    "instrumental",
    "instrumentals",
    "vocal",
    "vocals",
    "acoustic",
}

OUT_OF_SCOPE_CUES = [
    "recipe",
    "recipes",
    "pancake",
    "pancakes",
    "cook",
    "cooking",
    "bake",
    "baking",
    "ingredient",
    "ingredients",
    "weather",
    "forecast",
    "temperature",
    "news",
    "stock price",
    "stocks",
    "crypto",
    "code this",
    "debug this code",
    "solve this math",
    "math problem",
    "homework answer",
]

LYRIC_THEME_CUES = {
    "chill": ["quiet", "soft", "slow", "warm", "drift"],
    "focused": ["coding", "keys", "loop", "flow", "steady", "quiet"],
    "happy": ["sunlight", "bright", "smile", "golden"],
    "intense": ["pressure", "fire", "storm", "higher", "adrenaline"],
    "moody": ["night", "midnight", "blue", "dark", "rain"],
    "relaxed": ["gentle", "breathe", "slow", "warm"],
    "energetic": ["ignite", "fire", "higher", "run", "lightning"],
    "study": ["coding", "quiet", "keys", "loop", "room", "flow"],
    "deep_work": ["coding", "focus", "loop", "steady", "flow"],
    "sleep": ["dream", "moon", "slow", "drift", "gentle"],
    "reading": ["pages", "quiet", "lamplight", "rain"],
    "cafe": ["coffee", "corner", "warm", "window"],
    "night_drive": ["night", "midnight", "lights", "neon", "highway"],
    "workout": ["pressure", "storm", "higher", "limits", "fire"],
    "party": ["dance", "lights", "crowd", "celebration"],
    "commute": ["train", "morning", "city", "ride"],
    "walk": ["street", "steps", "wind", "stroll"],
    "dinner": ["kitchen", "candle", "slow", "warm"],
    "nocturnal": ["night", "midnight", "moon", "dark", "blue"],
    "gentle": ["quiet", "soft", "slow", "breathe"],
    "warm": ["warm", "golden", "glow", "ember"],
    "immersive": ["echo", "loop", "flow", "inside"],
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _phrase_in_text(text: str, phrase: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, normalized) is not None


def _append_unique(items: List[str], value: str) -> None:
    normalized = value.strip().lower()
    if normalized and normalized not in items:
        items.append(normalized)


def _merge_targets(targets: Dict[str, List[float]], additions: Dict[str, float]) -> None:
    for key, value in additions.items():
        targets.setdefault(key, []).append(float(value))


def _average_targets(targets: Dict[str, List[float]]) -> Dict[str, float]:
    averaged: Dict[str, float] = {}
    for key, values in targets.items():
        if not values:
            continue
        averaged[key] = round(sum(values) / len(values), 3)
    return averaged


def _closeness(song_value: float, target_value: float, tolerance: float) -> float:
    return max(0.0, 1.0 - abs(song_value - target_value) / tolerance)


def load_lyrics_index(lyrics_dir: str | Path) -> Dict[int, str]:
    lyrics_root = Path(lyrics_dir)
    lyrics_by_song_id: Dict[int, str] = {}
    if not lyrics_root.exists():
        return lyrics_by_song_id

    for path in lyrics_root.glob("*.txt"):
        try:
            song_id = int(path.stem)
        except ValueError:
            continue
        lyrics_by_song_id[song_id] = path.read_text(encoding="utf-8")

    return lyrics_by_song_id


def _safe_json_loads(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def gemini_explanations_enabled() -> bool:
    return _env_flag("GEMINI_EXPLANATIONS_ENABLED", default=False)


def gemini_reranking_enabled() -> bool:
    return _env_flag("GEMINI_RERANKING_ENABLED", default=False)


def gemini_rerank_top_n() -> int:
    return max(1, _env_int("GEMINI_RERANK_TOP_N", 8))


def wait_for_explanation_rate_limit(song_count: int) -> None:
    if song_count <= 0:
        return
    delay_per_song_seconds = max(
        0.0,
        _env_float("GEMINI_EXPLANATION_DELAY_PER_SONG_SECONDS", 1.5),
    )
    if delay_per_song_seconds <= 0:
        return
    time.sleep(delay_per_song_seconds * song_count)


_GEMINI_REQUEST_LOCK = threading.Lock()
_last_gemini_request_started_at = 0.0


def _wait_for_gemini_request_slot() -> None:
    global _last_gemini_request_started_at

    min_interval_seconds = max(
        0.0,
        _env_float("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", 1.5),
    )
    if min_interval_seconds <= 0:
        return

    with _GEMINI_REQUEST_LOCK:
        now = time.monotonic()
        sleep_for = max(0.0, min_interval_seconds - (now - _last_gemini_request_started_at))
        if sleep_for > 0:
            time.sleep(sleep_for)
            now = time.monotonic()
        _last_gemini_request_started_at = now


def _retry_after_seconds(exc: urllib.error.HTTPError) -> float | None:
    retry_after = exc.headers.get("Retry-After")
    if not retry_after:
        return None
    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=128)
def _cached_gemini_response(
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
) -> Dict[str, Any]:
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    max_retries = max(0, _env_int("GEMINI_HTTP_429_MAX_RETRIES", 2))
    attempt = 0
    while True:
        attempt += 1
        _wait_for_gemini_request_slot()
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt <= max_retries:
                retry_after_seconds = _retry_after_seconds(exc)
                backoff_seconds = retry_after_seconds if retry_after_seconds is not None else float(attempt * 2)
                time.sleep(backoff_seconds)
                continue
            raise RuntimeError(f"Gemini request failed: HTTP Error {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

    candidates = raw.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(str(part.get("text", "")) for part in parts)
    return _safe_json_loads(text)


def _post_to_gemini(prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return _cached_gemini_response(api_key, model, prompt, temperature)


def heuristic_parse_preferences(user_text: str) -> Dict[str, Any]:
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
    return parsed


def _has_recommender_signal(user_prefs: Dict[str, Any]) -> bool:
    list_keys = (
        "favorite_genres",
        "favorite_moods",
        "favorite_contexts",
        "preferred_mood_tags",
    )
    if any(user_prefs.get(key) for key in list_keys):
        return True
    return any(user_prefs.get(key) is not None for key in NUMERIC_KEYS)


def is_out_of_scope_music_request(user_text: str, parsed_prefs: Dict[str, Any]) -> bool:
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

Allowed genres: ambient, electronic, hip hop, indie pop, jazz, lofi, pop, rock, synthwave
Allowed moods: chill, energetic, focused, happy, intense, moody, relaxed
Allowed contexts: cafe, commute, deep_work, dinner, night_drive, party, reading, sleep, study, walk, workout
Numeric values should be normalized to 0-1 except tempo in BPM.
Use empty arrays or null when the request does not imply a value.

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

    return merged


def personalize_recommender_preferences(
    parsed_prefs: Dict[str, Any],
    taste_profile_prefs: Dict[str, Any],
    profile_numeric_weight: float = 0.07,
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

    return personalized


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

    return personalized


def build_song_document(song: Dict[str, Any]) -> str:
    parts = [
        f"title {song.get('title', '')}",
        f"artist {song.get('artist', '')}",
        f"genre {song.get('genre', '')}",
        f"mood {song.get('mood', '')}",
        f"context {song.get('listening_context', '')}",
        f"decade {song.get('release_decade', '')}",
        f"tags {song.get('detailed_mood_tags', '')}",
    ]
    return " ".join(parts).lower()


def build_lyrics_document(song_id: int, lyrics_by_song_id: Dict[int, str]) -> str:
    return lyrics_by_song_id.get(song_id, "").lower()


def _select_lyric_snippets(
    song_id: int,
    lyrics_by_song_id: Dict[int, str],
    query_tokens: set[str],
    lyric_query_terms: List[str],
    max_snippets: int = 3,
) -> List[str]:
    lyrics_text = lyrics_by_song_id.get(song_id, "").strip()
    if not lyrics_text:
        return []

    lines = [line.strip() for line in lyrics_text.splitlines() if line.strip()]
    if not lines:
        return []

    cue_tokens = set(_tokenize(" ".join(lyric_query_terms)))
    target_tokens = set(query_tokens) | cue_tokens
    scored_lines: List[Tuple[float, int, str]] = []

    for index, line in enumerate(lines):
        line_tokens = set(_tokenize(line))
        if not line_tokens:
            continue

        overlap = len(line_tokens & target_tokens)
        cue_overlap = len(line_tokens & cue_tokens)
        phrase_bonus = 0.0
        if any(_phrase_in_text(line, phrase) for phrase in lyric_query_terms if " " in phrase):
            phrase_bonus = 0.5

        score = float(overlap) + 0.35 * cue_overlap + phrase_bonus
        if score <= 0:
            continue

        scored_lines.append((score, index, line))

    if not scored_lines:
        return []

    top_lines = sorted(scored_lines, key=lambda item: (-item[0], item[1]))[:max_snippets]
    top_lines.sort(key=lambda item: item[1])
    return [line for _, _, line in top_lines]


def build_search_text(user_request: str, user_prefs: Dict[str, Any]) -> str:
    pieces = [user_request.strip()]
    pieces.extend(user_prefs.get("favorite_genres", []))
    pieces.extend(user_prefs.get("favorite_moods", []))
    pieces.extend(user_prefs.get("favorite_contexts", []))
    pieces.extend(user_prefs.get("preferred_mood_tags", []))
    return " ".join(piece for piece in pieces if piece).strip()


def _build_lyric_query_terms(user_prefs: Dict[str, Any]) -> List[str]:
    terms: List[str] = []
    for key in LIST_KEYS:
        for value in user_prefs.get(key, []):
            for cue in LYRIC_THEME_CUES.get(str(value).strip().lower(), []):
                if cue not in terms:
                    terms.append(cue)
    return terms


def _score_metadata_candidate(
    song: Dict[str, Any],
    query_tokens: set[str],
    favorite_genres: set[str],
    favorite_moods: set[str],
    favorite_contexts: set[str],
    mood_tags: set[str],
    user_prefs: Dict[str, Any],
) -> Tuple[float, List[str]]:
    document = build_song_document(song)
    doc_tokens = set(_tokenize(document))
    overlap_score = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)
    tag_tokens = {
        tag.strip().lower()
        for tag in str(song.get("detailed_mood_tags", "")).split(";")
        if tag.strip()
    }
    score = overlap_score
    reasons: List[str] = []

    if overlap_score > 0:
        reasons.append(f"text overlap {overlap_score:.2f}")

    if favorite_genres and str(song.get("genre", "")).lower() in favorite_genres:
        score += 1.2
        reasons.append("genre match")
    if favorite_moods and str(song.get("mood", "")).lower() in favorite_moods:
        score += 0.9
        reasons.append("mood match")
    if favorite_contexts and str(song.get("listening_context", "")).lower() in favorite_contexts:
        score += 0.7
        reasons.append("context match")
    if mood_tags:
        tag_overlap = len(tag_tokens & mood_tags) / max(len(mood_tags), 1)
        if tag_overlap > 0:
            score += 0.6 * tag_overlap
            reasons.append(f"tag overlap {tag_overlap:.2f}")

    numeric_preferences = [
        ("energy", "target_energy", 0.50, 0.25, "energy"),
        ("danceability", "target_danceability", 0.50, 0.20, "danceability"),
        ("acousticness", "target_acousticness", 0.50, 0.20, "acousticness"),
        ("tempo_bpm", "target_tempo_bpm", 40.0, 0.20, "tempo"),
        ("vocal_presence", "target_vocal_presence", 0.50, 0.15, "vocal presence"),
    ]
    for song_key, target_key, tolerance, weight, label in numeric_preferences:
        if target_key not in user_prefs:
            continue
        closeness = _closeness(
            float(song.get(song_key, 0.0)),
            float(user_prefs[target_key]),
            tolerance,
        )
        score += weight * closeness
        if closeness >= 0.7:
            reasons.append(f"{label} close")

    return round(score, 4), reasons


def _score_lyrics_candidate(
    song: Dict[str, Any],
    query_tokens: set[str],
    lyric_query_terms: List[str],
    lyrics_by_song_id: Dict[int, str],
) -> Tuple[float, List[str], List[str]]:
    song_id = int(song.get("id", -1))
    lyrics_document = build_lyrics_document(song_id, lyrics_by_song_id)
    if not lyrics_document:
        return 0.0, [], []

    lyric_tokens = set(_tokenize(lyrics_document))
    overlap_score = len(query_tokens & lyric_tokens) / max(len(query_tokens), 1)
    cue_overlap_tokens = lyric_tokens & set(lyric_query_terms)
    cue_overlap = len(cue_overlap_tokens) / max(len(set(lyric_query_terms)), 1) if lyric_query_terms else 0.0
    score = 1.4 * overlap_score + 0.9 * cue_overlap
    reasons: List[str] = []

    if overlap_score > 0:
        reasons.append(f"lyric text overlap {overlap_score:.2f}")
    if cue_overlap > 0:
        reasons.append(f"lyric theme overlap {cue_overlap:.2f}")

    snippets = []
    if score > 0:
        snippets = _select_lyric_snippets(
            song_id=song_id,
            lyrics_by_song_id=lyrics_by_song_id,
            query_tokens=query_tokens,
            lyric_query_terms=lyric_query_terms,
        )

    return round(score, 4), reasons, snippets


def retrieve_metadata_candidates(
    user_request: str,
    user_prefs: Dict[str, Any],
    songs: List[Dict[str, Any]],
    limit: int = 20,
) -> List[Dict[str, Any]]:
    query_text = build_search_text(user_request, user_prefs)
    query_tokens = set(_tokenize(query_text))
    favorite_genres = set(user_prefs.get("favorite_genres", []))
    favorite_moods = set(user_prefs.get("favorite_moods", []))
    favorite_contexts = set(user_prefs.get("favorite_contexts", []))
    mood_tags = set(user_prefs.get("preferred_mood_tags", []))

    retrieved: List[Dict[str, Any]] = []
    for song in songs:
        metadata_score, metadata_reasons = _score_metadata_candidate(
            song=song,
            query_tokens=query_tokens,
            favorite_genres=favorite_genres,
            favorite_moods=favorite_moods,
            favorite_contexts=favorite_contexts,
            mood_tags=mood_tags,
            user_prefs=user_prefs,
        )
        retrieved.append(
            {
                "song": song,
                "retrieval_score": metadata_score,
                "retrieval_breakdown": {
                    "metadata": metadata_score,
                    "lyrics": 0.0,
                },
                "matched_sources": ["metadata"] if metadata_score > 0 else [],
                "source_reasons": {
                    "metadata": metadata_reasons,
                    "lyrics": [],
                },
                "lyric_snippets": [],
            }
        )

    retrieved.sort(key=lambda item: item["retrieval_score"], reverse=True)
    return retrieved[: min(limit, len(retrieved))]


def retrieve_lyric_candidates(
    user_request: str,
    user_prefs: Dict[str, Any],
    songs: List[Dict[str, Any]],
    lyrics_by_song_id: Dict[int, str],
    limit: int = 20,
) -> List[Dict[str, Any]]:
    query_text = build_search_text(user_request, user_prefs)
    query_tokens = set(_tokenize(query_text))
    lyric_query_terms = _build_lyric_query_terms(user_prefs)

    retrieved: List[Dict[str, Any]] = []
    for song in songs:
        lyrics_score, lyrics_reasons, lyric_snippets = _score_lyrics_candidate(
            song=song,
            query_tokens=query_tokens,
            lyric_query_terms=lyric_query_terms,
            lyrics_by_song_id=lyrics_by_song_id,
        )
        retrieved.append(
            {
                "song": song,
                "retrieval_score": lyrics_score,
                "retrieval_breakdown": {
                    "metadata": 0.0,
                    "lyrics": lyrics_score,
                },
                "matched_sources": ["lyrics"] if lyrics_score > 0 else [],
                "source_reasons": {
                    "metadata": [],
                    "lyrics": lyrics_reasons,
                },
                "lyric_snippets": lyric_snippets,
            }
        )

    retrieved.sort(key=lambda item: item["retrieval_score"], reverse=True)
    return retrieved[: min(limit, len(retrieved))]


def retrieve_candidate_songs(
    user_request: str,
    user_prefs: Dict[str, Any],
    songs: List[Dict[str, Any]],
    lyrics_by_song_id: Dict[int, str] | None = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    lyrics_by_song_id = lyrics_by_song_id or {}
    metadata_candidates = retrieve_metadata_candidates(
        user_request=user_request,
        user_prefs=user_prefs,
        songs=songs,
        limit=len(songs),
    )
    lyric_candidates = retrieve_lyric_candidates(
        user_request=user_request,
        user_prefs=user_prefs,
        songs=songs,
        lyrics_by_song_id=lyrics_by_song_id,
        limit=len(songs),
    )

    merged_by_id: Dict[int, Dict[str, Any]] = {}
    for candidates in (metadata_candidates, lyric_candidates):
        for candidate in candidates:
            song = candidate["song"]
            song_id = int(song.get("id", -1))
            merged = merged_by_id.setdefault(
                song_id,
                {
                    "song": song,
                    "retrieval_score": 0.0,
                    "retrieval_breakdown": {"metadata": 0.0, "lyrics": 0.0},
                    "matched_sources": [],
                    "source_reasons": {"metadata": [], "lyrics": []},
                    "lyric_snippets": [],
                },
            )

            for source_name in ("metadata", "lyrics"):
                source_score = float(candidate["retrieval_breakdown"].get(source_name, 0.0))
                if source_score > merged["retrieval_breakdown"][source_name]:
                    merged["retrieval_breakdown"][source_name] = round(source_score, 4)
                    merged["source_reasons"][source_name] = candidate["source_reasons"].get(source_name, [])
                    if source_name == "lyrics":
                        merged["lyric_snippets"] = candidate.get("lyric_snippets", [])

                if source_score > 0 and source_name not in merged["matched_sources"]:
                    merged["matched_sources"].append(source_name)

    merged_candidates = list(merged_by_id.values())
    for candidate in merged_candidates:
        metadata_score = candidate["retrieval_breakdown"]["metadata"]
        lyrics_score = candidate["retrieval_breakdown"]["lyrics"]
        candidate["retrieval_score"] = round(metadata_score + lyrics_score, 4)

    merged_candidates.sort(key=lambda item: item["retrieval_score"], reverse=True)
    return merged_candidates[: min(limit, len(merged_candidates))]


def summarize_preferences(user_prefs: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "genres": user_prefs.get("favorite_genres", []),
        "moods": user_prefs.get("favorite_moods", []),
        "contexts": user_prefs.get("favorite_contexts", []),
        "mood_tags": user_prefs.get("preferred_mood_tags", []),
        "energy": user_prefs.get("target_energy"),
        "danceability": user_prefs.get("target_danceability"),
        "acousticness": user_prefs.get("target_acousticness"),
        "vocal_presence": user_prefs.get("target_vocal_presence"),
        "instrumental_focus": user_prefs.get("target_instrumental_focus"),
        "valence": user_prefs.get("target_valence"),
        "tempo_bpm": user_prefs.get("target_tempo_bpm"),
    }
    return {key: summary[key] for key in DISPLAY_KEY_ORDER if summary.get(key) not in (None, [], "")}


def _is_close(song: Dict[str, Any], prefs: Dict[str, Any], song_key: str, target_key: str, tolerance: float) -> bool:
    if target_key not in prefs:
        return False
    return _closeness(float(song.get(song_key, 0.0)), float(prefs[target_key]), tolerance) >= 0.72


def _fallback_song_explanation(song: Dict[str, Any], prefs: Dict[str, Any]) -> str:
    reasons: List[str] = []

    if str(song.get("genre", "")).lower() in set(prefs.get("favorite_genres", [])):
        reasons.append(f"its {song.get('genre', 'unknown')} genre matches the request")
    if str(song.get("mood", "")).lower() in set(prefs.get("favorite_moods", [])):
        reasons.append(f"the {song.get('mood', 'unknown')} mood lines up well")
    if str(song.get("listening_context", "")).lower() in set(prefs.get("favorite_contexts", [])):
        reasons.append(f"it fits a {song.get('listening_context', 'general')} listening context")
    if _is_close(song, prefs, "energy", "target_energy", 0.50):
        reasons.append("its energy sits close to the target")
    if _is_close(song, prefs, "acousticness", "target_acousticness", 0.50):
        reasons.append("it keeps acousticness in the requested range")
    if _is_close(song, prefs, "vocal_presence", "target_vocal_presence", 0.50):
        reasons.append("its vocal presence is close to what you asked for")
    if _is_close(song, prefs, "tempo_bpm", "target_tempo_bpm", 40.0):
        reasons.append("its tempo stays near the target pace")

    if not reasons:
        reasons.append("it overlaps with the requested vibe across several song features")

    return f"This track works because {', '.join(reasons[:3])}."


def _fallback_overall_explanation(user_request: str, prefs: Dict[str, Any]) -> str:
    summary = summarize_preferences(prefs)
    clauses: List[str] = []
    if summary.get("moods"):
        clauses.append(f"they stay in a {', '.join(summary['moods'])} lane")
    if summary.get("contexts"):
        clauses.append(f"they fit {', '.join(summary['contexts'])} listening")
    if summary.get("acousticness") is not None:
        clauses.append("they keep the acoustic character close to target")
    if summary.get("energy") is not None:
        clauses.append("their energy level stays aligned with the request")
    if not clauses:
        clauses.append("they matched the strongest overlaps in the request and song metadata")
    return f"These recommendations were selected because {', '.join(clauses[:3])}."


def _extract_llm_song_explanations(
    response: Dict[str, Any],
    ranked_songs: List[Tuple[Dict[str, Any], float, str]],
) -> Dict[int, str]:
    raw_items = response.get("song_explanations", [])
    if not isinstance(raw_items, list):
        return {}

    ranked_song_ids = [
        int(song.get("id", 0))
        for song, _, _ in ranked_songs
        if int(song.get("id", 0)) > 0
    ]
    explanations: Dict[int, str] = {}

    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue

        explanation = str(
            item.get("explanation")
            or item.get("reason")
            or item.get("text")
            or ""
        ).strip()
        if not explanation:
            continue

        raw_id = item.get("id", item.get("song_id"))
        song_id: int | None = None
        if raw_id is not None:
            try:
                song_id = int(raw_id)
            except (TypeError, ValueError):
                song_id = None

        if song_id is None and index < len(ranked_song_ids):
            song_id = ranked_song_ids[index]

        if song_id is not None and song_id > 0:
            explanations[song_id] = explanation

    return explanations


def explain_ranked_songs(
    user_request: str,
    user_prefs: Dict[str, Any],
    ranked_songs: List[Tuple[Dict[str, Any], float, str]],
    retrieval_context_by_song_id: Dict[int, Dict[str, Any]] | None = None,
) -> Tuple[str, Dict[int, str], str]:
    if not ranked_songs:
        return "No matching songs were found.", {}, "heuristic"

    retrieval_context_by_song_id = retrieval_context_by_song_id or {}
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and gemini_explanations_enabled():
        prompt = {
            "user_request": user_request,
            "detected_preferences": summarize_preferences(user_prefs),
            "recommended_songs": [
                {
                    "id": song.get("id"),
                    "title": song.get("title"),
                    "artist": song.get("artist"),
                    "genre": song.get("genre"),
                    "mood": song.get("mood"),
                    "listening_context": song.get("listening_context"),
                    "energy": song.get("energy"),
                    "danceability": song.get("danceability"),
                    "acousticness": song.get("acousticness"),
                    "tempo_bpm": song.get("tempo_bpm"),
                    "vocal_presence": song.get("vocal_presence"),
                    "detailed_mood_tags": song.get("detailed_mood_tags"),
                    "lyric_snippets": retrieval_context_by_song_id.get(
                        int(song.get("id", 0)),
                        {},
                    ).get("lyric_snippets", []),
                    "math_score": round(score, 4),
                }
                for song, score, _ in ranked_songs
            ],
        }
        llm_prompt = f"""
You explain music recommendations using only the provided JSON data.
Return strict JSON with:
- overall_explanation: string
- song_explanations: array of objects with id:number and explanation:string

Keep each explanation to one short sentence. When lyric_snippets are present, use them as retrieved grounding context. Do not invent attributes.

{json.dumps(prompt, indent=2)}
        """.strip()
        try:
            wait_for_explanation_rate_limit(len(ranked_songs))
            response = _post_to_gemini(llm_prompt, temperature=0.2)
            explanations = _extract_llm_song_explanations(response, ranked_songs)
            if explanations:
                fallback_explanations = {
                    int(song.get("id", 0)): _fallback_song_explanation(song, user_prefs)
                    for song, _, _ in ranked_songs
                }
                fallback_explanations.update(explanations)
                return (
                    str(response.get("overall_explanation", "")).strip()
                    or _fallback_overall_explanation(user_request, user_prefs),
                    fallback_explanations,
                    "gemini",
                )
        except Exception as exc:
            print(f"Gemini explanation fallback triggered: {exc}")
            pass

    fallback_explanations = {
        int(song.get("id", 0)): _fallback_song_explanation(song, user_prefs)
        for song, _, _ in ranked_songs
    }
    return (
        _fallback_overall_explanation(user_request, user_prefs),
        fallback_explanations,
        "heuristic",
    )


def _extract_llm_reranked_song_ids(
    response: Dict[str, Any],
    ranked_songs: List[Tuple[Dict[str, Any], float, str]],
) -> List[int]:
    raw_items = response.get("ranking", [])
    if not isinstance(raw_items, list):
        return []

    available_song_ids = {
        int(song.get("id", 0))
        for song, _, _ in ranked_songs
        if int(song.get("id", 0)) > 0
    }
    ordered_song_ids: List[int] = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id", item.get("song_id"))
        try:
            song_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if song_id not in available_song_ids or song_id in ordered_song_ids:
            continue
        ordered_song_ids.append(song_id)

    return ordered_song_ids


def rerank_recommendations_with_gemini(
    user_request: str,
    user_prefs: Dict[str, Any],
    ranked_songs: List[Tuple[Dict[str, Any], float, str]],
    retrieval_context_by_song_id: Dict[int, Dict[str, Any]] | None = None,
) -> Tuple[List[Tuple[Dict[str, Any], float, str]], str]:
    if len(ranked_songs) <= 1:
        return ranked_songs, "deterministic"

    retrieval_context_by_song_id = retrieval_context_by_song_id or {}
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not gemini_reranking_enabled():
        return ranked_songs, "deterministic"

    top_n = min(gemini_rerank_top_n(), len(ranked_songs))
    rerank_slice = ranked_songs[:top_n]
    remaining = ranked_songs[top_n:]
    llm_prompt_payload = {
        "user_request": user_request,
        "detected_preferences": summarize_preferences(user_prefs),
        "candidate_songs": [
            {
                "id": song.get("id"),
                "title": song.get("title"),
                "artist": song.get("artist"),
                "genre": song.get("genre"),
                "mood": song.get("mood"),
                "listening_context": song.get("listening_context"),
                "release_decade": song.get("release_decade"),
                "detailed_mood_tags": song.get("detailed_mood_tags"),
                "energy": song.get("energy"),
                "danceability": song.get("danceability"),
                "acousticness": song.get("acousticness"),
                "tempo_bpm": song.get("tempo_bpm"),
                "vocal_presence": song.get("vocal_presence"),
                "instrumental_focus": song.get("instrumental_focus"),
                "lyric_snippets": retrieval_context_by_song_id.get(
                    int(song.get("id", 0)),
                    {},
                ).get("lyric_snippets", []),
                "math_score": round(score, 4),
                "math_explanation": explanation,
            }
            for song, score, explanation in rerank_slice
        ],
    }
    llm_prompt = f"""
You rerank music recommendation candidates using only the provided JSON data.
Return strict JSON with one key:
- ranking: array of objects with id:number and rank:number

Rank the candidates from best to worst for the user's request.
Use every candidate exactly once.
Use lyric_snippets when present as retrieved grounding context. Do not invent attributes or songs.

{json.dumps(llm_prompt_payload, indent=2)}
    """.strip()

    try:
        response = _post_to_gemini(llm_prompt, temperature=0.1)
        reranked_ids = _extract_llm_reranked_song_ids(response, rerank_slice)
        if len(reranked_ids) != len(rerank_slice):
            return ranked_songs, "deterministic"

        reranked_by_id = {
            int(song.get("id", 0)): (song, score, explanation)
            for song, score, explanation in rerank_slice
        }
        reranked_slice = [reranked_by_id[song_id] for song_id in reranked_ids]
        return reranked_slice + remaining, "gemini"
    except Exception:
        return ranked_songs, "deterministic"
