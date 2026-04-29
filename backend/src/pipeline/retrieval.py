from typing import Any, Dict, List, Tuple

from .common import _closeness, _phrase_in_text, _tokenize
from .constants import DISPLAY_KEY_ORDER, LIST_KEYS, LYRIC_THEME_CUES


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


def _matches_hard_filters(
    song: Dict[str, Any],
    user_prefs: Dict[str, Any],
    lyrics_by_song_id: Dict[int, str] | None = None,
) -> bool:
    if user_prefs.get("exclude_lyrical_tracks"):
        song_id = int(song.get("id", -1))
        if lyrics_by_song_id and song_id in lyrics_by_song_id:
            return False
    return True


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
    lyrics_by_song_id: Dict[int, str] | None = None,
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
        if not _matches_hard_filters(song, user_prefs, lyrics_by_song_id):
            continue
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
        if not _matches_hard_filters(song, user_prefs, lyrics_by_song_id):
            continue
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
        lyrics_by_song_id=lyrics_by_song_id,
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
