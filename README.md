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

More profiles are listed in [Stress Test](#stress-test-diverse-and-adversarial-profiles) below.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Stress Test: Diverse and Adversarial Profiles

Each profile is defined in `src/main.py`. Run one with `python -m src.main <name>`, or a group with `python -m src.main core`, `adversarial` or `all`. The first three are consistent listeners. The rest are edge cases designed to trick the scoring logic. Expand a profile to see its full terminal output.

### High-Energy Pop

✅ Works. Sunrise City is a near-perfect match. Rooftop Lights (indie pop, which this profile allows) comes 2nd. Gym Hero is 3rd: right energy and genre, but it's intense, not happy.

<details><summary><code>python -m src.main high-energy-pop</code></summary>

```text
$ python -m src.main high-energy-pop
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: high-energy-pop
  genre=pop, mood=happy, energy=0.88, acousticness=0.1, valence=0.85, instrumentalness=0.05, tempo_bpm=125
================================================================

#1  Sunrise City — Neon Echo
    pop / happy    Score: 4.77
      • genre match: pop (+1.50)
      • mood match: happy (+1.00)
      • energy 0.82 vs target 0.88 (+0.94)
      • acousticness 0.18 vs target 0.1 (+0.55)
      • valence 0.84 vs target 0.85 (+0.40)
      • instrumentalness 0.02 vs target 0.05 (+0.19)
      • tempo_bpm 118 vs target 125 (+0.18)

#2  Rooftop Lights — Indigo Parade
    indie pop / happy    Score: 3.86
      • genre close enough: indie pop (+0.75)
      • mood match: happy (+1.00)
      • energy 0.76 vs target 0.88 (+0.88)
      • acousticness 0.35 vs target 0.1 (+0.45)
      • valence 0.81 vs target 0.85 (+0.38)
      • instrumentalness 0.03 vs target 0.05 (+0.20)
      • tempo_bpm 124 vs target 125 (+0.20)

#3  Gym Hero — Max Pulse
    pop / intense    Score: 3.76
      • genre match: pop (+1.50)
      • energy 0.93 vs target 0.88 (+0.95)
      • acousticness 0.05 vs target 0.1 (+0.57)
      • valence 0.77 vs target 0.85 (+0.37)
      • instrumentalness 0.01 vs target 0.05 (+0.19)
      • tempo_bpm 132 vs target 125 (+0.18)

#4  Neon Overdrive — Pulse Cartel
    edm / euphoric    Score: 2.65
      • mood close enough: euphoric (+0.50)
      • energy 0.95 vs target 0.88 (+0.93)
      • acousticness 0.03 vs target 0.1 (+0.56)
      • valence 0.9 vs target 0.85 (+0.38)
      • instrumentalness 0.6 vs target 0.05 (+0.09)
      • tempo_bpm 128 vs target 125 (+0.19)

#5  Storm Runner — Voltline
    rock / intense    Score: 2.16
      • energy 0.91 vs target 0.88 (+0.97)
      • acousticness 0.1 vs target 0.1 (+0.60)
      • valence 0.48 vs target 0.85 (+0.25)
      • instrumentalness 0.05 vs target 0.05 (+0.20)
      • tempo_bpm 152 vs target 125 (+0.14)

================================================================
```

</details>

### Chill Lofi

✅ Works. The three lofi songs come first, then the ambient and jazz songs the profile marked as "close enough". The scores match the hand-calculated values in the README.

<details><summary><code>python -m src.main chill-lofi</code></summary>

```text
$ python -m src.main chill-lofi
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: chill-lofi
  genre=lofi, mood=chill, energy=0.38, acousticness=0.8, valence=0.58, instrumentalness=0.85, tempo_bpm=76
================================================================

#1  Library Rain — Paper Lanterns
    lofi / chill    Score: 4.81
      • genre match: lofi (+1.50)
      • mood match: chill (+1.00)
      • energy 0.35 vs target 0.38 (+0.97)
      • acousticness 0.86 vs target 0.8 (+0.56)
      • valence 0.6 vs target 0.58 (+0.39)
      • instrumentalness 0.9 vs target 0.85 (+0.19)
      • tempo_bpm 72 vs target 76 (+0.19)

#2  Midnight Coding — LoRoom
    lofi / chill    Score: 4.79
      • genre match: lofi (+1.50)
      • mood match: chill (+1.00)
      • energy 0.42 vs target 0.38 (+0.96)
      • acousticness 0.71 vs target 0.8 (+0.55)
      • valence 0.56 vs target 0.58 (+0.39)
      • instrumentalness 0.85 vs target 0.85 (+0.20)
      • tempo_bpm 78 vs target 76 (+0.20)

#3  Focus Flow — LoRoom
    lofi / focused    Score: 4.35
      • genre match: lofi (+1.50)
      • mood close enough: focused (+0.50)
      • energy 0.4 vs target 0.38 (+0.98)
      • acousticness 0.78 vs target 0.8 (+0.59)
      • valence 0.59 vs target 0.58 (+0.40)
      • instrumentalness 0.88 vs target 0.85 (+0.19)
      • tempo_bpm 80 vs target 76 (+0.19)

#4  Spacewalk Thoughts — Orbit Bloom
    ambient / chill    Score: 3.90
      • genre close enough: ambient (+0.75)
      • mood match: chill (+1.00)
      • energy 0.28 vs target 0.38 (+0.90)
      • acousticness 0.92 vs target 0.8 (+0.53)
      • valence 0.65 vs target 0.58 (+0.37)
      • instrumentalness 0.95 vs target 0.85 (+0.18)
      • tempo_bpm 60 vs target 76 (+0.17)

#5  Coffee Shop Stories — Slow Stereo
    jazz / relaxed    Score: 3.47
      • genre close enough: jazz (+0.75)
      • mood close enough: relaxed (+0.50)
      • energy 0.37 vs target 0.38 (+0.99)
      • acousticness 0.89 vs target 0.8 (+0.55)
      • valence 0.71 vs target 0.58 (+0.35)
      • instrumentalness 0.7 vs target 0.85 (+0.17)
      • tempo_bpm 90 vs target 76 (+0.17)

================================================================
```

</details>

### Deep Intense Rock

✅ Works. Storm Runner is the only rock song and wins by 1.4 points. Metal (Iron Requiem) beats intense pop (Gym Hero), as intended.

<details><summary><code>python -m src.main deep-intense-rock</code></summary>

```text
$ python -m src.main deep-intense-rock
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: deep-intense-rock
  genre=rock, mood=intense, energy=0.92, acousticness=0.08, valence=0.45, instrumentalness=0.05, tempo_bpm=150
================================================================

#1  Storm Runner — Voltline
    rock / intense    Score: 4.86
      • genre match: rock (+1.50)
      • mood match: intense (+1.00)
      • energy 0.91 vs target 0.92 (+0.99)
      • acousticness 0.1 vs target 0.08 (+0.59)
      • valence 0.48 vs target 0.45 (+0.39)
      • instrumentalness 0.05 vs target 0.05 (+0.20)
      • tempo_bpm 152 vs target 150 (+0.20)

#2  Iron Requiem — Black Cinder
    metal / angry    Score: 3.45
      • genre close enough: metal (+0.75)
      • mood close enough: angry (+0.50)
      • energy 0.97 vs target 0.92 (+0.95)
      • acousticness 0.04 vs target 0.08 (+0.58)
      • valence 0.25 vs target 0.45 (+0.32)
      • instrumentalness 0.1 vs target 0.05 (+0.19)
      • tempo_bpm 168 vs target 150 (+0.16)

#3  Gym Hero — Max Pulse
    pop / intense    Score: 3.20
      • mood match: intense (+1.00)
      • energy 0.93 vs target 0.92 (+0.99)
      • acousticness 0.05 vs target 0.08 (+0.58)
      • valence 0.77 vs target 0.45 (+0.27)
      • instrumentalness 0.01 vs target 0.05 (+0.19)
      • tempo_bpm 132 vs target 150 (+0.16)

#4  Concrete Poetry — Verse Theory
    hip-hop / confident    Score: 2.04
      • energy 0.78 vs target 0.92 (+0.86)
      • acousticness 0.12 vs target 0.08 (+0.58)
      • valence 0.62 vs target 0.45 (+0.33)
      • instrumentalness 0.02 vs target 0.05 (+0.19)
      • tempo_bpm 96 vs target 150 (+0.08)

#5  Sunrise City — Neon Echo
    pop / happy    Score: 2.01
      • energy 0.82 vs target 0.92 (+0.90)
      • acousticness 0.18 vs target 0.08 (+0.54)
      • valence 0.84 vs target 0.45 (+0.24)
      • instrumentalness 0.02 vs target 0.05 (+0.19)
      • tempo_bpm 118 vs target 150 (+0.13)

================================================================
```

</details>

### Adversarial: sad but energetic (energy 0.9, mood "sad")

⚠️ The mood bonus never fires because no song is labeled "sad". The closest label is "melancholy", and exact text matching doesn't count it. The low valence target (0.4 weight) can't outweigh energy (1.0), so the results are loud, aggressive songs. The actually sad song, Nocturne in Rain, isn't in the top 5.

<details><summary><code>python -m src.main sad-but-energetic</code></summary>

```text
$ python -m src.main sad-but-energetic
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: sad-but-energetic
  mood=sad, energy=0.9, valence=0.1
================================================================

#1  Iron Requiem — Black Cinder
    metal / angry    Score: 1.27
      • energy 0.97 vs target 0.9 (+0.93)
      • valence 0.25 vs target 0.1 (+0.34)

#2  Storm Runner — Voltline
    rock / intense    Score: 1.24
      • energy 0.91 vs target 0.9 (+0.99)
      • valence 0.48 vs target 0.1 (+0.25)

#3  Gym Hero — Max Pulse
    pop / intense    Score: 1.10
      • energy 0.93 vs target 0.9 (+0.97)
      • valence 0.77 vs target 0.1 (+0.13)

#4  Night Drive Loop — Neon Echo
    synthwave / moody    Score: 1.09
      • energy 0.75 vs target 0.9 (+0.85)
      • valence 0.49 vs target 0.1 (+0.24)

#5  Concrete Poetry — Verse Theory
    hip-hop / confident    Score: 1.07
      • energy 0.78 vs target 0.9 (+0.88)
      • valence 0.62 vs target 0.1 (+0.19)

================================================================
```

</details>

### Adversarial: pop genre + chill mood

✅ The genre 1.5 fix holds: chill songs fill #1, #2 and #4, the best pop song is #3, and Gym Hero is #5. The margin is thin, though: Sunrise City beats Spacewalk by only 0.08.

<details><summary><code>python -m src.main pop-genre-chill-mood</code></summary>

```text
$ python -m src.main pop-genre-chill-mood
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: pop-genre-chill-mood
  genre=pop, mood=chill, energy=0.4, acousticness=0.7, valence=0.65, instrumentalness=0.1, tempo_bpm=85
================================================================

#1  Midnight Coding — LoRoom
    lofi / chill    Score: 3.17
      • mood match: chill (+1.00)
      • energy 0.42 vs target 0.4 (+0.98)
      • acousticness 0.71 vs target 0.7 (+0.59)
      • valence 0.56 vs target 0.65 (+0.36)
      • instrumentalness 0.85 vs target 0.1 (+0.05)
      • tempo_bpm 78 vs target 85 (+0.18)

#2  Library Rain — Paper Lanterns
    lofi / chill    Score: 3.05
      • mood match: chill (+1.00)
      • energy 0.35 vs target 0.4 (+0.95)
      • acousticness 0.86 vs target 0.7 (+0.50)
      • valence 0.6 vs target 0.65 (+0.38)
      • instrumentalness 0.9 vs target 0.1 (+0.04)
      • tempo_bpm 72 vs target 85 (+0.17)

#3  Sunrise City — Neon Echo
    pop / happy    Score: 3.00
      • genre match: pop (+1.50)
      • energy 0.82 vs target 0.4 (+0.58)
      • acousticness 0.18 vs target 0.7 (+0.29)
      • valence 0.84 vs target 0.65 (+0.32)
      • instrumentalness 0.02 vs target 0.1 (+0.18)
      • tempo_bpm 118 vs target 85 (+0.13)

#4  Spacewalk Thoughts — Orbit Bloom
    ambient / chill    Score: 2.92
      • mood match: chill (+1.00)
      • energy 0.28 vs target 0.4 (+0.88)
      • acousticness 0.92 vs target 0.7 (+0.47)
      • valence 0.65 vs target 0.65 (+0.40)
      • instrumentalness 0.95 vs target 0.1 (+0.03)
      • tempo_bpm 60 vs target 85 (+0.15)

#5  Gym Hero — Max Pulse
    pop / intense    Score: 2.81
      • genre match: pop (+1.50)
      • energy 0.93 vs target 0.4 (+0.47)
      • acousticness 0.05 vs target 0.7 (+0.21)
      • valence 0.77 vs target 0.65 (+0.35)
      • instrumentalness 0.01 vs target 0.1 (+0.18)
      • tempo_bpm 132 vs target 85 (+0.10)

================================================================
```

</details>

### Adversarial: lofi genre + intense mood + energy 0.95

⚠️ A five-way near-tie (1.90–1.98). The genre bonus alone (1.5) roughly equals mood plus energy (1.0 + about 0.97). Calm lofi songs at energy 0.35–0.42 rank alongside the intense songs the user's energy target actually describes.

<details><summary><code>python -m src.main lofi-but-intense</code></summary>

```text
$ python -m src.main lofi-but-intense
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: lofi-but-intense
  genre=lofi, mood=intense, energy=0.95
================================================================

#1  Gym Hero — Max Pulse
    pop / intense    Score: 1.98
      • mood match: intense (+1.00)
      • energy 0.93 vs target 0.95 (+0.98)

#2  Midnight Coding — LoRoom
    lofi / chill    Score: 1.97
      • genre match: lofi (+1.50)
      • energy 0.42 vs target 0.95 (+0.47)

#3  Storm Runner — Voltline
    rock / intense    Score: 1.96
      • mood match: intense (+1.00)
      • energy 0.91 vs target 0.95 (+0.96)

#4  Focus Flow — LoRoom
    lofi / focused    Score: 1.95
      • genre match: lofi (+1.50)
      • energy 0.4 vs target 0.95 (+0.45)

#5  Library Rain — Paper Lanterns
    lofi / chill    Score: 1.90
      • genre match: lofi (+1.50)
      • energy 0.35 vs target 0.95 (+0.40)

================================================================
```

</details>

### Adversarial: "Pop" / "Happy" capitalized

🐞 **Bug: matching is case-sensitive.** This profile is identical to pop/happy except for capital letters, yet both bonuses silently vanish. Sunrise City drops from 3.48 to 0.98 and ties a hip-hop song.

<details><summary><code>python -m src.main capitalized-labels</code></summary>

```text
$ python -m src.main capitalized-labels
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: capitalized-labels
  genre=Pop, mood=Happy, energy=0.8
================================================================

#1  Sunrise City — Neon Echo
    pop / happy    Score: 0.98
      • energy 0.82 vs target 0.8 (+0.98)

#2  Concrete Poetry — Verse Theory
    hip-hop / confident    Score: 0.98
      • energy 0.78 vs target 0.8 (+0.98)

#3  Rooftop Lights — Indigo Parade
    indie pop / happy    Score: 0.96
      • energy 0.76 vs target 0.8 (+0.96)

#4  Night Drive Loop — Neon Echo
    synthwave / moody    Score: 0.95
      • energy 0.75 vs target 0.8 (+0.95)

#5  Storm Runner — Voltline
    rock / intense    Score: 0.89
      • energy 0.91 vs target 0.8 (+0.89)

================================================================
```

</details>

### Adversarial: out-of-range targets (energy 1.5, acousticness −0.5, tempo 250)

⚠️ Nothing checks the inputs. The ranking still degrades gracefully (the most extreme songs win, which is what the user probably meant), but tempo gives almost every song 0 because every gap is more than 92 BPM.

<details><summary><code>python -m src.main impossible-targets</code></summary>

```text
$ python -m src.main impossible-targets
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: impossible-targets
  energy=1.5, acousticness=-0.5, tempo_bpm=250
================================================================

#1  Iron Requiem — Black Cinder
    metal / angry    Score: 0.77
      • energy 0.97 vs target 1.5 (+0.47)
      • acousticness 0.04 vs target -0.5 (+0.28)
      • tempo_bpm 168 vs target 250 (+0.02)

#2  Neon Overdrive — Pulse Cartel
    edm / euphoric    Score: 0.73
      • energy 0.95 vs target 1.5 (+0.45)
      • acousticness 0.03 vs target -0.5 (+0.28)
      • tempo_bpm 128 vs target 250 (+0.00)

#3  Gym Hero — Max Pulse
    pop / intense    Score: 0.70
      • energy 0.93 vs target 1.5 (+0.43)
      • acousticness 0.05 vs target -0.5 (+0.27)
      • tempo_bpm 132 vs target 250 (+0.00)

#4  Storm Runner — Voltline
    rock / intense    Score: 0.65
      • energy 0.91 vs target 1.5 (+0.41)
      • acousticness 0.1 vs target -0.5 (+0.24)
      • tempo_bpm 152 vs target 250 (+0.00)

#5  Sunrise City — Neon Echo
    pop / happy    Score: 0.51
      • energy 0.82 vs target 1.5 (+0.32)
      • acousticness 0.18 vs target -0.5 (+0.19)
      • tempo_bpm 118 vs target 250 (+0.00)

================================================================
```

</details>

### Adversarial: empty profile

⚠️ Every song scores 0, so the "top 5" is just the first five rows of the CSV. The system can't say "I don't know enough about you"; it returns arbitrary songs as recommendations.

<details><summary><code>python -m src.main empty-profile</code></summary>

```text
$ python -m src.main empty-profile
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: empty-profile
  (no preferences)
================================================================

#1  Sunrise City — Neon Echo
    pop / happy    Score: 0.00
      • (no matching preferences)

#2  Midnight Coding — LoRoom
    lofi / chill    Score: 0.00
      • (no matching preferences)

#3  Storm Runner — Voltline
    rock / intense    Score: 0.00
      • (no matching preferences)

#4  Library Rain — Paper Lanterns
    lofi / chill    Score: 0.00
      • (no matching preferences)

#5  Gym Hero — Max Pulse
    pop / intense    Score: 0.00
      • (no matching preferences)

================================================================
```

</details>

### Adversarial: wants rock at energy 0.9 but max_energy 0.3

⚠️ The dealbreaker runs before scoring, so every rock song is removed and only 2 songs survive: an ambient track and a classical piece. That's technically correct, but the user's contradiction is never flagged.

<details><summary><code>python -m src.main strict-dealbreaker</code></summary>

```text
$ python -m src.main strict-dealbreaker
Loading songs from data/songs.csv...
Loaded songs: 18

================================================================
Profile: strict-dealbreaker
  genre=rock, energy=0.9, max_energy=0.3
================================================================

#1  Spacewalk Thoughts — Orbit Bloom
    ambient / chill    Score: 0.38
      • energy 0.28 vs target 0.9 (+0.38)

#2  Nocturne in Rain — Elise Marchetti
    classical / melancholy    Score: 0.30
      • energy 0.2 vs target 0.9 (+0.30)

================================================================
(only 2 songs passed the filters)
```

</details>

### What the stress test revealed

| Finding | Profiles | Severity |
|---|---|---|
| Label matching is case-sensitive, so "Pop" ≠ "pop" | capitalized-labels | Bug |
| A mood with no exact label in the catalog (e.g. "sad") gets no credit, even when a near-synonym exists | sad-but-energetic | Design gap |
| The genre bonus can outweigh a strong numeric signal (energy 0.95 vs 0.40) | lofi-but-intense | Weight balance |
| Energy dominates valence, so "sad" requests get loud songs | sad-but-energetic | Weight balance |
| Out-of-range targets and empty profiles are accepted silently | impossible-targets, empty-profile | Input validation |
| A dealbreaker can wipe out everything the user asked for without warning | strict-dealbreaker | UX |

The three consistent profiles all behave as intended. Every failure comes from conflicting, unusual or malformed input.

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



