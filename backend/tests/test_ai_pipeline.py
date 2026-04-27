import io
import urllib.error

from backend.src.ai_pipeline import (
    _cached_gemini_response,
    _extract_llm_song_explanations,
    _extract_llm_reranked_song_ids,
    explain_ranked_songs,
    gemini_explanations_enabled,
    gemini_rerank_top_n,
    gemini_reranking_enabled,
    heuristic_parse_preferences,
    is_out_of_scope_music_request,
    load_lyrics_index,
    manual_preferences_to_recommender,
    merge_recommender_preferences,
    personalize_recommender_preferences,
    rerank_recommendations_with_gemini,
    retrieve_lyric_candidates,
    retrieve_metadata_candidates,
    retrieve_candidate_songs,
    wait_for_explanation_rate_limit,
)
from backend.src.recommender import load_songs


def test_heuristic_parser_extracts_study_request_preferences():
    parsed = heuristic_parse_preferences(
        "I want chill music for late-night studying with soft vocals"
    )

    assert "chill" in parsed["favorite_moods"]
    assert "focused" in parsed["favorite_moods"]
    assert "study" in parsed["favorite_contexts"]
    assert parsed["target_energy"] < 0.4
    assert parsed["target_acousticness"] >= 0.7
    assert 0.2 <= parsed["target_vocal_presence"] <= 0.45
    assert "nocturnal" in parsed["preferred_mood_tags"]


def test_out_of_scope_detector_flags_clear_non_music_request():
    parsed = heuristic_parse_preferences("Give me a pancakes recipe")

    assert is_out_of_scope_music_request("Give me a pancakes recipe", parsed) is True


def test_out_of_scope_detector_allows_music_requests_with_domain_terms():
    parsed = heuristic_parse_preferences("Give me a chill study playlist")

    assert is_out_of_scope_music_request("Give me a chill study playlist", parsed) is False


def test_manual_preferences_are_translated_for_recommender():
    translated = manual_preferences_to_recommender(
        {
            "genre": "lofi",
            "mood": "chill",
            "listening_context": "study",
            "energy": 0.3,
            "acousticness": 0.8,
            "vocal_presence": 0.5,
            "preferred_mood_tags": ["soft", "late-night"],
        }
    )

    assert translated["favorite_genres"] == ["lofi"]
    assert translated["favorite_moods"] == ["chill"]
    assert translated["favorite_contexts"] == ["study"]
    assert translated["target_energy"] == 0.3
    assert translated["target_acousticness"] == 0.8
    assert translated["target_vocal_presence"] == 0.5


def test_merge_preferences_keeps_manual_values_authoritative_and_fills_gaps():
    manual = manual_preferences_to_recommender(
        {
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.3,
            "listening_context": "study",
        }
    )
    parsed = {
        "favorite_genres": ["ambient"],
        "favorite_moods": ["focused"],
        "favorite_contexts": ["deep_work"],
        "preferred_mood_tags": ["nocturnal", "soft"],
        "target_energy": 0.65,
        "target_acousticness": 0.84,
        "target_vocal_presence": 0.28,
    }

    merged = merge_recommender_preferences(manual, parsed)

    assert merged["favorite_genres"] == ["lofi", "ambient"]
    assert merged["favorite_moods"] == ["chill", "focused"]
    assert merged["favorite_contexts"] == ["study", "deep_work"]
    assert merged["target_energy"] == 0.3
    assert merged["target_acousticness"] == 0.84
    assert merged["target_vocal_presence"] == 0.28


def test_personalization_keeps_prompt_preferences_primary():
    parsed = {
        "favorite_moods": ["happy"],
        "favorite_contexts": ["party"],
        "target_energy": 0.88,
        "target_valence": 0.9,
    }
    taste_profile = manual_preferences_to_recommender(
        {
            "genre": "lofi",
            "mood": "chill",
            "listening_context": "study",
            "energy": 0.3,
            "valence": 0.45,
            "acousticness": 0.8,
        }
    )

    personalized = personalize_recommender_preferences(parsed, taste_profile)

    assert personalized["favorite_moods"] == ["happy"]
    assert personalized["favorite_contexts"] == ["party"]
    assert personalized["favorite_genres"] == ["lofi"]
    assert personalized["target_energy"] > 0.7
    assert personalized["target_valence"] > 0.8
    assert personalized["target_acousticness"] == 0.8


