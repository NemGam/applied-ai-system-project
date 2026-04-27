from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.src.ai_pipeline import (
    explain_ranked_songs,
    is_out_of_scope_music_request,
    rerank_recommendations_with_gemini,
    manual_preferences_to_recommender,
    merge_recommender_preferences,
    personalize_recommender_preferences,
    parse_preferences_with_gemini,
    retrieve_candidate_songs,
    summarize_preferences,
)
from backend.src.recommender import recommend_songs


router = APIRouter()
MEDIA_ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = MEDIA_ROOT / "audio"
COVERS_DIR = MEDIA_ROOT / "covers"
LYRICS_DIR = MEDIA_ROOT / "lyrics"


class RecommendationRequest(BaseModel):
    favorite_genres: List[str] = Field(default_factory=list)
    favorite_moods: List[str] = Field(default_factory=list)
    favorite_contexts: List[str] = Field(default_factory=list)
    preferred_mood_tags: List[str] = Field(default_factory=list)
    favorite_decades: List[str] = Field(default_factory=list)
    target_energy: float | None = None
    target_valence: float | None = None
    target_danceability: float | None = None
    target_acousticness: float | None = None
    target_tempo_bpm: float | None = None
    target_popularity_100: float | None = None
    target_vocal_presence: float | None = None
    target_instrumental_focus: float | None = None
    target_replay_value: float | None = None
    k: int = Field(default=5, ge=1, le=20)


class ManualPreferencesInput(BaseModel):
    genre: str | None = None
    mood: str | None = None
    energy: float | None = Field(default=None, ge=0, le=1)
    tempo_bpm: float | None = Field(default=None, ge=0)
    danceability: float | None = Field(default=None, ge=0, le=1)
    acousticness: float | None = Field(default=None, ge=0, le=1)
    vocal_presence: float | None = Field(default=None, ge=0, le=1)
    instrumental_focus: float | None = Field(default=None, ge=0, le=1)
    valence: float | None = Field(default=None, ge=0, le=1)
    listening_context: str | None = None
    preferred_mood_tags: List[str] = Field(default_factory=list)


class AIRecommendationRequest(BaseModel):
    user_text: str | None = None
    manual_preferences: ManualPreferencesInput | None = None
    taste_profile: ManualPreferencesInput | None = None
    k: int = Field(default=5, ge=1, le=20)
    retrieval_k: int = Field(default=20, ge=1, le=50)


def _songs(request: Request) -> List[Dict[str, Any]]:
    songs = getattr(request.app.state, "songs", None)
    if songs is None:
        raise HTTPException(status_code=500, detail="Song catalog is not loaded")
    return songs


def _lyrics_by_song_id(request: Request) -> Dict[int, str]:
    lyrics = getattr(request.app.state, "lyrics_by_song_id", None)
    if lyrics is None:
        return {}
    return lyrics


def _payload_to_dict(payload: RecommendationRequest) -> Dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_none=True)
    return payload.dict(exclude_none=True)


def _resolve_media_url(
    request: Request,
    media_dir: Path,
    mount_path: str,
    song_id: Any,
    extensions: List[str],
) -> str | None:
    for extension in extensions:
        filename = f"{song_id}.{extension}"
        if (media_dir / filename).exists():
            return f"{str(request.base_url).rstrip('/')}{mount_path}/{filename}"
    return None


def _lyrics_path(song_id: Any) -> Path:
    return LYRICS_DIR / f"{song_id}.txt"


def _lyrics_url(request: Request, song_id: Any) -> str:
    return f"{str(request.base_url).rstrip('/')}/songs/{song_id}/lyrics"


def _find_song(request: Request, song_id: int) -> Dict[str, Any]:
    for song in _songs(request):
        if int(song.get("id", -1)) == song_id:
            return song
    raise HTTPException(status_code=404, detail="Song not found")


def _song_with_assets(request: Request, song: Dict[str, Any]) -> Dict[str, Any]:
    song_copy = dict(song)
    song_id = song_copy.get("id")
    lyrics_path = _lyrics_path(song_id)

    song_copy["cover_url"] = _resolve_media_url(
        request,
        COVERS_DIR,
        "/covers",
        song_id,
        ["png", "jpg", "jpeg", "webp"],
    )
    song_copy["audio_url"] = _resolve_media_url(
        request,
        AUDIO_DIR,
        "/audio",
        song_id,
        ["mp3", "wav", "ogg"],
    )
    song_copy["has_lyrics"] = lyrics_path.exists()
    song_copy["lyrics_url"] = _lyrics_url(request, song_id) if lyrics_path.exists() else None
    return song_copy


def _manual_request_summary(manual_preferences: Dict[str, Any]) -> str:
    parts: List[str] = []
    if manual_preferences.get("mood"):
        parts.append(f"mood {manual_preferences['mood']}")
    if manual_preferences.get("genre"):
        parts.append(f"genre {manual_preferences['genre']}")
    if manual_preferences.get("listening_context"):
        parts.append(f"context {manual_preferences['listening_context']}")
    if manual_preferences.get("energy") is not None:
        parts.append(f"energy {manual_preferences['energy']}")
    if manual_preferences.get("acousticness") is not None:
        parts.append(f"acousticness {manual_preferences['acousticness']}")
    if manual_preferences.get("vocal_presence") is not None:
        parts.append(f"vocal presence {manual_preferences['vocal_presence']}")
    return ", ".join(parts) or "manual preference request"


