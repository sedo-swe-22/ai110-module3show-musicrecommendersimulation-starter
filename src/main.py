"""
Command line runner for the Music Recommender Simulation.

Usage (from the project root):
    python -m src.main                         # default "pop/happy" profile
    python -m src.main chill-lofi              # any profile name below
    python -m src.main core                    # the three core profiles
    python -m src.main adversarial             # all edge-case profiles
    python -m src.main extended                # profiles using the advanced features
    python -m src.main all                     # default + core + adversarial

Options (combine freely):
    --mode {balanced,genre-first,mood-first,energy-focused}   ranking strategy
    --diverse                                                 penalize repeated artists/genres
    --table                                                   compact ASCII table output
"""

import argparse
import sys
import textwrap

from src.recommender import DEFAULT_MODE, MODES, load_songs, recommend_songs

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

# Profiles that use the advanced features (Challenge 1).
EXTENDED = {
    # The adversarial "sad-but-energetic" listener again, now able to say "sad"
    # through mood tags instead of a mood label the catalog doesn't have.
    "sad-energetic-tagged": {"mood": "sad", "energy": 0.9, "valence": 0.1, "mood_tags": ["sad", "dark"]},
    # A crate-digger: 80s, not too mainstream, nostalgic late-night feel.
    "nostalgic-80s-deep-cuts": {
        "energy": 0.7, "release_decade": 1980, "popularity": 40,
        "mood_tags": ["nostalgic", "mysterious", "late-night"],
    },
    # Wants current chart hits with lots of lyrics and a live, crowd feel.
    "wordy-live-hits": {
        "energy": 0.8, "popularity": 85, "release_decade": 2020,
        "speechiness": 0.3, "liveness": 0.35,
    },
}

PROFILES = {**DEFAULT, **CORE, **ADVERSARIAL, **EXTENDED}
GROUPS = {
    "core": CORE,
    "adversarial": ADVERSARIAL,
    "extended": EXTENDED,
    "all": {**DEFAULT, **CORE, **ADVERSARIAL},
}

WIDTH = 64


def describe(prefs: dict) -> str:
    """One-line summary of the profile's stated preferences."""
    skip = {"also_ok_genres", "also_ok_moods"}
    return ", ".join(f"{k}={v}" for k, v in prefs.items() if k not in skip) or "(no preferences)"


def header_lines(name: str, prefs: dict, settings: str) -> list:
    """Profile name, its preferences, and the non-default settings (if any)."""
    lines = [f"Profile: {name}", f"  {describe(prefs)}"]
    if settings:
        lines.append(f"  {settings}")
    return lines


def print_recommendations(name: str, prefs: dict, recommendations: list, settings: str = "") -> None:
    """Print a ranked, readable block: title, artist, genre/mood, score and each reason."""
    print("=" * WIDTH)
    for line in header_lines(name, prefs, settings):
        print(line)
    print("=" * WIDTH)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n#{rank}  {song['title']} — {song['artist']}")
        print(f"    {song['genre']} / {song['mood']}    Score: {score:.2f}")
        for reason in explanation.split("; ") if explanation else ["(no matching preferences)"]:
            print(f"      • {reason}")
    print("\n" + "=" * WIDTH)


def reasons_of(explanation: str) -> list:
    """Split the explanation string back into individual reasons."""
    return explanation.split("; ") if explanation else ["(no matching preferences)"]


def print_table(name: str, prefs: dict, recommendations: list, settings: str = "") -> None:
    """Print the top results as an ASCII table whose last column lists every reason (Challenge 4)."""
    headers = ["#", "Song", "Genre / Mood", "Score", "Why (reasons)"]
    widths = [2, 22, 20, 5, 46]
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        why = []
        for reason in reasons_of(explanation):
            why += textwrap.wrap(reason, widths[4], subsequent_indent="  ")
        rows.append([
            [str(rank)],
            textwrap.wrap(f"{song['title']} — {song['artist']}", widths[1]),
            textwrap.wrap(f"{song['genre']} / {song['mood']}", widths[2]),
            [f"{score:.2f}"],
            why,
        ])

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def line(cells):
        return "| " + " | ".join(
            (c.rjust(w) if i in (0, 3) else c.ljust(w)) for i, (c, w) in enumerate(zip(cells, widths))
        ) + " |"

    for text in header_lines(name, prefs, settings):
        print(text)
    print(border)
    print(line(headers))
    print(border.replace("-", "="))
    for row in rows:
        for i in range(max(len(cell) for cell in row)):
            print(line([cell[i] if i < len(cell) else "" for cell in row]))
        print(border)
    if recommendations:
        top = recommendations[0]
        print(f"Top pick: {top[0]['title']} ({top[1]:.2f}). "
              f"Genres in list: {len({s['genre'] for s, _, _ in recommendations})}, "
              f"artists: {len({s['artist'] for s, _, _ in recommendations})}.")
    print()


def parse_args(argv=None) -> argparse.Namespace:
    """Read the profile name and options from the command line."""
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("profile", nargs="?", default="pop/happy",
                        help=f"profile or group: {', '.join([*GROUPS, *PROFILES])}")
    parser.add_argument("--mode", choices=list(MODES), default=DEFAULT_MODE.name,
                        help="ranking strategy (default: balanced)")
    parser.add_argument("--diverse", action="store_true",
                        help="penalize songs whose artist or genre is already in the list")
    parser.add_argument("--table", action="store_true", help="show results as an ASCII table")
    parser.add_argument("-k", type=int, default=5, help="number of recommendations (default: 5)")
    return parser.parse_args(argv)


def main() -> None:
    """Load the catalog, pick a profile or group (default pop/happy) and print each top k."""
    args = parse_args()
    name = args.profile
    selected = GROUPS.get(name) or ({name: PROFILES[name]} if name in PROFILES else None)
    if selected is None:
        choices = ", ".join([*GROUPS, *PROFILES])
        sys.exit(f"Unknown profile '{name}'. Choose from: {choices}")

    mode = MODES[args.mode]
    settings = ", ".join(
        part for part in (
            f"mode={mode.name} ({mode.description})" if mode is not DEFAULT_MODE else "",
            "diversity penalty ON" if args.diverse else "",
        ) if part
    )
    show = print_table if args.table else print_recommendations

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    for profile_name, prefs in selected.items():
        recommendations = recommend_songs(prefs, songs, k=args.k, mode=mode, diversity=args.diverse)
        show(profile_name, prefs, recommendations, settings)
        if len(recommendations) < args.k:
            print(f"(only {len(recommendations)} songs passed the filters)\n")


if __name__ == "__main__":
    main()
