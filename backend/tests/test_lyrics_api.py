from types import SimpleNamespace

import pytest

from backend.api.routes import (
    AIRecommendationRequest,
    AgentRecommendationRequest,
    ManualPreferencesInput,
    RecommendationRequest,
    create_agent_recommendations,
    create_ai_recommendations,
    create_recommendations,
    get_song_lyrics,
)
from backend.src.ai_pipeline import load_lyrics_index
from backend.src.recommender import load_songs


class DummyRequest:
    def __init__(self):
        self.base_url = 'http://testserver/'
        self.app = SimpleNamespace()
        self.app.state = SimpleNamespace()
        self.app.state.songs = load_songs('backend/data/songs.csv')
        self.app.state.lyrics_by_song_id = load_lyrics_index('backend/lyrics')


def test_recommendations_include_has_lyrics_and_lyrics_url_when_text_exists():
    request = DummyRequest()
    payload = RecommendationRequest(
        favorite_genres=['lofi'],
        favorite_moods=['chill'],
        k=5,
    )
    response = create_recommendations(payload, request)

    songs = [item['song'] for item in response['results']]
    lyrics_song = next(song for song in songs if song['id'] == 2)
    assert lyrics_song['has_lyrics'] is True
    assert lyrics_song['lyrics_url'] is not None


def test_song_lyrics_endpoint_returns_text_for_existing_file():
    request = DummyRequest()
    payload = get_song_lyrics(2, request)

    assert payload['song_id'] == 2
    assert 'Midnight coding' in payload['lyrics']


def test_song_lyrics_endpoint_returns_404_when_missing():
    request = DummyRequest()

    with pytest.raises(Exception) as exc_info:
        get_song_lyrics(12, request)

    assert getattr(exc_info.value, 'status_code', None) == 404
    assert getattr(exc_info.value, 'detail', None) == 'Lyrics not found'


def test_ai_recommendations_include_multi_source_retrieval_fields():
    request = DummyRequest()
    payload = AIRecommendationRequest(
        user_text='midnight coding late-night study flow',
        manual_preferences=None,
        k=3,
        retrieval_k=5,
    )

    response = create_ai_recommendations(payload, request)

    assert response['retrieval']['strategy'] == 'metadata+lyrics'
    assert 'source_counts' in response['retrieval']
    assert response['results']
    first_result = response['results'][0]
    assert 'retrieval_breakdown' in first_result
    assert 'matched_sources' in first_result
    assert 'source_reasons' in first_result
    assert 'lyric_snippets' in first_result
    assert 'lyric_snippets' in response['retrieval']['candidates'][0]


def test_ai_recommendations_can_apply_taste_profile_to_natural_language_mode():
    request = DummyRequest()
    payload = AIRecommendationRequest(
        user_text='I want something I would like for studying',
        manual_preferences=None,
        taste_profile=ManualPreferencesInput(
            genre='lofi',
            mood='chill',
            listening_context='study',
            acousticness=0.8,
            vocal_presence=0.35,
        ),
        k=3,
        retrieval_k=5,
    )

    response = create_ai_recommendations(payload, request)

    assert response['input_mode'] == 'natural_language'
    assert response['personalization']['enabled'] is True
    assert response['personalization']['source'] == 'taste_profile'
    assert 'lofi' in response['personalization']['taste_profile']['genres']
    assert response['providers']['parser'].endswith('+taste_profile')


def test_ai_recommendations_honor_no_lyrics_requests_when_gemini_returns_flag(monkeypatch):
    monkeypatch.setattr(
        "backend.src.ai_pipeline._post_to_gemini",
        lambda prompt, temperature=0.1: {
            "favorite_genres": ["ambient"],
            "favorite_moods": ["focused"],
            "favorite_contexts": ["study"],
            "preferred_mood_tags": [],
            "target_energy": None,
            "target_valence": None,
            "target_danceability": None,
            "target_acousticness": None,
            "target_tempo_bpm": None,
            "target_vocal_presence": 0.02,
            "target_instrumental_focus": 0.97,
            "exclude_lyrical_tracks": True,
        },
    )
    request = DummyRequest()
    payload = AIRecommendationRequest(
        user_text='I want songs with no lyrics for studying',
        manual_preferences=None,
        k=5,
        retrieval_k=10,
    )

    response = create_ai_recommendations(payload, request)

    assert response['results']
    assert response['providers']['parser'] == 'gemini'
    assert all(item['song']['has_lyrics'] is False for item in response['results'])


def test_ai_recommendations_return_guardrail_response_for_out_of_scope_request():
    request = DummyRequest()
    payload = AIRecommendationRequest(
        user_text='Give me a pancakes recipe',
        manual_preferences=None,
        k=3,
        retrieval_k=5,
    )

    response = create_ai_recommendations(payload, request)

    assert response['input_mode'] == 'natural_language'
    assert response['guardrail']['triggered'] is True
    assert response['guardrail']['category'] == 'out_of_scope'
    assert response['providers']['ranking'] == 'not_run'
    assert response['retrieval']['candidate_count'] == 0
    assert response['results'] == []


def test_agent_recommendations_can_request_one_clarification_for_low_signal_input():
    request = DummyRequest()
    payload = AgentRecommendationRequest(
        user_text='rock music',
        k=3,
        retrieval_k=5,
    )

    response = create_agent_recommendations(payload, request)

    assert response['agent']['enabled'] is True
    assert response['agent']['status'] == 'needs_clarification'
    assert response['agent']['needs_clarification'] is True
    assert response['agent']['clarification_question']
    assert response['agent']['clarification_slot'] == 'listening_context'
    assert response['providers']['ranking'] == 'not_run'
    assert response['results'] == []


def test_agent_recommendations_complete_after_clarification_answer():
    request = DummyRequest()
    payload = AgentRecommendationRequest(
        user_text='rock music',
        clarification_answer='for driving at night with strong vocals',
        k=3,
        retrieval_k=5,
    )

    response = create_agent_recommendations(payload, request)

    assert response['agent']['status'] == 'completed'
    assert response['agent']['needs_clarification'] is False
    assert response['results']
    assert response['providers']['ranking'] in {'deterministic', 'gemini'}
    assert 'night_drive' in response['detected_preferences']['contexts']
    assert response['agent']['trace'][1]['action'] == 'merge_clarification'
