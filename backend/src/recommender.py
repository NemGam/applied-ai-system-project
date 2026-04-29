from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

@dataclass
class Song:
    """Represents a song and its attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity_100: float = 0.0
    release_decade: str = ""
    detailed_mood_tags: str = ""
    vocal_presence: float = 0.0
    instrumental_focus: float = 0.0
    listening_context: str = ""
    replay_value: float = 0.0

@dataclass
class UserProfile:
    """Represents a user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """Implements recommendation logic with an object-oriented interface."""
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Returns up to k recommended songs for a user profile."""
        user_prefs = {
            "favorite_genres": [user.favorite_genre],
            "favorite_moods": [user.favorite_mood],
            "target_energy": user.target_energy,
        }
        ranked = recommend_songs(user_prefs, [song.__dict__ for song in self.songs], k=k)
        song_by_id = {song.id: song for song in self.songs}
        return [song_by_id[int(item[0]["id"])] for item in ranked if int(item[0]["id"]) in song_by_id]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns a human-readable explanation for a recommendation."""
        user_prefs = {
            "favorite_genres": [user.favorite_genre],
            "favorite_moods": [user.favorite_mood],
            "target_energy": user.target_energy,
        }
        score, reasons = score_song(user_prefs, song.__dict__)
        return f"Score {score:.3f}: " + "; ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file into typed dictionaries."""
    songs: List[Dict] = []
    int_fields = {"id"}
    float_fields = {
        "energy",
        "tempo_bpm",
        "valence",
        "danceability",
        "acousticness",
        "popularity_100",
        "vocal_presence",
        "instrumental_focus",
        "replay_value",
    }

    with open(csv_path, mode="r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            song: Dict = {}
            for key, value in row.items():
                if key in int_fields:
                    song[key] = int(value)
                elif key in float_fields:
                    song[key] = float(value)
                else:
                    song[key] = value
            songs.append(song)

    return songs


def _get_preference_list(user_prefs: Dict, plural_key: str, singular_key: str) -> List[str]:
    values = user_prefs.get(plural_key, user_prefs.get(singular_key, []))
    if isinstance(values, str):
        values = [values]
    return [str(value).strip().lower() for value in values if str(value).strip()]


def _parse_song_tags(raw_tags: str) -> List[str]:
    return [tag.strip().lower() for tag in str(raw_tags).split(";") if tag.strip()]


def _get_weight_map(user_prefs: Dict, key: str, defaults: Dict[str, float]) -> Dict[str, float]:
    provided = user_prefs.get(key, {})
    if not isinstance(provided, dict):
        provided = {}
    merged = defaults.copy()
    for field, value in provided.items():
        try:
            merged[field] = float(value)
        except (TypeError, ValueError):
            continue
    return merged


def _get_diversity_settings(user_prefs: Dict) -> Dict[str, float]:
    settings = user_prefs.get("diversity_settings", {})
    if not isinstance(settings, dict):
        settings = {}

    defaults = {
        "artist_penalty": 0.12,
        "genre_penalty": 0.08,
    }
    merged = defaults.copy()
    for key, value in settings.items():
        try:
            merged[key] = max(0.0, float(value))
        except (TypeError, ValueError):
            continue
    return merged

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Computes a recommendation score and explanation reasons for one song."""
    favorite_genres = set(_get_preference_list(user_prefs, "favorite_genres", "genre"))
    favorite_moods = set(_get_preference_list(user_prefs, "favorite_moods", "mood"))
    favorite_decades = set(_get_preference_list(user_prefs, "favorite_decades", "release_decade"))
    favorite_contexts = set(_get_preference_list(user_prefs, "favorite_contexts", "listening_context"))
    preferred_mood_tags = set(_get_preference_list(user_prefs, "preferred_mood_tags", "detailed_mood_tags"))

    song_genre = str(song.get("genre", "")).lower()
    song_mood = str(song.get("mood", "")).lower()
    song_decade = str(song.get("release_decade", "")).lower()
    song_context = str(song.get("listening_context", "")).lower()
    song_tags = set(_parse_song_tags(song.get("detailed_mood_tags", "")))

    genre_match = 1.0 if song_genre in favorite_genres else 0.0
    mood_match = 1.0 if song_mood in favorite_moods else 0.0
    decade_match = 1.0 if favorite_decades and song_decade in favorite_decades else 0.0
    context_match = 1.0 if favorite_contexts and song_context in favorite_contexts else 0.0
    tag_match = len(song_tags & preferred_mood_tags) / max(len(preferred_mood_tags), 1) if preferred_mood_tags else 0.0

    def closeness(song_value: float, target_value: float, tolerance: float) -> float:
        return max(0.0, 1.0 - abs(song_value - target_value) / tolerance)

    category_weights = _get_weight_map(
        user_prefs,
        "category_weights",
        {
            "genre": 0.50,
            "mood": 0.30,
            "release_decade": 0.08,
            "listening_context": 0.07,
            "detailed_mood_tags": 0.05,
        },
    )
    active_category_features: List[Tuple[str, float, float]] = [
        ("genre", genre_match, category_weights.get("genre", 0.0)),
        ("mood", mood_match, category_weights.get("mood", 0.0)),
    ]
    if favorite_decades:
        active_category_features.append(("release_decade", decade_match, category_weights.get("release_decade", 0.0)))
    if favorite_contexts:
        active_category_features.append(("listening_context", context_match, category_weights.get("listening_context", 0.0)))
    if preferred_mood_tags:
        active_category_features.append(("detailed_mood_tags", tag_match, category_weights.get("detailed_mood_tags", 0.0)))

    category_weight_sum = sum(weight for _, _, weight in active_category_features)
    categorical_score = 0.0
    normalized_category: Dict[str, float] = {}
    category_match_scores: Dict[str, float] = {}
    if category_weight_sum > 0:
        for label, match_score, weight in active_category_features:
            normalized_weight = weight / category_weight_sum
            normalized_category[label] = normalized_weight
            category_match_scores[label] = match_score
            categorical_score += normalized_weight * match_score

    numeric_weights = _get_weight_map(
        user_prefs,
        "feature_weights",
        {
            "energy": 0.18,
            "valence": 0.12,
            "danceability": 0.12,
            "acousticness": 0.10,
            "tempo_bpm": 0.10,
            "popularity_100": 0.12,
            "vocal_presence": 0.08,
            "instrumental_focus": 0.08,
            "replay_value": 0.10,
        },
    )
    numeric_features = [
        ("energy", ["target_energy", "energy"], 0.50, numeric_weights.get("energy", 0.0), "energy"),
        ("valence", ["target_valence", "valence"], 0.50, numeric_weights.get("valence", 0.0), "valence"),
        ("danceability", ["target_danceability", "danceability"], 0.50, numeric_weights.get("danceability", 0.0), "danceability"),
        ("acousticness", ["target_acousticness", "acousticness"], 0.50, numeric_weights.get("acousticness", 0.0), "acousticness"),
        ("tempo_bpm", ["target_tempo_bpm", "tempo_bpm"], 40.0, numeric_weights.get("tempo_bpm", 0.0), "tempo"),
        ("popularity_100", ["target_popularity_100", "popularity_100"], 30.0, numeric_weights.get("popularity_100", 0.0), "popularity"),
        ("vocal_presence", ["target_vocal_presence", "vocal_presence"], 0.50, numeric_weights.get("vocal_presence", 0.0), "vocal_presence"),
        ("instrumental_focus", ["target_instrumental_focus", "instrumental_focus"], 0.50, numeric_weights.get("instrumental_focus", 0.0), "instrumental_focus"),
        ("replay_value", ["target_replay_value", "replay_value"], 0.50, numeric_weights.get("replay_value", 0.0), "replay_value"),
    ]

    provided_numeric: List[Tuple[str, float, float, str]] = []
    for song_key, target_keys, tolerance, weight, label in numeric_features:
        target_value = None
        for key in target_keys:
            if key in user_prefs and user_prefs[key] is not None:
                target_value = float(user_prefs[key])
                break
        if target_value is not None:
            close = closeness(float(song.get(song_key, 0.0)), target_value, tolerance)
            provided_numeric.append((label, close, weight, song_key))

    numeric_weight_sum = sum(weight for _, _, weight, _ in provided_numeric)
    numeric_score = 0.0
    normalized_numeric: Dict[str, float] = {}
    numeric_closeness: Dict[str, float] = {}
    if numeric_weight_sum > 0:
        for label, close, weight, _ in provided_numeric:
            normalized_weight = weight / numeric_weight_sum
            normalized_numeric[label] = normalized_weight
            numeric_closeness[label] = close
            numeric_score += normalized_weight * close

    blend_weights = _get_weight_map(
        user_prefs,
        "blend_weights",
        {"categorical": 0.72, "numeric": 0.28},
    )
    blend_weight_sum = blend_weights.get("categorical", 0.0) + blend_weights.get("numeric", 0.0)
    if blend_weight_sum <= 0:
        final_score = 0.0
    else:
        final_score = (
            blend_weights.get("categorical", 0.0) / blend_weight_sum * categorical_score
            + blend_weights.get("numeric", 0.0) / blend_weight_sum * numeric_score
        )

    reasons: List[str] = []
    categorical_blend = blend_weights.get("categorical", 0.0) / blend_weight_sum if blend_weight_sum > 0 else 0.0
    numeric_blend = blend_weights.get("numeric", 0.0) / blend_weight_sum if blend_weight_sum > 0 else 0.0
    genre_points = categorical_blend * normalized_category.get("genre", 0.0) * category_match_scores.get("genre", 0.0)
    mood_points = categorical_blend * normalized_category.get("mood", 0.0) * category_match_scores.get("mood", 0.0)
    decade_points = categorical_blend * normalized_category.get("release_decade", 0.0) * category_match_scores.get("release_decade", 0.0)
    context_points = categorical_blend * normalized_category.get("listening_context", 0.0) * category_match_scores.get("listening_context", 0.0)
    tag_points = categorical_blend * normalized_category.get("detailed_mood_tags", 0.0) * category_match_scores.get("detailed_mood_tags", 0.0)
    energy_points = numeric_blend * normalized_numeric.get("energy", 0.0) * numeric_closeness.get("energy", 0.0)
    valence_points = numeric_blend * normalized_numeric.get("valence", 0.0) * numeric_closeness.get("valence", 0.0)
    danceability_points = numeric_blend * normalized_numeric.get("danceability", 0.0) * numeric_closeness.get("danceability", 0.0)
    acousticness_points = numeric_blend * normalized_numeric.get("acousticness", 0.0) * numeric_closeness.get("acousticness", 0.0)
    tempo_points = numeric_blend * normalized_numeric.get("tempo", 0.0) * numeric_closeness.get("tempo", 0.0)
    popularity_points = numeric_blend * normalized_numeric.get("popularity", 0.0) * numeric_closeness.get("popularity", 0.0)
    vocal_points = numeric_blend * normalized_numeric.get("vocal_presence", 0.0) * numeric_closeness.get("vocal_presence", 0.0)
    instrumental_points = numeric_blend * normalized_numeric.get("instrumental_focus", 0.0) * numeric_closeness.get("instrumental_focus", 0.0)
    replay_points = numeric_blend * normalized_numeric.get("replay_value", 0.0) * numeric_closeness.get("replay_value", 0.0)


    # Generate reasons
    if genre_match:
        reasons.append(f"genre (+{genre_points:.3f})")
    if mood_match:
        reasons.append(f"mood (+{mood_points:.3f})")
    if decade_match:
        reasons.append(f"release decade (+{decade_points:.3f})")
    if context_match:
        reasons.append(f"context (+{context_points:.3f})")
    if tag_match >= 0.50:
        reasons.append(f"detailed mood (+{tag_points:.3f})")
    if numeric_closeness.get("energy", 0.0) >= 0.70:
        reasons.append(f"energy (+{energy_points:.3f})")
    if numeric_closeness.get("valence", 0.0) >= 0.70:
        reasons.append(f"valence (+{valence_points:.3f})")
    if numeric_closeness.get("danceability", 0.0) >= 0.70:
        reasons.append(f"danceability (+{danceability_points:.3f})")
    if numeric_closeness.get("acousticness", 0.0) >= 0.70:
        reasons.append(f"acousticness (+{acousticness_points:.3f})")
    if numeric_closeness.get("tempo", 0.0) >= 0.70:
        reasons.append(f"tempo (+{tempo_points:.3f})")
    if numeric_closeness.get("popularity", 0.0) >= 0.70:
        reasons.append(f"popularity (+{popularity_points:.3f})")
    if numeric_closeness.get("vocal_presence", 0.0) >= 0.70:
        reasons.append(f"vocal presence (+{vocal_points:.3f})")
    if numeric_closeness.get("instrumental_focus", 0.0) >= 0.70:
        reasons.append(f"instrumental focus (+{instrumental_points:.3f})")
    if numeric_closeness.get("replay_value", 0.0) >= 0.70:
        reasons.append(f"replay value (+{replay_points:.3f})")
    if not reasons:
        reasons.append("some feature overlap (+0.000)")

    return final_score, reasons


def _apply_diversity_rerank(
    user_prefs: Dict,
    scored_songs: List[Tuple[Dict, float, str]],
    k: int,
) -> List[Tuple[Dict, float, str]]:
    if not scored_songs or k <= 0:
        return []

    diversity_settings = _get_diversity_settings(user_prefs)
    artist_penalty_weight = diversity_settings.get("artist_penalty", 0.0)
    genre_penalty_weight = diversity_settings.get("genre_penalty", 0.0)

    if artist_penalty_weight <= 0 and genre_penalty_weight <= 0:
        return scored_songs[:k]

    selected: List[Tuple[Dict, float, str]] = []
    remaining = list(scored_songs)
    artist_counts: Dict[str, int] = {}
    genre_counts: Dict[str, int] = {}

    while remaining and len(selected) < k:
        best_candidate: Optional[Tuple[Dict, float, str]] = None
        best_adjusted_score: Optional[float] = None
        best_explanation: str = ""

        for song, base_score, explanation in remaining:
            artist = str(song.get("artist", "")).strip().lower()
            genre = str(song.get("genre", "")).strip().lower()
            artist_penalty = artist_penalty_weight * artist_counts.get(artist, 0)
            genre_penalty = genre_penalty_weight * genre_counts.get(genre, 0)
            adjusted_score = max(0.0, base_score - artist_penalty - genre_penalty)

            reason_parts = [explanation] if explanation else []
            if artist_penalty > 0:
                reason_parts.append(f"repeated artist (-{artist_penalty:.3f})")
            if genre_penalty > 0:
                reason_parts.append(f"repeated genre (-{genre_penalty:.3f})")
            candidate_explanation = "; ".join(part for part in reason_parts if part)

            if best_adjusted_score is None or adjusted_score > best_adjusted_score:
                best_candidate = (song, adjusted_score, candidate_explanation)
                best_adjusted_score = adjusted_score
                best_explanation = candidate_explanation

        if best_candidate is None:
            break

        song, adjusted_score, _ = best_candidate
        selected.append((song, adjusted_score, best_explanation))

        artist = str(song.get("artist", "")).strip().lower()
        genre = str(song.get("genre", "")).strip().lower()
        artist_counts[artist] = artist_counts.get(artist, 0) + 1
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        remaining = [item for item in remaining if int(item[0].get("id", -1)) != int(song.get("id", -1))]

    return selected

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Scores, sorts, and returns the top-k song recommendations."""
    if k <= 0:
        return []

    scored_songs = sorted(
        (
            (song, score, "; ".join(reasons))
            for song in songs
            for score, reasons in [score_song(user_prefs, song)]
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    return _apply_diversity_rerank(user_prefs, scored_songs, k)
