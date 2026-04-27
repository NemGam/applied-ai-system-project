from types import SimpleNamespace

import pytest

from backend.api.routes import (
    AIRecommendationRequest,
    ManualPreferencesInput,
    RecommendationRequest,
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
        get_song_lyrics(1, request)

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
