"""
Command line runner for the Music Recommender Simulation.

Usage (from the project root):
    python -m src.main              # default "pop/happy" profile
    python -m src.main lofi         # any profile name from PROFILES
"""

import sys

from src.recommender import load_songs, recommend_songs

PROFILES = {
    # Starter default profile: only genre, mood and energy are specified,
    # so every other numeric feature is skipped (no preference).
    "pop/happy": {"genre": "pop", "mood": "happy", "energy": 0.8},
    # Primary profile from the README: late-night study lofi listener.
    "lofi": {
        "genre": "lofi", "also_ok_genres": ["ambient", "jazz"],
        "mood": "chill", "also_ok_moods": ["focused", "relaxed"],
        "energy": 0.38, "acousticness": 0.80, "valence": 0.58,
        "instrumentalness": 0.85, "tempo_bpm": 76,
    },
    "rock": {
        "genre": "rock", "also_ok_genres": ["metal"],
        "mood": "intense", "also_ok_moods": ["angry"],
        "energy": 0.92, "acousticness": 0.08, "valence": 0.45,
        "instrumentalness": 0.05, "tempo_bpm": 150,
    },
    "pop/chill": {
        "genre": "pop", "also_ok_genres": ["indie pop"],
        "mood": "chill", "also_ok_moods": ["relaxed"],
        "energy": 0.40, "acousticness": 0.70, "valence": 0.65,
        "instrumentalness": 0.10, "tempo_bpm": 85,
    },
}

WIDTH = 64


def describe(prefs: dict) -> str:
    """One-line summary of the profile's stated preferences."""
    skip = {"also_ok_genres", "also_ok_moods"}
    return ", ".join(f"{k}={v}" for k, v in prefs.items() if k not in skip)


def print_recommendations(name: str, prefs: dict, recommendations: list) -> None:
    """Print a ranked, readable block: title, artist, genre/mood, score and each reason."""
    print("=" * WIDTH)
    print(f"Profile: {name}")
    print(f"  {describe(prefs)}")
    print("=" * WIDTH)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n#{rank}  {song['title']} — {song['artist']}")
        print(f"    {song['genre']} / {song['mood']}    Score: {score:.2f}")
        for reason in explanation.split("; "):
            print(f"      • {reason}")
    print("\n" + "=" * WIDTH)


def main() -> None:
    """Load the catalog, pick a profile from argv (default pop/happy) and print its top 5."""
    name = sys.argv[1] if len(sys.argv) > 1 else "pop/happy"
    if name not in PROFILES:
        sys.exit(f"Unknown profile '{name}'. Choose from: {', '.join(PROFILES)}")

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    prefs = PROFILES[name]
    print_recommendations(name, prefs, recommend_songs(prefs, songs, k=5))


if __name__ == "__main__":
    main()
