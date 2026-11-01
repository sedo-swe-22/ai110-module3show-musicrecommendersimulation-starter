import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import asdict, dataclass, field

# CSV columns that hold numbers; everything else (title, genre, ...) stays a string.
FLOAT_COLUMNS = (
    "energy",
    "tempo_bpm",
    "valence",
    "danceability",
    "acousticness",
    "instrumentalness",
    "popularity",
    "speechiness",
    "liveness",
)
INT_COLUMNS = ("id", "release_decade")
LIST_COLUMNS = ("mood_tags",)  # stored as "tag1;tag2;tag3" in the CSV

# --- Scoring weights (the "Algorithm Recipe"; max total = 4.9 for the core features) ---
GENRE_WEIGHT = 1.5
MOOD_WEIGHT = 1.0
PARTIAL_CREDIT = 0.5  # also-OK genre/mood earns half the exact-match points
NUMERIC_WEIGHTS = {
    "energy": 1.0,
    "acousticness": 0.6,
    "valence": 0.4,
    "instrumentalness": 0.2,
    "tempo_bpm": 0.2,
    # Advanced features (Challenge 1). Like every numeric feature, each one is
    # skipped unless the user gives a target, so existing profiles are unaffected.
    "popularity": 0.3,
    "release_decade": 0.4,
    "speechiness": 0.2,
    "liveness": 0.1,
}
TAG_WEIGHT = 0.3       # points per matching mood tag ...
MAX_TAG_MATCHES = 3    # ... counting at most 3 tags (max 0.9)

# A gap this large drops closeness to 0. Features not listed use 1.0 (0-1 scale).
FEATURE_SCALES = {
    "tempo_bpm": 92.0,       # BPM
    "popularity": 100.0,     # 0-100
    "release_decade": 40.0,  # years: 4 decades away = 0 points
}
TEMPO_RANGE = FEATURE_SCALES["tempo_bpm"]

# --- Diversity penalty (Challenge 3) ---
ARTIST_PENALTY = 0.6  # per song by the same artist already in the list
GENRE_PENALTY = 0.4   # per song of the same genre already in the list


@dataclass(frozen=True)
class ScoringMode:
    """A ranking strategy: one set of weights that score_song can plug in (Strategy pattern)."""
    name: str
    description: str
    genre_weight: float
    mood_weight: float
    numeric_weights: Dict[str, float]
    tag_weight: float = TAG_WEIGHT

    def max_core_score(self) -> float:
        """Best possible score from genre + mood + the five core numeric features."""
        core = ("energy", "acousticness", "valence", "instrumentalness", "tempo_bpm")
        return self.genre_weight + self.mood_weight + sum(self.numeric_weights[f] for f in core)


def _with(**changes: float) -> Dict[str, float]:
    """Copy of the default numeric weights with some values overridden."""
    return {**NUMERIC_WEIGHTS, **changes}


