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
)

# --- Scoring weights (the "Algorithm Recipe"; max total = 4.9) ---
GENRE_WEIGHT = 1.5
MOOD_WEIGHT = 1.0
PARTIAL_CREDIT = 0.5  # also-OK genre/mood earns half the exact-match points
NUMERIC_WEIGHTS = {
    "energy": 1.0,
    "acousticness": 0.6,
    "valence": 0.4,
    "instrumentalness": 0.2,
    "tempo_bpm": 0.2,
}
TEMPO_RANGE = 92.0  # BPM gap that drops tempo closeness to 0

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

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, best first (same logic as recommend_songs)."""
        by_id = {song.id: song for song in self.songs}
        ranked = recommend_songs(_profile_to_prefs(user), [asdict(s) for s in self.songs], k)
        return [by_id[song["id"]] for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable 'score: reasons' string explaining how this song scored for the user."""
        score, reasons = score_song(_profile_to_prefs(user), asdict(song))
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
    }

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs.csv into a list of dicts, converting numeric columns to int/float."""
    print(f"Loading songs from {csv_path}...")
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for col in FLOAT_COLUMNS:
                if col in row:
                    row[col] = float(row[col])
            row["id"] = int(row["id"])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against user prefs; return (total points, list of human-readable reasons)."""
    # Recipe (README "Algorithm Recipe"): genre exact +1.5 / also-OK +0.75,
    # mood exact +1.0 / also-OK +0.5, numeric closeness = weight * (1 - gap),
    # tempo gap normalized by 92 BPM. A missing target is skipped, not penalized.
    score = 0.0
    reasons: List[str] = []

    # --- Categorical bonuses ---
    for feature, weight in (("genre", GENRE_WEIGHT), ("mood", MOOD_WEIGHT)):
        value = song[feature]
        if user_prefs.get(feature) == value:
            score += weight
            reasons.append(f"{feature} match: {value} (+{weight:.2f})")
        elif value in user_prefs.get(f"also_ok_{feature}s", []):
            partial = weight * PARTIAL_CREDIT
            score += partial
            reasons.append(f"{feature} close enough: {value} (+{partial:.2f})")

    # --- Numeric closeness ---
    targets = dict(user_prefs)
    # likes_acoustic is only a fallback when no explicit acousticness target is given.
    if targets.get("acousticness") is None and "likes_acoustic" in targets:
        targets["acousticness"] = 0.8 if targets["likes_acoustic"] else 0.2

    for feature, weight in NUMERIC_WEIGHTS.items():
        target = targets.get(feature)
        if target is None:
            continue  # no preference -> skip, don't penalize
        gap = abs(song[feature] - target)
        if feature == "tempo_bpm":
            closeness = max(0.0, 1 - gap / TEMPO_RANGE)
        else:
            if feature == "energy" and gap <= targets.get("energy_tolerance", 0.0):
                gap = 0.0
            closeness = max(0.0, 1 - gap)
        points = weight * closeness
        score += points
        reasons.append(f"{feature} {song[feature]:g} vs target {target:g} (+{points:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Judge every song with score_song and return the top k as (song, score, explanation), best first."""
    # Dealbreaker filter happens before judging, so excluded songs never compete.
    max_energy = user_prefs.get("max_energy")
    candidates = [s for s in songs if max_energy is None or s["energy"] <= max_energy]

    # Judge every candidate: (song, score, reasons) for each one.
    scored = [(song, *score_song(user_prefs, song)) for song in candidates]

    # sorted() returns a NEW list and leaves `songs` untouched; ties keep CSV order.
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    return [(song, score, "; ".join(reasons)) for song, score, reasons in ranked[:k]]
