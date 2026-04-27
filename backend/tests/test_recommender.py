from backend.src.recommender import Song, UserProfile, Recommender, recommend_songs

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_diversity_penalty_spreads_top_results_across_artists():
    songs = [
        {
            "id": 1,
            "title": "Anchor Pop",
            "artist": "Artist A",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.80,
            "tempo_bpm": 120.0,
            "valence": 0.90,
            "danceability": 0.82,
            "acousticness": 0.18,
        },
        {
            "id": 2,
            "title": "Second Pop",
            "artist": "Artist A",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.79,
            "tempo_bpm": 119.0,
            "valence": 0.88,
            "danceability": 0.81,
            "acousticness": 0.20,
        },
        {
            "id": 3,
            "title": "Fresh Voice",
            "artist": "Artist B",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.77,
            "tempo_bpm": 118.0,
            "valence": 0.86,
            "danceability": 0.79,
            "acousticness": 0.22,
        },
    ]
    user_prefs = {
        "favorite_genres": ["pop"],
        "favorite_moods": ["happy"],
        "target_energy": 0.8,
        "target_valence": 0.9,
        "target_danceability": 0.82,
        "target_acousticness": 0.18,
        "target_tempo_bpm": 120,
        "diversity_settings": {
            "artist_penalty": 0.25,
            "genre_penalty": 0.0,
        },
    }

    results = recommend_songs(user_prefs, songs, k=3)

    assert [song["title"] for song, _, _ in results[:2]] == ["Anchor Pop", "Fresh Voice"]
    assert "repeated artist" in results[2][2]


def test_diversity_penalty_can_prefer_new_genre_in_second_slot():
    songs = [
        {
            "id": 1,
            "title": "Top Pop",
            "artist": "Artist A",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.80,
            "tempo_bpm": 120.0,
            "valence": 0.90,
            "danceability": 0.82,
            "acousticness": 0.18,
        },
        {
            "id": 2,
            "title": "Runner Up Pop",
            "artist": "Artist B",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.79,
            "tempo_bpm": 119.0,
            "valence": 0.88,
            "danceability": 0.81,
            "acousticness": 0.20,
        },
        {
            "id": 3,
            "title": "Different Lane",
            "artist": "Artist C",
            "genre": "rock",
            "mood": "happy",
            "energy": 0.76,
            "tempo_bpm": 118.0,
            "valence": 0.86,
            "danceability": 0.75,
            "acousticness": 0.24,
        },
    ]
    user_prefs = {
        "favorite_genres": ["pop", "rock"],
        "favorite_moods": ["happy"],
        "target_energy": 0.8,
        "target_valence": 0.9,
        "target_danceability": 0.82,
        "target_acousticness": 0.18,
        "target_tempo_bpm": 120,
        "diversity_settings": {
            "artist_penalty": 0.0,
            "genre_penalty": 0.20,
        },
    }

    results = recommend_songs(user_prefs, songs, k=3)

    assert [song["title"] for song, _, _ in results[:2]] == ["Top Pop", "Different Lane"]
    assert "repeated genre" in results[2][2]
