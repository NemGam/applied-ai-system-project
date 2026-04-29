import json
import os
from typing import Any, Dict, List, Tuple

from .common import _closeness
from .gemini import (
    _post_to_gemini,
    gemini_explanations_enabled,
    gemini_rerank_top_n,
    gemini_reranking_enabled,
    wait_for_explanation_rate_limit,
)
from .retrieval import summarize_preferences


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