def _hybrid_request_summary(manual_summary: str, user_text: str) -> str:
    notes = user_text.strip()
    if not notes:
        return manual_summary
    return f"{manual_summary}. Extra notes: {notes}"


def _out_of_scope_ai_response(
    user_request: str,
    input_mode: str,
    parser_provider: str,
    personalization_summary: Dict[str, Any] | None = None,
    personalization_enabled: bool = False,
    personalization_source: str | None = None,
) -> Dict[str, Any]:
    return {
        "input_mode": input_mode,
        "user_request": user_request,
        "detected_preferences": {},
        "personalization": {
            "enabled": personalization_enabled,
            "source": personalization_source,
            "taste_profile": personalization_summary or {},
        },
        "providers": {
            "parser": parser_provider,
            "ranking": "not_run",
            "explanations": "not_run",
        },
        "guardrail": {
            "triggered": True,
            "category": "out_of_scope",
            "message": "This assistant only handles music recommendation requests. Try asking for songs, artists, moods, genres, lyrics, or listening contexts.",
        },
        "retrieval": {
            "strategy": "metadata+lyrics",
            "candidate_count": 0,
            "source_counts": {
                "metadata": 0,
                "lyrics": 0,
                "both": 0,
            },
            "candidates": [],
        },
        "overall_explanation": "No recommendations were generated because the request appears to be outside the music domain.",
        "results": [],
    }


@router.get("/")
def root() -> Dict[str, str]:
    return {
        "message": "Music Recommender API is running",
        "docs": "/docs",
    }


@router.get("/health")
def health(request: Request) -> Dict[str, Any]:
    songs = _songs(request)
    return {
        "status": "ok",
        "songs_loaded": len(songs),
    }


@router.get("/songs")
def list_songs(request: Request) -> Dict[str, Any]:
    songs = _songs(request)
    return {
        "count": len(songs),
        "songs": [_song_with_assets(request, song) for song in songs],
    }


@router.get("/songs/{song_id}/lyrics")
def get_song_lyrics(song_id: int, request: Request) -> Dict[str, Any]:
    song = _find_song(request, song_id)
    lyrics_path = _lyrics_path(song_id)
    if not lyrics_path.exists():
        raise HTTPException(status_code=404, detail="Lyrics not found")

    return {
        "song_id": song_id,
        "title": song.get("title", "Unknown Title"),
        "artist": song.get("artist", "Unknown Artist"),
        "lyrics": lyrics_path.read_text(encoding="utf-8"),
    }


@router.post("/recommendations")
def create_recommendations(payload: RecommendationRequest, request: Request) -> Dict[str, Any]:
    songs = _songs(request)
    user_prefs = _payload_to_dict(payload)
    k = user_prefs.pop("k")
    ranked = recommend_songs(user_prefs=user_prefs, songs=songs, k=k)

    return {
        "count": len(ranked),
        "results": [
            {
                "song": _song_with_assets(request, song),
                "score": score,
                "explanation": explanation,
            }
            for song, score, explanation in ranked
        ],
    }