def test_retrieval_surfaces_relevant_low_energy_study_tracks():
    songs = load_songs("backend/data/songs.csv")
    lyrics_by_song_id = load_lyrics_index("backend/lyrics")
    user_prefs = heuristic_parse_preferences(
        "I want chill music for late-night studying with soft vocals"
    )

    retrieved = retrieve_candidate_songs(
        user_request="I want chill music for late-night studying with soft vocals",
        user_prefs=user_prefs,
        songs=songs,
        lyrics_by_song_id=lyrics_by_song_id,
        limit=5,
    )

    top_titles = [item["song"]["title"] for item in retrieved]

    assert retrieved[0]["song"]["title"] in {"Library Chill", "Midnight Coding"}
    assert "Midnight Coding" in top_titles
    assert retrieved == sorted(retrieved, key=lambda item: item["retrieval_score"], reverse=True)
    assert any(item["song"]["genre"] in {"lofi", "ambient"} for item in retrieved[:3])
    assert any("metadata" in item["matched_sources"] for item in retrieved)


def test_metadata_retrieval_only_marks_metadata_source():
    songs = load_songs("backend/data/songs.csv")
    user_prefs = heuristic_parse_preferences("I want focused lofi for studying")

    retrieved = retrieve_metadata_candidates(
        user_request="I want focused lofi for studying",
        user_prefs=user_prefs,
        songs=songs,
        limit=3,
    )

    assert retrieved[0]["retrieval_breakdown"]["metadata"] > 0
    assert retrieved[0]["retrieval_breakdown"]["lyrics"] == 0
    assert retrieved[0]["matched_sources"] == ["metadata"]


def test_lyrics_retrieval_finds_song_from_lyric_language():
    songs = load_songs("backend/data/songs.csv")
    lyrics_by_song_id = load_lyrics_index("backend/lyrics")
    user_prefs = {"favorite_moods": ["focused"], "favorite_contexts": ["study"]}

    retrieved = retrieve_lyric_candidates(
        user_request="midnight coding afterglow low-lit flow",
        user_prefs=user_prefs,
        songs=songs,
        lyrics_by_song_id=lyrics_by_song_id,
        limit=3,
    )

    assert retrieved[0]["song"]["title"] == "Midnight Coding"
    assert retrieved[0]["retrieval_breakdown"]["lyrics"] > 0
    assert retrieved[0]["matched_sources"] == ["lyrics"]
    assert any("lyric" in reason for reason in retrieved[0]["source_reasons"]["lyrics"])


def test_merged_retrieval_can_report_both_sources_for_same_song():
    songs = load_songs("backend/data/songs.csv")
    lyrics_by_song_id = load_lyrics_index("backend/lyrics")
    user_prefs = {
        "favorite_genres": ["lofi"],
        "favorite_moods": ["focused"],
        "favorite_contexts": ["study"],
        "preferred_mood_tags": ["nocturnal"],
    }

    retrieved = retrieve_candidate_songs(
        user_request="midnight coding late-night study flow",
        user_prefs=user_prefs,
        songs=songs,
        lyrics_by_song_id=lyrics_by_song_id,
        limit=5,
    )

    midnight_coding = next(item for item in retrieved if item["song"]["title"] == "Midnight Coding")
    assert "metadata" in midnight_coding["matched_sources"]
    assert "lyrics" in midnight_coding["matched_sources"]
    assert midnight_coding["retrieval_breakdown"]["metadata"] > 0
    assert midnight_coding["retrieval_breakdown"]["lyrics"] > 0


