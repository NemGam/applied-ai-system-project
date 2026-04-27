"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.
"""

from textwrap import wrap

from backend.src.recommender import load_songs, recommend_songs


LINE_WIDTH = 92


def _box_line(text: str = "", fill: str = " ") -> str:
    return f"| {text.ljust(LINE_WIDTH - 4, fill)} |"


def _box_rule(char: str = "-") -> str:
    return "+" + (char * (LINE_WIDTH - 2)) + "+"


def _print_recommendation(idx: int, song: dict, score: float, explanation: str) -> None:
    title = song.get("title", "Unknown Title")
    artist = song.get("artist", "Unknown Artist")
    genre = song.get("genre", "unknown")
    mood = song.get("mood", "unknown")
    reasons = [part.strip() for part in explanation.split(";") if part.strip()]

    print(_box_rule("-"))
    print(_box_line(f"{idx}. {title} | {artist}"))
    print(_box_line(f"Score: {score:.3f}"))
    print(_box_line(f"Tags : genre={genre}, mood={mood}"))
    print(_box_line("Reasons:"))
    for reason in reasons:
        wrapped_reason = wrap(reason, width=LINE_WIDTH - 8) or [reason]
        print(_box_line(f"- {wrapped_reason[0]}"))
        for continuation in wrapped_reason[1:]:
            print(_box_line(f"  {continuation}"))
    print(_box_rule("-"))


def main() -> None:
    songs = load_songs("backend/data/songs.csv")
    print(f"\nLoaded {len(songs)} songs")

    user_profiles = {
        "Late Night Coder": {
            "favorite_genres": ["lofi", "ambient"],
            "favorite_moods": ["focused", "chill"],
            "favorite_contexts": ["study", "deep_work"],
            "preferred_mood_tags": ["immersive", "steady", "clear-headed"],
            "target_energy": 0.38,
            "target_tempo_bpm": 78,
            "target_acousticness": 0.82,
            "target_instrumental_focus": 0.92,
            "target_vocal_presence": 0.10,
        },
        "Night Drive Mood": {
            "favorite_genres": ["synthwave", "electronic", "rock"],
            "favorite_moods": ["moody"],
            "favorite_decades": ["2010s", "2020s"],
            "favorite_contexts": ["night_drive"],
            "preferred_mood_tags": ["cinematic", "brooding", "neon"],
            "target_energy": 0.76,
            "target_valence": 0.46,
            "target_danceability": 0.72,
            "target_tempo_bpm": 112,
        },
        "Weekend Pop Boost": {
            "favorite_genres": ["pop", "indie pop"],
            "favorite_moods": ["happy", "energetic"],
            "favorite_contexts": ["party", "commute", "walk"],
            "preferred_mood_tags": ["uplifting", "bright", "carefree"],
            "target_energy": 0.82,
            "target_valence": 0.84,
            "target_danceability": 0.83,
            "target_popularity_100": 84,
            "target_replay_value": 0.85,
        },
        "Quiet Morning Reader": {
            "favorite_genres": ["jazz", "ambient", "lofi"],
            "favorite_moods": ["relaxed", "chill"],
            "favorite_contexts": ["reading", "cafe", "sleep"],
            "preferred_mood_tags": ["gentle", "cozy", "warm"],
            "target_energy": 0.34,
            "target_acousticness": 0.90,
            "target_tempo_bpm": 72,
            "target_instrumental_focus": 0.88,
        },
        "Genre First Explorer": {
            "favorite_genres": ["hip hop", "rock"],
            "favorite_moods": ["focused", "intense"],
            "target_energy": 0.72,
            "target_vocal_presence": 0.82,
        },
    }

    for profile_name, user_prefs in user_profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print()
        print(_box_rule("="))
        print(_box_line(f"Top 5 Recommendations | {profile_name}"))
        print(_box_rule("="))

        for idx, (song, score, explanation) in enumerate(recommendations, start=1):
            _print_recommendation(idx, song, score, explanation)


if __name__ == "__main__":
    main()
