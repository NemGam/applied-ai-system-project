import time
import urllib
from typing import Any, Dict, List, Tuple

from backend.src.pipeline import constants as _constants
from backend.src.pipeline import explanations as _explanations
from backend.src.pipeline import gemini as _gemini
from backend.src.pipeline import preferences as _preferences
from backend.src.pipeline import retrieval as _retrieval
from backend.src.pipeline.common import (
    _append_unique,
    _average_targets,
    _closeness,
    _merge_targets,
    _phrase_in_text,
    _tokenize,
    load_lyrics_index,
)

GENRE_ALIASES = _constants.GENRE_ALIASES
MOOD_CUES = _constants.MOOD_CUES
CONTEXT_CUES = _constants.CONTEXT_CUES
FREEFORM_FEATURE_CUES = _constants.FREEFORM_FEATURE_CUES
NUMERIC_KEYS = _constants.NUMERIC_KEYS
LIST_KEYS = _constants.LIST_KEYS
DISPLAY_KEY_ORDER = _constants.DISPLAY_KEY_ORDER
AGENT_CLARIFICATION_CHOICES = _constants.AGENT_CLARIFICATION_CHOICES
MUSIC_DOMAIN_TERMS = _constants.MUSIC_DOMAIN_TERMS
OUT_OF_SCOPE_CUES = _constants.OUT_OF_SCOPE_CUES
LYRIC_THEME_CUES = _constants.LYRIC_THEME_CUES

_post_to_gemini = _gemini._post_to_gemini
gemini_explanations_enabled = _gemini.gemini_explanations_enabled
gemini_reranking_enabled = _gemini.gemini_reranking_enabled
gemini_rerank_top_n = _gemini.gemini_rerank_top_n
_last_gemini_request_started_at = _gemini._last_gemini_request_started_at

normalize_recommender_preferences = _preferences.normalize_recommender_preferences
manual_preferences_to_recommender = _preferences.manual_preferences_to_recommender
merge_recommender_preferences = _preferences.merge_recommender_preferences
merge_clarification_preferences = _preferences.merge_clarification_preferences
evaluate_agent_confidence = _preferences.evaluate_agent_confidence
choose_agent_clarification_question = _preferences.choose_agent_clarification_question
personalize_recommender_preferences = _preferences.personalize_recommender_preferences
heuristic_parse_preferences = _preferences.heuristic_parse_preferences
is_out_of_scope_music_request = _preferences.is_out_of_scope_music_request
_has_recommender_signal = _preferences._has_recommender_signal

build_song_document = _retrieval.build_song_document
build_lyrics_document = _retrieval.build_lyrics_document
build_search_text = _retrieval.build_search_text
retrieve_metadata_candidates = _retrieval.retrieve_metadata_candidates
retrieve_lyric_candidates = _retrieval.retrieve_lyric_candidates
retrieve_candidate_songs = _retrieval.retrieve_candidate_songs
summarize_preferences = _retrieval.summarize_preferences
_build_lyric_query_terms = _retrieval._build_lyric_query_terms
_score_metadata_candidate = _retrieval._score_metadata_candidate
_score_lyrics_candidate = _retrieval._score_lyrics_candidate
_select_lyric_snippets = _retrieval._select_lyric_snippets

_extract_llm_song_explanations = _explanations._extract_llm_song_explanations
_extract_llm_reranked_song_ids = _explanations._extract_llm_reranked_song_ids


def _cached_gemini_response(
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
) -> Dict[str, Any]:
    global _last_gemini_request_started_at

    original_timestamp = _gemini._last_gemini_request_started_at
    _gemini._last_gemini_request_started_at = _last_gemini_request_started_at
    try:
        response = _gemini._cached_gemini_response(api_key, model, prompt, temperature)
        return response
    finally:
        _last_gemini_request_started_at = _gemini._last_gemini_request_started_at
        _gemini._last_gemini_request_started_at = original_timestamp


_cached_gemini_response.cache_clear = _gemini._cached_gemini_response.cache_clear


def wait_for_explanation_rate_limit(song_count: int) -> None:
    _gemini.wait_for_explanation_rate_limit(song_count)


def parse_preferences_with_gemini(user_text: str) -> Tuple[Dict[str, Any], str]:
    original = _preferences._post_to_gemini
    _preferences._post_to_gemini = _post_to_gemini
    try:
        return _preferences.parse_preferences_with_gemini(user_text)
    finally:
        _preferences._post_to_gemini = original


def explain_ranked_songs(
    user_request: str,
    user_prefs: Dict[str, Any],
    ranked_songs: List[Tuple[Dict[str, Any], float, str]],
    retrieval_context_by_song_id: Dict[int, Dict[str, Any]] | None = None,
) -> Tuple[str, Dict[int, str], str]:
    original_post = _explanations._post_to_gemini
    original_wait = _explanations.wait_for_explanation_rate_limit
    _explanations._post_to_gemini = _post_to_gemini
    _explanations.wait_for_explanation_rate_limit = wait_for_explanation_rate_limit
    try:
        return _explanations.explain_ranked_songs(
            user_request=user_request,
            user_prefs=user_prefs,
            ranked_songs=ranked_songs,
            retrieval_context_by_song_id=retrieval_context_by_song_id,
        )
    finally:
        _explanations._post_to_gemini = original_post
        _explanations.wait_for_explanation_rate_limit = original_wait


def rerank_recommendations_with_gemini(
    user_request: str,
    user_prefs: Dict[str, Any],
    ranked_songs: List[Tuple[Dict[str, Any], float, str]],
    retrieval_context_by_song_id: Dict[int, Dict[str, Any]] | None = None,
) -> Tuple[List[Tuple[Dict[str, Any], float, str]], str]:
    original = _explanations._post_to_gemini
    _explanations._post_to_gemini = _post_to_gemini
    try:
        return _explanations.rerank_recommendations_with_gemini(
            user_request=user_request,
            user_prefs=user_prefs,
            ranked_songs=ranked_songs,
            retrieval_context_by_song_id=retrieval_context_by_song_id,
        )
    finally:
        _explanations._post_to_gemini = original