def test_gemini_explanations_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("GEMINI_EXPLANATIONS_ENABLED", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    assert gemini_explanations_enabled() is False

    overall, explanations, provider = explain_ranked_songs(
        user_request="focused lofi for studying",
        user_prefs={"favorite_genres": ["lofi"], "favorite_contexts": ["study"]},
        ranked_songs=[
            (
                {
                    "id": 1,
                    "title": "Library Chill",
                    "artist": "Test Artist",
                    "genre": "lofi",
                    "mood": "focused",
                    "listening_context": "study",
                    "energy": 0.3,
                    "acousticness": 0.8,
                    "vocal_presence": 0.2,
                    "tempo_bpm": 80,
                },
                0.91,
                "math explanation",
            )
        ],
    )

    assert provider == "heuristic"
    assert overall
    assert explanations[1]


def test_gemini_reranking_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("GEMINI_RERANKING_ENABLED", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    assert gemini_reranking_enabled() is False
    assert gemini_rerank_top_n() == 8


def test_wait_for_explanation_rate_limit_scales_with_song_count(monkeypatch):
    slept_for: list[float] = []

    monkeypatch.setenv("GEMINI_EXPLANATION_DELAY_PER_SONG_SECONDS", "1.5")
    monkeypatch.setattr("backend.src.ai_pipeline.time.sleep", slept_for.append)

    wait_for_explanation_rate_limit(3)

    assert slept_for == [4.5]


def test_extract_llm_song_explanations_falls_back_to_rank_order_when_ids_missing():
    ranked_songs = [
        ({"id": 2, "title": "First"}, 0.9, "math a"),
        ({"id": 5, "title": "Second"}, 0.8, "math b"),
    ]
    response = {
        "song_explanations": [
            {"text": "First explanation"},
            {"reason": "Second explanation"},
        ]
    }

    explanations = _extract_llm_song_explanations(response, ranked_songs)

    assert explanations == {
        2: "First explanation",
        5: "Second explanation",
    }


def test_extract_llm_reranked_song_ids_filters_invalid_items():
    ranked_songs = [
        ({"id": 2, "title": "First"}, 0.9, "math a"),
        ({"id": 5, "title": "Second"}, 0.8, "math b"),
    ]
    response = {
        "ranking": [
            {"id": 5, "rank": 1},
            {"song_id": 2, "rank": 2},
            {"id": 5, "rank": 3},
            {"id": 999, "rank": 4},
        ]
    }

    reranked_ids = _extract_llm_reranked_song_ids(response, ranked_songs)

    assert reranked_ids == [5, 2]


def test_rerank_recommendations_with_gemini_reorders_top_slice(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_RERANKING_ENABLED", "true")
    monkeypatch.setenv("GEMINI_RERANK_TOP_N", "2")
    monkeypatch.setattr(
        "backend.src.ai_pipeline._post_to_gemini",
        lambda prompt, temperature=0.1: {
            "ranking": [
                {"id": 2, "rank": 1},
                {"id": 1, "rank": 2},
            ]
        },
    )

    ranked_songs = [
        ({"id": 1, "title": "First", "genre": "lofi", "mood": "focused"}, 0.95, "math a"),
        ({"id": 2, "title": "Second", "genre": "ambient", "mood": "focused"}, 0.9, "math b"),
        ({"id": 3, "title": "Third", "genre": "jazz", "mood": "chill"}, 0.8, "math c"),
    ]

    reranked, provider = rerank_recommendations_with_gemini(
        user_request="focused study music",
        user_prefs={"favorite_moods": ["focused"], "favorite_contexts": ["study"]},
        ranked_songs=ranked_songs,
    )

    assert provider == "gemini"
    assert [song["id"] for song, _, _ in reranked] == [2, 1, 3]


def test_rerank_recommendations_with_gemini_falls_back_when_response_incomplete(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_RERANKING_ENABLED", "true")
    monkeypatch.setattr(
        "backend.src.ai_pipeline._post_to_gemini",
        lambda prompt, temperature=0.1: {"ranking": [{"id": 2, "rank": 1}]},
    )

    ranked_songs = [
        ({"id": 1, "title": "First"}, 0.95, "math a"),
        ({"id": 2, "title": "Second"}, 0.9, "math b"),
    ]

    reranked, provider = rerank_recommendations_with_gemini(
        user_request="focused study music",
        user_prefs={"favorite_moods": ["focused"]},
        ranked_songs=ranked_songs,
    )

    assert provider == "deterministic"
    assert reranked == ranked_songs


def test_cached_gemini_response_retries_once_after_429(monkeypatch):
    _cached_gemini_response.cache_clear()
    calls: list[str] = []
    sleeps: list[float] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"candidates":[{"content":{"parts":[{"text":"{\\"overall_explanation\\": \\"ok\\"}"}]}}]}'

    def fake_urlopen(request, timeout):
        calls.append("urlopen")
        if len(calls) == 1:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=429,
                msg="Too Many Requests",
                hdrs={"Retry-After": "3"},
                fp=io.BytesIO(b""),
            )
        return FakeResponse()

    monotonic_values = iter([10.0, 10.0, 16.0, 16.0])

    monkeypatch.setenv("GEMINI_HTTP_429_MAX_RETRIES", "2")
    monkeypatch.setenv("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", "1.5")
    monkeypatch.setattr("backend.src.ai_pipeline.urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("backend.src.ai_pipeline.time.sleep", sleeps.append)
    monkeypatch.setattr("backend.src.ai_pipeline.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("backend.src.ai_pipeline._last_gemini_request_started_at", 0.0)

    response = _cached_gemini_response("key", "model", "prompt", 0.2)

    assert response["overall_explanation"] == "ok"
    assert calls == ["urlopen", "urlopen"]
    assert sleeps == [3.0, 1.5]
