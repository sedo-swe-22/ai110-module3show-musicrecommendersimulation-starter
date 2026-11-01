"""Tests for the optional extensions: advanced features, scoring modes, diversity penalty."""

import pytest

from src.recommender import (
    ARTIST_PENALTY,
    GENRE_PENALTY,
    MODES,
    Recommender,
    Song,
    UserProfile,
    load_songs,
    recommend_songs,
    score_song,
)

CSV = "data/songs.csv"


@pytest.fixture(scope="module")
def songs():
    return load_songs(CSV)


def by_title(songs, title):
    return next(s for s in songs if s["title"] == title)


# --- Challenge 1: advanced features -------------------------------------------------

def test_new_columns_are_parsed_to_usable_types(songs):
    song = by_title(songs, "Nocturne in Rain")
    assert isinstance(song["popularity"], float)
    assert isinstance(song["release_decade"], int)
    assert song["mood_tags"] == ["sad", "rainy", "bittersweet"]


def test_advanced_features_are_skipped_when_not_requested(songs):
    score, reasons = score_song({"genre": "lofi", "energy": 0.4}, by_title(songs, "Focus Flow"))
    assert not any(word in r for r in reasons for word in ("popularity", "decade", "tags", "speech", "live"))
    assert score == pytest.approx(1.5 + 1.0)


def test_mood_tags_score_per_match_and_ignore_case(songs):
    score, reasons = score_song({"mood_tags": ["SAD", "Dark"]}, by_title(songs, "Iron Requiem"))
    assert score == pytest.approx(0.6)
    assert reasons == ["mood tags: dark, sad (+0.60)"]


def test_decade_and_popularity_closeness(songs):
    night_drive = by_title(songs, "Night Drive Loop")  # 1980, popularity 64
    score, _ = score_song({"release_decade": 2000, "popularity": 64}, night_drive)
    # decade: 0.4 * (1 - 20/40) = 0.2 ; popularity: 0.3 * (1 - 0/100) = 0.3
    assert score == pytest.approx(0.5)


def test_tags_let_a_sad_request_find_the_sad_loud_song(songs):
    prefs = {"energy": 0.9, "valence": 0.1, "mood_tags": ["sad", "dark"]}
    top = recommend_songs(prefs, songs, k=1)[0][0]
    assert top["title"] == "Iron Requiem"


# --- Challenge 2: scoring modes (Strategy pattern) ----------------------------------

def test_balanced_mode_is_the_default_recipe(songs):
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    song = by_title(songs, "Sunrise City")
    assert score_song(prefs, song) == score_song(prefs, song, MODES["balanced"])


def test_genre_first_puts_genre_matches_on_top(songs):
    prefs = {"genre": "pop", "mood": "chill", "energy": 0.4, "acousticness": 0.7}
    top2 = [s["genre"] for s, _, _ in recommend_songs(prefs, songs, k=2, mode=MODES["genre-first"])]
    assert top2 == ["pop", "pop"]


def test_mood_first_puts_mood_matches_on_top(songs):
    prefs = {"genre": "pop", "mood": "chill", "energy": 0.4, "acousticness": 0.7}
    top3 = [s["mood"] for s, _, _ in recommend_songs(prefs, songs, k=3, mode=MODES["mood-first"])]
    assert top3 == ["chill", "chill", "chill"]


def test_genre_first_genre_weight_beats_every_core_non_genre_point():
    mode = MODES["genre-first"]
    assert mode.genre_weight > mode.max_core_score() - mode.genre_weight


# --- Challenge 3: diversity penalty --------------------------------------------------

def test_diversity_penalizes_repeated_artist_and_genre(songs):
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.38, "acousticness": 0.8,
             "valence": 0.58, "instrumentalness": 0.85, "tempo_bpm": 76}
    plain = recommend_songs(prefs, songs, k=5)
    diverse = recommend_songs(prefs, songs, k=5, diversity=True)
    plain_score = {s["title"]: sc for s, sc, _ in plain}
    diverse_rank = [s["title"] for s, _, _ in diverse]
    diverse_score = {s["title"]: sc for s, sc, _ in diverse}

    # Focus Flow is the 2nd LoRoom song and the 3rd lofi song once it is reached.
    assert diverse_rank.index("Focus Flow") > [s["title"] for s, _, _ in plain].index("Focus Flow")
    assert diverse_score["Focus Flow"] == pytest.approx(
        plain_score["Focus Flow"] - ARTIST_PENALTY - 2 * GENRE_PENALTY
    )


def test_diversity_off_by_default_and_never_changes_the_top_pick(songs):
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    plain = recommend_songs(prefs, songs)
    assert "diversity" not in " ".join(e for _, _, e in plain)
    assert recommend_songs(prefs, songs, diversity=True)[0][0] == plain[0][0]


def test_diversity_replaces_second_song_by_same_artist(songs):
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    artists = [s["artist"] for s, _, _ in recommend_songs(prefs, songs, diversity=True)]
    assert len(artists) == len(set(artists))


# --- OOP path stays in sync ----------------------------------------------------------

def test_recommender_class_supports_modes_and_diversity(songs):
    catalog = [Song(**s) for s in songs]
    user = UserProfile("pop", "chill", 0.4, True)
    rec = Recommender(catalog, mode=MODES["mood-first"], diversity=True)
    top = rec.recommend(user, k=3)
    assert [s.mood for s in top] == ["chill", "chill", "chill"]
    assert "Score" in rec.explain_recommendation(user, top[0])
