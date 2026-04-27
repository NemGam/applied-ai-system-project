import pytest

from backend.src.adversarial_profiles import ADVERSARIAL_PROFILES
from backend.src.recommender import load_songs, recommend_songs


@pytest.fixture(scope="module")
def songs():
    return load_songs("backend/data/songs.csv")


@pytest.mark.parametrize(("profile_name", "user_prefs"), ADVERSARIAL_PROFILES)
def test_adversarial_profiles_run_end_to_end(profile_name, user_prefs, songs):
    results = recommend_songs(user_prefs, songs, k=5)

    assert len(results) == 5, profile_name
    assert all(0.0 <= score <= 1.0 for _, score, _ in results), profile_name
    assert all(isinstance(explanation, str) and explanation for _, _, explanation in results), profile_name


def test_zeroed_blend_weights_collapse_scores_to_zero(songs):
    results = recommend_songs(
        {
            "favorite_genres": ["rock"],
            "favorite_moods": ["intense"],
            "blend_weights": {"categorical": 0, "numeric": 0},
        },
        songs,
        k=5,
    )

    assert all(score == 0.0 for _, score, _ in results)


def test_broad_tag_profile_scores_lower_than_sparse_tag_profile_for_same_song(songs):
    sparse_results = recommend_songs(
        {
            "favorite_moods": ["moody"],
            "preferred_mood_tags": ["nostalgic", "cinematic"],
        },
        songs,
        k=18,
    )
    broad_results = recommend_songs(
        {
            "favorite_moods": ["moody"],
            "preferred_mood_tags": [
                "nostalgic",
                "cinematic",
                "brooding",
                "stormy",
                "urban",
                "tense",
                "restless",
                "neon",
            ],
        },
        songs,
        k=18,
    )

    sparse_score_by_id = {song["id"]: score for song, score, _ in sparse_results}
    broad_score_by_id = {song["id"]: score for song, score, _ in broad_results}

    assert broad_score_by_id[8] < sparse_score_by_id[8]


def test_duplicate_dirty_inputs_normalize_to_same_ranking_as_clean_inputs(songs):
    dirty_results = recommend_songs(
        {
            "favorite_genres": [" Rock ", "rock", "ROCK"],
            "favorite_moods": ["moody", "", "  moody  "],
            "preferred_mood_tags": ["cinematic", "CINEMATIC", " neon "],
        },
        songs,
        k=5,
    )
    clean_results = recommend_songs(
        {
            "favorite_genres": ["rock"],
            "favorite_moods": ["moody"],
            "preferred_mood_tags": ["cinematic", "neon"],
        },
        songs,
        k=5,
    )

    assert [song["id"] for song, _, _ in dirty_results] == [song["id"] for song, _, _ in clean_results]