MODES: Dict[str, ScoringMode] = {
    mode.name: mode
    for mode in (
        ScoringMode("balanced", "Default recipe: genre 1.5, mood 1.0, energy 1.0.",
                    GENRE_WEIGHT, MOOD_WEIGHT, dict(NUMERIC_WEIGHTS)),
        ScoringMode("genre-first", "Genre outweighs mood + all core numbers combined (3.5 > 3.4).",
                    3.5, MOOD_WEIGHT, dict(NUMERIC_WEIGHTS)),
        ScoringMode("mood-first", "Mood is king; genre is a light tiebreaker.",
                    0.75, 2.5, dict(NUMERIC_WEIGHTS)),
        ScoringMode("energy-focused", "Mostly how the song feels: energy and tempo lead, labels matter little.",
                    0.5, 0.5, _with(energy=2.5, acousticness=0.3, tempo_bpm=0.4)),
    )
}
DEFAULT_MODE = MODES["balanced"]


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
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
    instrumentalness: float = 0.0
    # Advanced attributes (Challenge 1); defaults keep older code and tests working.
    popularity: float = 50.0
    release_decade: int = 2020
    mood_tags: List[str] = field(default_factory=list)
    speechiness: float = 0.0
    liveness: float = 0.0

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Optional numeric targets; None means "no preference" and the scorer
    # skips the feature (no renormalization; the max total just shrinks).
    target_acousticness: Optional[float] = None
    target_valence: Optional[float] = None
    target_tempo_bpm: Optional[float] = None
    target_danceability: Optional[float] = None
    target_instrumentalness: Optional[float] = None
    # Near-misses that still earn (partial) mood/genre credit.
    also_ok_moods: List[str] = field(default_factory=list)
    also_ok_genres: List[str] = field(default_factory=list)
    # A song within +/- this of target_energy is treated as a full match.
    energy_tolerance: float = 0.0
    # Dealbreaker: songs with energy above this are excluded entirely.
    max_energy: Optional[float] = None
    # Advanced preferences (Challenge 1).
    target_popularity: Optional[float] = None
    target_decade: Optional[int] = None
    target_speechiness: Optional[float] = None
    target_liveness: Optional[float] = None
    mood_tags: List[str] = field(default_factory=list)

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], mode: ScoringMode = DEFAULT_MODE, diversity: bool = False):
        self.songs = songs
        self.mode = mode
        self.diversity = diversity

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, best first (same logic as recommend_songs)."""
        by_id = {song.id: song for song in self.songs}
        ranked = recommend_songs(_profile_to_prefs(user), [asdict(s) for s in self.songs], k,
                                 mode=self.mode, diversity=self.diversity)
        return [by_id[song["id"]] for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable 'score: reasons' string explaining how this song scored for the user."""
        score, reasons = score_song(_profile_to_prefs(user), asdict(song), self.mode)
        return f"Score {score:.2f}: " + "; ".join(reasons)


