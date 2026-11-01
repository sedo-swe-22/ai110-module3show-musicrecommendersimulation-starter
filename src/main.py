"""
Command line runner for the Music Recommender Simulation.

Usage (from the project root):
    python -m src.main                     # default "pop/happy" profile
    python -m src.main chill-lofi          # any profile name below
    python -m src.main core                # the three core profiles
    python -m src.main adversarial         # all edge-case profiles
    python -m src.main all                 # everything
"""

import sys

from src.recommender import load_songs, recommend_songs

# Starter default: only genre, mood and energy are given, so every other
# numeric feature is skipped (no preference).
DEFAULT = {"pop/happy": {"genre": "pop", "mood": "happy", "energy": 0.8}}

# Three distinct, internally consistent listeners.
CORE = {
    "high-energy-pop": {
        "genre": "pop", "also_ok_genres": ["indie pop"],
        "mood": "happy", "also_ok_moods": ["euphoric"],
        "energy": 0.88, "acousticness": 0.10, "valence": 0.85,
        "instrumentalness": 0.05, "tempo_bpm": 125,
    },
    "chill-lofi": {
        "genre": "lofi", "also_ok_genres": ["ambient", "jazz"],
        "mood": "chill", "also_ok_moods": ["focused", "relaxed"],
        "energy": 0.38, "acousticness": 0.80, "valence": 0.58,
        "instrumentalness": 0.85, "tempo_bpm": 76,
    },
    "deep-intense-rock": {
        "genre": "rock", "also_ok_genres": ["metal"],
        "mood": "intense", "also_ok_moods": ["angry"],
        "energy": 0.92, "acousticness": 0.08, "valence": 0.45,
        "instrumentalness": 0.05, "tempo_bpm": 150,
    },
}

# Edge cases designed to trick the scoring logic or expose odd behavior.
ADVERSARIAL = {
    # Conflict: high energy but a sad mood. No song is labeled "sad"
    # (the closest is "melancholy"), so the mood bonus can never fire.
    "sad-but-energetic": {"mood": "sad", "energy": 0.9, "valence": 0.1},
    # Conflict: the genre's typical sound contradicts the requested mood.
    "pop-genre-chill-mood": {
        "genre": "pop", "also_ok_genres": ["indie pop"],
        "mood": "chill", "also_ok_moods": ["relaxed"],
        "energy": 0.40, "acousticness": 0.70, "valence": 0.65,
        "instrumentalness": 0.10, "tempo_bpm": 85,
    },
    # Conflict: a calm genre with an intense mood and near-max energy.
    # Does the genre bonus beat every numeric signal?
    "lofi-but-intense": {"genre": "lofi", "mood": "intense", "energy": 0.95},
    # Same as pop/happy but capitalized. Is matching case-sensitive?
    "capitalized-labels": {"genre": "Pop", "mood": "Happy", "energy": 0.8},
    # Targets outside the 0-1 / real BPM range.
    "impossible-targets": {"energy": 1.5, "acousticness": -0.5, "tempo_bpm": 250},
    # No preferences at all: every song scores 0.
    "empty-profile": {},
    # Dealbreaker that removes almost the whole catalog.
    "strict-dealbreaker": {"genre": "rock", "energy": 0.9, "max_energy": 0.3},
}

PROFILES = {**DEFAULT, **CORE, **ADVERSARIAL}
GROUPS = {"core": CORE, "adversarial": ADVERSARIAL, "all": PROFILES}

WIDTH = 64


def describe(prefs: dict) -> str:
    """One-line summary of the profile's stated preferences."""
    skip = {"also_ok_genres", "also_ok_moods"}
    return ", ".join(f"{k}={v}" for k, v in prefs.items() if k not in skip) or "(no preferences)"


def print_recommendations(name: str, prefs: dict, recommendations: list) -> None:
    """Print a ranked, readable block: title, artist, genre/mood, score and each reason."""
    print("=" * WIDTH)
    print(f"Profile: {name}")
    print(f"  {describe(prefs)}")
    print("=" * WIDTH)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n#{rank}  {song['title']} — {song['artist']}")
        print(f"    {song['genre']} / {song['mood']}    Score: {score:.2f}")
        for reason in explanation.split("; ") if explanation else ["(no matching preferences)"]:
            print(f"      • {reason}")
    print("\n" + "=" * WIDTH)


def main() -> None:
    """Load the catalog, pick a profile or group from argv (default pop/happy) and print each top 5."""
    name = sys.argv[1] if len(sys.argv) > 1 else "pop/happy"
    selected = GROUPS.get(name) or ({name: PROFILES[name]} if name in PROFILES else None)
    if selected is None:
        choices = ", ".join([*GROUPS, *PROFILES])
        sys.exit(f"Unknown profile '{name}'. Choose from: {choices}")

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    for profile_name, prefs in selected.items():
        recommendations = recommend_songs(prefs, songs, k=5)
        print_recommendations(profile_name, prefs, recommendations)
        if len(recommendations) < 5:
            print(f"(only {len(recommendations)} songs passed the filters)\n")


if __name__ == "__main__":
    main()
