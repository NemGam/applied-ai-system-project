GENRE_ALIASES = {
    "ambient": ["ambient", "atmospheric"],
    "electronic": ["electronic", "edm"],
    "hip hop": ["hip hop", "hiphop", "rap"],
    "indie pop": ["indie", "indie pop"],
    "jazz": ["jazz"],
    "lofi": ["lofi", "lo-fi"],
    "pop": ["pop"],
    "rock": ["rock"],
    "synthwave": ["synthwave", "retro wave", "retrowave"],
}

MOOD_CUES = {
    "chill": {
        "keywords": ["chill", "calm", "soft", "easygoing", "laid back"],
        "targets": {
            "target_energy": 0.30,
            "target_danceability": 0.38,
            "target_acousticness": 0.76,
            "target_valence": 0.58,
            "target_tempo_bpm": 78.0,
        },
        "tags": ["calm", "gentle", "soft"],
    },
    "focused": {
        "keywords": ["focus", "focused", "study", "studying", "deep work", "coding"],
        "targets": {
            "target_energy": 0.34,
            "target_acousticness": 0.74,
            "target_tempo_bpm": 82.0,
            "target_vocal_presence": 0.24,
            "target_instrumental_focus": 0.82,
        },
        "tags": ["focused", "steady", "immersive"],
    },
    "happy": {
        "keywords": ["happy", "bright", "sunny", "uplifting", "cheerful"],
        "targets": {
            "target_energy": 0.80,
            "target_danceability": 0.82,
            "target_valence": 0.88,
            "target_tempo_bpm": 120.0,
        },
        "tags": ["uplifting", "bright"],
    },
    "intense": {
        "keywords": ["intense", "aggressive", "hard", "power", "workout", "gym"],
        "targets": {
            "target_energy": 0.90,
            "target_danceability": 0.74,
            "target_valence": 0.62,
            "target_tempo_bpm": 138.0,
            "target_vocal_presence": 0.78,
        },
        "tags": ["aggressive", "explosive"],
    },
    "moody": {
        "keywords": ["moody", "dark", "late night", "night drive", "brooding"],
        "targets": {
            "target_energy": 0.68,
            "target_danceability": 0.68,
            "target_valence": 0.42,
            "target_tempo_bpm": 108.0,
        },
        "tags": ["nocturnal", "cinematic", "brooding"],
    },
    "relaxed": {
        "keywords": ["relaxed", "cozy", "warm", "gentle", "quiet"],
        "targets": {
            "target_energy": 0.32,
            "target_acousticness": 0.84,
            "target_danceability": 0.42,
            "target_valence": 0.64,
            "target_tempo_bpm": 74.0,
        },
        "tags": ["warm", "cozy", "gentle"],
    },
    "energetic": {
        "keywords": ["energetic", "hype", "party", "pump up"],
        "targets": {
            "target_energy": 0.86,
            "target_danceability": 0.84,
            "target_valence": 0.76,
            "target_tempo_bpm": 126.0,
        },
        "tags": ["bright", "motivational"],
    },
}