@router.post("/recommendations/ai")
def create_ai_recommendations(payload: AIRecommendationRequest, request: Request) -> Dict[str, Any]:
    songs = _songs(request)
    lyrics_by_song_id = _lyrics_by_song_id(request)
    personalization_summary: Dict[str, Any] = {}
    personalization_enabled = False
    personalization_source: str | None = None

    user_text = (payload.user_text or "").strip()
    has_text = bool(user_text)
    has_manual = payload.manual_preferences is not None
    has_taste_profile = payload.taste_profile is not None
    if not has_text and not has_manual:
        raise HTTPException(
            status_code=400,
            detail="Provide user_text, manual_preferences, or both",
        )

    if has_text and not has_manual:
        parsed_prefs, parser_provider = parse_preferences_with_gemini(user_text)
        if is_out_of_scope_music_request(user_text, parsed_prefs):
            return _out_of_scope_ai_response(
                user_request=user_text,
                input_mode="natural_language",
                parser_provider=parser_provider,
            )
        recommender_prefs = parsed_prefs
        if has_taste_profile:
            taste_profile_dict = _payload_to_dict(payload.taste_profile)
            taste_profile_prefs = manual_preferences_to_recommender(taste_profile_dict)
            recommender_prefs = personalize_recommender_preferences(
                parsed_prefs=parsed_prefs,
                taste_profile_prefs=taste_profile_prefs,
            )
            personalization_summary = summarize_preferences(taste_profile_prefs)
            personalization_enabled = bool(personalization_summary)
            personalization_source = "taste_profile" if personalization_enabled else None
            if personalization_enabled:
                parser_provider = f"{parser_provider}+taste_profile"
        request_summary = user_text
        input_mode = "natural_language"
    elif has_manual and not has_text:
        manual_dict = _payload_to_dict(payload.manual_preferences)
        recommender_prefs = manual_preferences_to_recommender(manual_dict)
        parser_provider = "manual"
        request_summary = _manual_request_summary(manual_dict)
        input_mode = "manual"
    else:
        manual_dict = _payload_to_dict(payload.manual_preferences)
        manual_prefs = manual_preferences_to_recommender(manual_dict)
        parsed_prefs, parsed_provider = parse_preferences_with_gemini(user_text)
        if not any(manual_prefs.get(key) for key in ("favorite_genres", "favorite_moods", "favorite_contexts", "preferred_mood_tags")) and not any(
            manual_prefs.get(key) is not None
            for key in (
                "target_energy",
                "target_valence",
                "target_danceability",
                "target_acousticness",
                "target_tempo_bpm",
                "target_vocal_presence",
                "target_instrumental_focus",
            )
        ) and is_out_of_scope_music_request(user_text, parsed_prefs):
            return _out_of_scope_ai_response(
                user_request=_hybrid_request_summary(_manual_request_summary(manual_dict), user_text),
                input_mode="hybrid",
                parser_provider=f"manual+{parsed_provider}",
            )
        recommender_prefs = merge_recommender_preferences(
            manual_prefs=manual_prefs,
            parsed_prefs=parsed_prefs,
        )
        parser_provider = f"manual+{parsed_provider}"
        request_summary = _hybrid_request_summary(_manual_request_summary(manual_dict), user_text)
        input_mode = "hybrid"

    retrieved_candidates = retrieve_candidate_songs(
        user_request=request_summary,
        user_prefs=recommender_prefs,
        songs=songs,
        lyrics_by_song_id=lyrics_by_song_id,
        limit=payload.retrieval_k,
    )
    candidate_songs = [candidate["song"] for candidate in retrieved_candidates]
    ranked = recommend_songs(user_prefs=recommender_prefs, songs=candidate_songs, k=payload.k)
    ranked, ranking_provider = rerank_recommendations_with_gemini(
        user_request=request_summary,
        user_prefs=recommender_prefs,
        ranked_songs=ranked,
    )
    overall_explanation, llm_explanations, explanation_provider = explain_ranked_songs(
        user_request=request_summary,
        user_prefs=recommender_prefs,
        ranked_songs=ranked,
    )

    retrieval_scores_by_id = {
        int(candidate["song"].get("id", -1)): candidate["retrieval_score"]
        for candidate in retrieved_candidates
    }
    retrieval_details_by_id = {
        int(candidate["song"].get("id", -1)): candidate
        for candidate in retrieved_candidates
    }
    metadata_matches = sum(1 for candidate in retrieved_candidates if "metadata" in candidate["matched_sources"])
    lyric_matches = sum(1 for candidate in retrieved_candidates if "lyrics" in candidate["matched_sources"])
    both_matches = sum(1 for candidate in retrieved_candidates if len(candidate["matched_sources"]) > 1)

    return {
        "input_mode": input_mode,
        "user_request": request_summary,
        "detected_preferences": summarize_preferences(recommender_prefs),
        "personalization": {
            "enabled": personalization_enabled,
            "source": personalization_source,
            "taste_profile": personalization_summary,
        },
        "providers": {
            "parser": parser_provider,
            "ranking": ranking_provider,
            "explanations": explanation_provider,
        },
        "retrieval": {
            "strategy": "metadata+lyrics",
            "candidate_count": len(retrieved_candidates),
            "source_counts": {
                "metadata": metadata_matches,
                "lyrics": lyric_matches,
                "both": both_matches,
            },
            "candidates": [
                {
                    "song_id": candidate["song"].get("id"),
                    "title": candidate["song"].get("title"),
                    "artist": candidate["song"].get("artist"),
                    "genre": candidate["song"].get("genre"),
                    "mood": candidate["song"].get("mood"),
                    "listening_context": candidate["song"].get("listening_context"),
                    "retrieval_score": candidate["retrieval_score"],
                    "retrieval_breakdown": candidate["retrieval_breakdown"],
                    "matched_sources": candidate["matched_sources"],
                    "source_reasons": candidate["source_reasons"],
                }
                for candidate in retrieved_candidates
            ],
        },
        "overall_explanation": overall_explanation,
        "results": [
            {
                "song": _song_with_assets(request, song),
                "score": score,
                "retrieval_score": retrieval_scores_by_id.get(int(song.get("id", -1)), 0.0),
                "retrieval_breakdown": retrieval_details_by_id.get(int(song.get("id", -1)), {}).get(
                    "retrieval_breakdown",
                    {"metadata": 0.0, "lyrics": 0.0},
                ),
                "matched_sources": retrieval_details_by_id.get(int(song.get("id", -1)), {}).get(
                    "matched_sources",
                    [],
                ),
                "source_reasons": retrieval_details_by_id.get(int(song.get("id", -1)), {}).get(
                    "source_reasons",
                    {"metadata": [], "lyrics": []},
                ),
                "math_explanation": explanation,
                "llm_explanation": llm_explanations.get(
                    int(song.get("id", -1)),
                    explanation,
                ),
            }
            for song, score, explanation in ranked
        ],
    }
