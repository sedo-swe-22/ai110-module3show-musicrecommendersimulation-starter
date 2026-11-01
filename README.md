# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world platforms like Spotify and YouTube predict what you'll love next with a multi-stage pipeline: they generate candidates, rank them with a heavier model, then re-rank for diversity and freshness. They learn mostly from implicit behavior such as plays, skips, replays and playlist adds. They blend **collaborative filtering** (what similar users listened to) with **content-based filtering** (a song's own attributes, like tempo, energy and mood) so new songs with no listening history can still be recommended. This version is deliberately **content-based**. With only 18 songs and no user history, it relies on the song attributes in `data/songs.csv`: `genre` and `mood` act as match bonuses, and `energy`, `acousticness`, `valence`, `instrumentalness` and `tempo_bpm` add points for closeness. Numeric features are scored by how *close* a song is to the user's target value, not by whether the value is high or low. A separate ranking step then sorts the scored songs and returns the top results.

### Features

- **Each `Song` uses:** `genre`, `mood`, `energy`, `acousticness`, `valence`, `instrumentalness` and `tempo_bpm`. `danceability` is loaded but not scored, because it mostly repeats valence and energy in this catalog.
- **Each `UserProfile` stores:**
  - a favorite genre and mood
  - optional "also OK" genres and moods that earn partial credit
  - a target value for each numeric feature. A target set to `None` means "no preference", and that feature is skipped instead of scored as 0. The remaining weights are **not** renormalized, so the max total simply shrinks.
  - `likes_acoustic` (required by the starter tests): used only as a fallback when `target_acousticness` is `None`. It becomes a target of 0.8 if true, 0.2 if false.
  - `max_energy` (optional dealbreaker): songs above it are removed **before** scoring.
  - `energy_tolerance` (optional, default 0): an energy gap within the tolerance counts as a perfect match.
  - `target_danceability` exists but is ignored. Danceability has weight 0 in the recipe.

### Primary user profile (used for development)

A "late-night study" listener who wants calm, mostly instrumental lofi:

```python
UserProfile(
    favorite_genre="lofi",       also_ok_genres=["ambient", "jazz"],
    favorite_mood="chill",       also_ok_moods=["focused", "relaxed"],
    target_energy=0.38,          likes_acoustic=True,
    target_acousticness=0.80,    target_valence=0.58,
    target_instrumentalness=0.85, target_tempo_bpm=76,
)
```

The dict form used by `score_song` and `main.py` uses these keys: `genre`, `mood`, `also_ok_genres`, `also_ok_moods`, `energy`, `acousticness`, `valence`, `instrumentalness`, `tempo_bpm`.

**Expected top 5** (hand-computed with the recipe below): Library Rain 4.807, Midnight Coding 4.794, Focus Flow 4.349, Spacewalk Thoughts 3.895, Coffee Shop Stories 3.474. Two contrast profiles will be used to stress-test it:
- **Intense rock** (rock / intense, energy .92). Expected #1: Storm Runner.
- **Pop genre, chill mood**. This is the conflict case. Gym Hero must **not** be in the top 3.

### Algorithm Recipe (final)

`score_song` judges one song against the user's preferences and returns `(score, reasons)`:

| Component | Rule | Max points |
|---|---|---|
| Genre | exact match **+1.5**, also-OK genre **+0.75**, else 0 | 1.5 |
| Mood | exact match **+1.0**, also-OK mood **+0.5**, else 0 | 1.0 |
| Energy | `1.0 × (1 − \|song − target\|)` | 1.0 |
| Acousticness | `0.6 × (1 − \|song − target\|)` | 0.6 |
| Valence | `0.4 × (1 − \|song − target\|)` | 0.4 |
| Instrumentalness | `0.2 × (1 − \|song − target\|)` | 0.2 |
| Tempo | `0.2 × max(0, 1 − \|song − target\| / 92)` | 0.2 |
| **Total** | | **4.9** |

Each component that earns points adds a reason, such as `"mood match (+1.0)"` or `"energy close (+0.97)"`, so every recommendation can be explained.