CONTEXT_CUES = {
    "study": {
        "keywords": ["study", "studying", "homework", "reading", "focus", "late-night studying"],
        "targets": {
            "target_energy": 0.32,
            "target_acousticness": 0.78,
            "target_tempo_bpm": 80.0,
            "target_vocal_presence": 0.26,
            "target_instrumental_focus": 0.84,
        },
        "tags": ["focused", "steady", "nocturnal"],
    },
    "deep_work": {
        "keywords": ["deep work", "coding", "programming", "heads down"],
        "targets": {
            "target_energy": 0.38,
            "target_tempo_bpm": 82.0,
            "target_vocal_presence": 0.18,
            "target_instrumental_focus": 0.90,
        },
        "tags": ["immersive", "clear-headed", "steady"],
    },
    "sleep": {
        "keywords": ["sleep", "fall asleep", "bedtime"],
        "targets": {
            "target_energy": 0.22,
            "target_acousticness": 0.88,
            "target_tempo_bpm": 64.0,
            "target_vocal_presence": 0.12,
            "target_instrumental_focus": 0.92,
        },
        "tags": ["weightless", "gentle", "ethereal"],
    },
    "reading": {
        "keywords": ["reading", "book", "library"],
        "targets": {
            "target_energy": 0.34,
            "target_acousticness": 0.86,
            "target_tempo_bpm": 74.0,
            "target_vocal_presence": 0.18,
            "target_instrumental_focus": 0.86,
        },
        "tags": ["nostalgic", "gentle", "rainy"],
    },
    "cafe": {
        "keywords": ["cafe", "coffee shop", "coffeehouse"],
        "targets": {
            "target_energy": 0.42,
            "target_acousticness": 0.76,
            "target_tempo_bpm": 92.0,
            "target_vocal_presence": 0.42,
        },
        "tags": ["warm", "cozy", "unhurried"],
    },
    "night_drive": {
        "keywords": ["night drive", "driving at night", "after dark", "late night drive"],
        "targets": {
            "target_energy": 0.72,
            "target_danceability": 0.70,
            "target_valence": 0.46,
            "target_tempo_bpm": 110.0,
        },
        "tags": ["nocturnal", "cinematic", "neon"],
    },
    "workout": {
        "keywords": ["workout", "gym", "run", "running", "training"],
        "targets": {
            "target_energy": 0.92,
            "target_danceability": 0.82,
            "target_valence": 0.74,
            "target_tempo_bpm": 136.0,
            "target_vocal_presence": 0.82,
        },
        "tags": ["motivational", "adrenaline", "confident"],
    },
    "party": {
        "keywords": ["party", "pregame", "celebration"],
        "targets": {
            "target_energy": 0.88,
            "target_danceability": 0.86,
            "target_valence": 0.82,
            "target_tempo_bpm": 124.0,
        },
        "tags": ["carefree", "uplifting", "bright"],
    },
    "commute": {
        "keywords": ["commute", "morning train", "bus ride"],
        "targets": {
            "target_energy": 0.70,
            "target_danceability": 0.72,
            "target_valence": 0.74,
            "target_tempo_bpm": 112.0,
        },
        "tags": ["bright", "steady"],
    },
    "walk": {
        "keywords": ["walk", "walking", "stroll"],
        "targets": {
            "target_energy": 0.58,
            "target_danceability": 0.60,
            "target_valence": 0.70,
            "target_tempo_bpm": 102.0,
        },
        "tags": ["carefree", "warm"],
    },
    "dinner": {
        "keywords": ["dinner", "meal", "cooking"],
        "targets": {
            "target_energy": 0.40,
            "target_acousticness": 0.68,
            "target_tempo_bpm": 88.0,
            "target_vocal_presence": 0.48,
        },
        "tags": ["warm", "unhurried"],
    },
}

FREEFORM_FEATURE_CUES = {
    "acoustic": {"target_acousticness": 0.90, "target_instrumental_focus": 0.70},
    "acousticness": {"target_acousticness": 0.90},
    "instrumental": {"target_instrumental_focus": 0.94, "target_vocal_presence": 0.08},
    "instrumentals": {"target_instrumental_focus": 0.94, "target_vocal_presence": 0.08},
    "instrumental only": {"target_instrumental_focus": 0.97, "target_vocal_presence": 0.04},
    "lyricless": {"target_instrumental_focus": 0.94, "target_vocal_presence": 0.08},
    "no vocals": {"target_instrumental_focus": 0.97, "target_vocal_presence": 0.02},
    "without vocals": {"target_instrumental_focus": 0.97, "target_vocal_presence": 0.02},
    "no singing": {"target_instrumental_focus": 0.97, "target_vocal_presence": 0.02},
    "without singing": {"target_instrumental_focus": 0.97, "target_vocal_presence": 0.02},
    "vocals": {"target_vocal_presence": 0.70},
    "vocal": {"target_vocal_presence": 0.70},
    "singing": {"target_vocal_presence": 0.72},
    "soft vocals": {"target_vocal_presence": 0.42},
    "danceable": {"target_danceability": 0.82},
    "upbeat": {"target_energy": 0.82, "target_valence": 0.78},
    "slow": {"target_tempo_bpm": 72.0},
    "fast": {"target_tempo_bpm": 132.0},
}

