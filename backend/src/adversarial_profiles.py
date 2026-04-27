ADVERSARIAL_PROFILES = [
    (
        "Empty Inputs",
        {},
    ),
    (
        "Duplicate And Dirty Strings",
        {
            "favorite_genres": [" Rock ", "rock", "ROCK"],
            "favorite_moods": ["moody", "", "  moody  "],
            "preferred_mood_tags": ["cinematic", "CINEMATIC", " neon "],
        },
    ),
    (
        "Zero Blend Weights",
        {
            "favorite_genres": ["rock"],
            "favorite_moods": ["intense"],
            "blend_weights": {"categorical": 0, "numeric": 0},
        },
    ),
    (
        "Broad Preference Surface",
        {
            "favorite_genres": ["pop", "rock", "synthwave", "ambient"],
            "favorite_moods": ["happy", "moody", "focused"],
            "favorite_contexts": ["commute", "study", "night_drive"],
            "preferred_mood_tags": ["cinematic", "bright", "steady", "nostalgic"],
            "target_energy": 0.62,
            "target_valence": 0.58,
            "target_danceability": 0.67,
            "target_tempo_bpm": 108,
        },
    ),
    (
        "Weighted Numeric Bias",
        {
            "favorite_genres": ["lofi", "ambient"],
            "favorite_moods": ["focused", "chill"],
            "target_energy": 0.35,
            "target_acousticness": 0.88,
            "target_instrumental_focus": 0.90,
            "feature_weights": {
                "energy": 0.25,
                "acousticness": 0.25,
                "instrumental_focus": 0.25,
                "tempo_bpm": 0.15,
                "vocal_presence": 0.10,
            },
        },
    ),
]
