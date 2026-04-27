from backend.src.recommender import load_songs, recommend_songs, score_song


def test_load_songs_parses_extended_dataset_columns():
    songs = load_songs("backend/data/songs.csv")

    assert len(songs) >= 18

    first_song = songs[0]
    assert isinstance(first_song["id"], int)
    assert isinstance(first_song["energy"], float)
    assert isinstance(first_song["popularity_100"], float)
    assert isinstance(first_song["vocal_presence"], float)
    assert isinstance(first_song["instrumental_focus"], float)
    assert isinstance(first_song["replay_value"], float)
    assert first_song["release_decade"] == "2020s"
    assert "euphoric" in first_song["detailed_mood_tags"]


def test_score_song_rewards_decade_context_and_tag_overlap():
    song = {
        "id": 99,
        "title": "Night Transit",
        "artist": "Metro Bloom",
        "genre": "synthwave",
        "mood": "moody",
        "energy": 0.74,
        "tempo_bpm": 118.0,
        "valence": 0.50,
        "danceability": 0.68,
        "acousticness": 0.28,
        "popularity_100": 80.0,
        "release_decade": "2010s",
        "detailed_mood_tags": "nostalgic;cinematic;neon",
        "vocal_presence": 0.45,
        "instrumental_focus": 0.55,
        "listening_context": "night_drive",
        "replay_value": 0.82,
    }
    user_prefs = {
        "favorite_genres": ["synthwave"],
        "favorite_moods": ["moody"],
        "favorite_decades": ["2010s"],
        "favorite_contexts": ["night_drive"],
        "preferred_mood_tags": ["nostalgic", "cinematic"],
        "target_energy": 0.74,
        "target_valence": 0.50,
        "target_danceability": 0.68,
        "target_acousticness": 0.28,
        "target_tempo_bpm": 118,
        "target_popularity_100": 80,
        "target_vocal_presence": 0.45,
        "target_instrumental_focus": 0.55,
        "target_replay_value": 0.82,
    }

    score, reasons = score_song(user_prefs, song)
    joined_reasons = "; ".join(reasons)

    assert score > 0.95
    assert "release decade (+" in joined_reasons
    assert "context (+" in joined_reasons
    assert "detailed mood (+" in joined_reasons
    assert "popularity (+" in joined_reasons


def test_recommend_songs_without_diversity_penalty_keeps_raw_score_order():
    songs = [
        {
            "id": 1,
            "title": "Best Pop",
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
            "title": "Second Best Pop",
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
            "title": "Different Song",
            "artist": "Artist B",
            "genre": "rock",
            "mood": "happy",
            "energy": 0.70,
            "tempo_bpm": 114.0,
            "valence": 0.76,
            "danceability": 0.70,
            "acousticness": 0.26,
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
            "genre_penalty": 0.0,
        },
    }

    results = recommend_songs(user_prefs, songs, k=3)

    assert [song["title"] for song, _, _ in results] == [
        "Best Pop",
        "Second Best Pop",
        "Different Song",
    ]


def test_recommend_songs_respects_requested_k():
    songs = load_songs("backend/data/songs.csv")
    user_prefs = {
        "favorite_genres": ["lofi", "rock"],
        "favorite_moods": ["focused", "intense"],
        "target_energy": 0.70,
    }

    results = recommend_songs(user_prefs, songs, k=3)

    assert len(results) == 3