NUMERIC_KEYS = [
    "target_energy",
    "target_valence",
    "target_danceability",
    "target_acousticness",
    "target_tempo_bpm",
    "target_vocal_presence",
    "target_instrumental_focus",
]

LIST_KEYS = [
    "favorite_genres",
    "favorite_moods",
    "favorite_contexts",
    "preferred_mood_tags",
]

FLAG_KEYS = [
    "exclude_lyrical_tracks",
]

DISPLAY_KEY_ORDER = [
    "genres",
    "moods",
    "contexts",
    "mood_tags",
    "energy",
    "danceability",
    "acousticness",
    "vocal_presence",
    "instrumental_focus",
    "valence",
    "tempo_bpm",
]

AGENT_CLARIFICATION_CHOICES = {
    "listening_context": [
        "studying",
        "working out",
        "driving at night",
    ],
    "vocal_presence": [
        "mostly instrumental",
        "soft vocals",
        "strong vocals",
    ],
    "mood": [
        "more chill",
        "more energetic",
        "more moody",
    ],
    "genre": [
        "lofi",
        "rock",
        "electronic",
    ],
}

MUSIC_DOMAIN_TERMS = {
    "music",
    "song",
    "songs",
    "track",
    "tracks",
    "playlist",
    "playlists",
    "album",
    "albums",
    "artist",
    "artists",
    "band",
    "bands",
    "genre",
    "genres",
    "lyrics",
    "lyric",
    "listen",
    "listening",
    "vibe",
    "vibes",
    "bpm",
    "melody",
    "melodies",
    "instrumental",
    "instrumentals",
    "vocal",
    "vocals",
    "acoustic",
}

OUT_OF_SCOPE_CUES = [
    "recipe",
    "recipes",
    "pancake",
    "pancakes",
    "cook",
    "cooking",
    "bake",
    "baking",
    "ingredient",
    "ingredients",
    "weather",
    "forecast",
    "temperature",
    "news",
    "stock price",
    "stocks",
    "crypto",
    "code this",
    "debug this code",
    "solve this math",
    "math problem",
    "homework answer",
]

LYRIC_THEME_CUES = {
    "chill": ["quiet", "soft", "slow", "warm", "drift"],
    "focused": ["coding", "keys", "loop", "flow", "steady", "quiet"],
    "happy": ["sunlight", "bright", "smile", "golden"],
    "intense": ["pressure", "fire", "storm", "higher", "adrenaline"],
    "moody": ["night", "midnight", "blue", "dark", "rain"],
    "relaxed": ["gentle", "breathe", "slow", "warm"],
    "energetic": ["ignite", "fire", "higher", "run", "lightning"],
    "study": ["coding", "quiet", "keys", "loop", "room", "flow"],
    "deep_work": ["coding", "focus", "loop", "steady", "flow"],
    "sleep": ["dream", "moon", "slow", "drift", "gentle"],
    "reading": ["pages", "quiet", "lamplight", "rain"],
    "cafe": ["coffee", "corner", "warm", "window"],
    "night_drive": ["night", "midnight", "lights", "neon", "highway"],
    "workout": ["pressure", "storm", "higher", "limits", "fire"],
    "party": ["dance", "lights", "crowd", "celebration"],
    "commute": ["train", "morning", "city", "ride"],
    "walk": ["street", "steps", "wind", "stroll"],
    "dinner": ["kitchen", "candle", "slow", "warm"],
    "nocturnal": ["night", "midnight", "moon", "dark", "blue"],
    "gentle": ["quiet", "soft", "slow", "breathe"],
    "warm": ["warm", "golden", "glow", "ember"],
    "immersive": ["echo", "loop", "flow", "inside"],
}