**Why genre is 1.5 rather than 2.0:** 13 of the 15 genres appear only once, so a genre bonus usually lands on a single song. At 2.0, a "pop genre, chill mood" profile ranked *Gym Hero* (intense, energy .93) #2 purely because it is pop. Any genre weight between 1.0 and about 1.6 drops it below the genuinely chill songs. Within that range, metal (*Iron Requiem*) still outranks pop (*Gym Hero*) for a rock fan.

**Worked example** (*Library Rain* for a chill lofi profile, with targets energy .38, acousticness .80, valence .58, instrumentalness .85, tempo 76):

`1.5 + 1.0 + 1.0(1−.03) + .6(1−.06) + .4(1−.02) + .2(1−.05) + .2(1−4/92)`
`= 1.5 + 1.0 + .970 + .564 + .392 + .190 + .191 = 4.807`

### Ranking and data flow

`recommend_songs` scores every song, sorts by score from highest to lowest and returns the top `k` (default 5) as `(song, score, explanation)`:

```
INPUT                     PROCESS (loop)                         OUTPUT
songs.csv ─load_songs()─► for each song:                         sort by score, highest first
user_prefs ─────────────►   score_song(prefs, song)       ─────► take top k
                              genre + mood bonuses               return (song, score, explanation)
                              + numeric closeness points
                            collect (song, score, reasons)
```

When scores tie, songs keep their CSV order, because Python's sort is stable.

### Expected biases and weak spots

- **Genre can still over-rule mood.** Even at 1.5, a genre match is worth more than a mood match. The system can push a great song that matches the user's mood below a mediocre song in their genre, especially for broad genres like pop.
- **Energy is counted about three times.** In this catalog, energy, acousticness (r = −0.97) and tempo (r = 0.90) move together. Together they hold 1.8 of the 2.4 numeric points, so "how energetic is it?" dominates. "How happy is it?" (valence, 0.4) gets little say.
- **Exact string matching.** "indie pop" does not match "pop", and "laid-back" does not match "chill", unless the user lists them as also-OK. Songs with a near-synonym label get no credit.
- **Catalog skew.** Lofi (3 songs) and chill (3 songs) are the only well-represented categories. Users with those tastes get a full, varied top 5. Users who like folk, country or classical get one matching song and then filler.
- **No diversity control.** Nothing stops the top 5 from being several songs by the same artist or with the same sound (for example, both LoRoom tracks).
- **Taste is only what the user types in.** There is no listening history, lyrics or context, so the system cannot learn that a stated preference is wrong.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output of `python -m src.main` with the default **pop/happy** profile. This profile only states a genre, mood and energy, so the other numeric features are skipped and the max possible score is 3.5:

```text
$ python -m src.main
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: pop/happy
  genre=pop, mood=happy, energy=0.8
================================================================

#1  Sunrise City — Neon Echo
    pop / happy    Score: 3.48
      • genre match: pop (+1.50)
      • mood match: happy (+1.00)
      • energy 0.82 vs target 0.8 (+0.98)

#2  Gym Hero — Max Pulse
    pop / intense    Score: 2.37
      • genre match: pop (+1.50)
      • energy 0.93 vs target 0.8 (+0.87)

#3  Rooftop Lights — Indigo Parade
    indie pop / happy    Score: 1.96
      • mood match: happy (+1.00)
      • energy 0.76 vs target 0.8 (+0.96)

#4  Concrete Poetry — Verse Theory
    hip-hop / confident    Score: 0.98
      • energy 0.78 vs target 0.8 (+0.98)

#5  Night Drive Loop — Neon Echo
    synthwave / moody    Score: 0.95
      • energy 0.75 vs target 0.8 (+0.95)

================================================================
```

**Does this match expectations?** Yes:
- **#1 Sunrise City** is the only song that is pop, happy *and* close to energy 0.8, so it earns nearly every point.
- **#2 Gym Hero** is pop, but its mood is intense, so it gets the genre bonus and no mood bonus.
- **#3 Rooftop Lights** is happy with nearly the right energy, but "indie pop" doesn't count as "pop" because the profile has no also-OK genres.
- **#4–5** match on neither genre nor mood, so they are ranked by energy closeness alone.

Other profiles: `python -m src.main lofi`, `python -m src.main rock` and `python -m src.main pop/chill`.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