def _profile_to_prefs(user: UserProfile) -> Dict:
    """Translate a UserProfile into the user_prefs dict that score_song expects."""
    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "also_ok_genres": user.also_ok_genres,
        "also_ok_moods": user.also_ok_moods,
        "energy": user.target_energy,
        "acousticness": user.target_acousticness,
        "likes_acoustic": user.likes_acoustic,
        "valence": user.target_valence,
        "instrumentalness": user.target_instrumentalness,
        "tempo_bpm": user.target_tempo_bpm,
        "energy_tolerance": user.energy_tolerance,
        "max_energy": user.max_energy,
        "popularity": user.target_popularity,
        "release_decade": user.target_decade,
        "speechiness": user.target_speechiness,
        "liveness": user.target_liveness,
        "mood_tags": user.mood_tags,
    }

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs.csv into a list of dicts, converting numeric columns to int/float and tag lists to lists."""
    print(f"Loading songs from {csv_path}...")
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for col in FLOAT_COLUMNS:
                if col in row:
                    row[col] = float(row[col])
            for col in INT_COLUMNS:
                if col in row:
                    row[col] = int(row[col])
            for col in LIST_COLUMNS:
                if col in row:
                    row[col] = [tag.strip() for tag in row[col].split(";") if tag.strip()]
            songs.append(row)
    return songs

def _format_value(feature: str, value: float) -> str:
    """Human-friendly value for a reason string (decades as '1990s')."""
    return f"{int(value)}s" if feature == "release_decade" else f"{value:g}"

def score_song(user_prefs: Dict, song: Dict, mode: ScoringMode = DEFAULT_MODE) -> Tuple[float, List[str]]:
    """Score one song against user prefs; return (total points, list of human-readable reasons)."""
    # Recipe (README "Algorithm Recipe"): genre exact +1.5 / also-OK +0.75,
    # mood exact +1.0 / also-OK +0.5, numeric closeness = weight * (1 - gap / scale),
    # mood tags +0.3 each (max 3). A missing target is skipped, not penalized.
    # `mode` swaps in a different set of weights (see MODES).
    score = 0.0
    reasons: List[str] = []

    # --- Categorical bonuses ---
    for feature, weight in (("genre", mode.genre_weight), ("mood", mode.mood_weight)):
        value = song[feature]
        if user_prefs.get(feature) == value:
            score += weight
            reasons.append(f"{feature} match: {value} (+{weight:.2f})")
        elif value in user_prefs.get(f"also_ok_{feature}s", []):
            partial = weight * PARTIAL_CREDIT
            score += partial
            reasons.append(f"{feature} close enough: {value} (+{partial:.2f})")

    # --- Mood tags (Challenge 1): credit for each shared tag, case-insensitive ---
    wanted_tags = {t.lower() for t in user_prefs.get("mood_tags") or []}
    if wanted_tags:
        shared = [t for t in song.get("mood_tags", []) if t.lower() in wanted_tags][:MAX_TAG_MATCHES]
        if shared:
            points = mode.tag_weight * len(shared)
            score += points
            reasons.append(f"mood tags: {', '.join(shared)} (+{points:.2f})")

    # --- Numeric closeness ---
    targets = dict(user_prefs)
    # likes_acoustic is only a fallback when no explicit acousticness target is given.
    if targets.get("acousticness") is None and "likes_acoustic" in targets:
        targets["acousticness"] = 0.8 if targets["likes_acoustic"] else 0.2

    for feature, weight in mode.numeric_weights.items():
        target = targets.get(feature)
        if target is None or feature not in song:
            continue  # no preference (or no data) -> skip, don't penalize
        gap = abs(song[feature] - target)
        if feature == "energy" and gap <= targets.get("energy_tolerance", 0.0):
            gap = 0.0
        closeness = max(0.0, 1 - gap / FEATURE_SCALES.get(feature, 1.0))
        points = weight * closeness
        score += points
        reasons.append(
            f"{feature} {_format_value(feature, song[feature])} vs target "
            f"{_format_value(feature, target)} (+{points:.2f})"
        )

    return score, reasons

def diversity_penalty(song: Dict, already_picked: List[Dict]) -> Tuple[float, List[str]]:
    """Points to subtract because the list already has songs by this artist or in this genre."""
    same_artist = sum(1 for s in already_picked if s["artist"] == song["artist"])
    same_genre = sum(1 for s in already_picked if s["genre"] == song["genre"])
    penalty, notes = 0.0, []
    if same_artist:
        penalty += ARTIST_PENALTY * same_artist
        notes.append(f"diversity: {same_artist} song(s) by {song['artist']} already picked "
                     f"(-{ARTIST_PENALTY * same_artist:.2f})")
    if same_genre:
        penalty += GENRE_PENALTY * same_genre
        notes.append(f"diversity: {same_genre} {song['genre']} song(s) already picked "
                     f"(-{GENRE_PENALTY * same_genre:.2f})")
    return penalty, notes

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: ScoringMode = DEFAULT_MODE,
    diversity: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """Judge every song with score_song and return the top k as (song, score, explanation), best first."""
    # Dealbreaker filter happens before judging, so excluded songs never compete.
    max_energy = user_prefs.get("max_energy")
    candidates = [s for s in songs if max_energy is None or s["energy"] <= max_energy]

    # Judge every candidate: (song, score, reasons) for each one.
    scored = [(song, *score_song(user_prefs, song, mode)) for song in candidates]

    # sorted() returns a NEW list and leaves `songs` untouched; ties keep CSV order.
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    if diversity:
        ranked = _rerank_for_diversity(ranked, k)

    return [(song, score, "; ".join(reasons)) for song, score, reasons in ranked[:k]]

def _rerank_for_diversity(ranked: List[Tuple[Dict, float, List[str]]], k: int) -> List[Tuple[Dict, float, List[str]]]:
    """Greedy re-rank: repeatedly pick the best song after penalizing repeats of artists/genres already picked."""
    pool = list(ranked)
    picked: List[Tuple[Dict, float, List[str]]] = []
    while pool and len(picked) < k:
        picked_songs = [song for song, _, _ in picked]
        best_i, best = None, None
        for i, (song, score, reasons) in enumerate(pool):
            penalty, notes = diversity_penalty(song, picked_songs)
            adjusted = (song, score - penalty, reasons + notes)
            if best is None or adjusted[1] > best[1]:  # strict '>' keeps the original order on ties
                best_i, best = i, adjusted
        picked.append(best)
        pool.pop(best_i)
    return picked
