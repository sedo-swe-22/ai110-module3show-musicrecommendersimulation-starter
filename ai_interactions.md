# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

**Challenge 1: Advanced song features.** I asked the agent (Claude Code, in agent mode) to add five new song attributes to the catalog and make the scoring account for them. The rule was that the existing recommendations must not change unless a user asks for the new features.

**Prompts used:**

> "Try all of them." *(the four optional extensions, pasted from the project instructions)*

> *(Challenge 1, as given to the agent)* "Introduce 5 or more complex attributes to your dataset that are not currently present in the baseline data, such as Song Popularity (0-100), Release Decade, or Detailed Mood Tags. Update both data/songs.csv and the scoring logic in src/recommender.py so scoring accounts for the new attributes."

The constraints the agent worked under (from earlier project decisions):
- A missing preference is skipped, not scored as 0.
- The default output must stay identical, so the README and model card samples stay valid.
- Every point earned must produce a readable reason.

**What did the agent generate or change?**

- **`data/songs.csv`:** five new columns for all 18 songs:
  - `popularity` (0–100)
  - `release_decade` (1970–2020)
  - `mood_tags` (3 tags per song, `;`-separated, e.g. `sad;rainy;bittersweet`)
  - `speechiness` (0–1)
  - `liveness` (0–1)
- **`src/recommender.py`:**
  - **Loading:** `load_songs` now converts `release_decade` to `int` and splits `mood_tags` into a list.
  - **Scoring:** new weights `popularity 0.3`, `release_decade 0.4`, `speechiness 0.2` and `liveness 0.1`. A `FEATURE_SCALES` table sets how big a gap drops closeness to 0: 100 points of popularity, 40 years, 92 BPM. The old tempo-only special case became one generic closeness formula.
  - **Mood tags:** +0.3 per shared tag, at most 3 tags (0.9). Matching ignores capitals, so "SAD" matches "sad".
  - **Data classes:** `Song` and `UserProfile` got the new fields, with defaults so the old tests still construct them.
- **`src/main.py`:** an `extended` profile group: `sad-energetic-tagged`, `nostalgic-80s-deep-cuts` and `wordy-live-hits`.
- **`tests/test_extensions.py`:** tests for parsing, skipping, tag matching, closeness math, and the sad-tag scenario.
- **Commands:**
  - `python -m src.main all | diff - baseline.txt`, the regression check
  - `python -m src.main extended`
  - `.venv/bin/python -m pytest`

**What did you verify or fix manually?**

- **Regression check:** before any change, the full output of all 11 existing profiles was saved. After each change it was diffed against the new output. The result was **identical**, so the new features really are opt-in and every existing doc sample is still accurate.
- **Hand math:**
  - Night Drive Loop with target decade 2000 and popularity 64: 0.4 × (1 − 20/40) + 0.3 × (1 − 0/100) = **0.5**, matching `test_decade_and_popularity_closeness`.
  - Iron Requiem with tags ["SAD", "Dark"]: 2 × 0.3 = **0.60**.
- **Did it fix anything?** Partly. The old adversarial "sad but energetic" listener can now say *sad* through tags. Iron Requiem (tagged `sad`) wins by a clear margin, 1.87 vs. 1.24, where before it led by just 0.03. But happy-sounding Gym Hero is still #3, so tags only help songs that carry the tag. The underlying energy-dominance bias remains.
- **Something to watch:** in `wordy-live-hits`, the actual rap song (Concrete Poetry, speechiness 0.31) only came 2nd. Speechiness is worth just 0.2 points, so energy and decade decided the order. That's a weight choice to revisit, not a bug.
- **New bias risk:** `popularity` can create a "rich get richer" effect if a profile asks for popular songs. Every profile that doesn't ask for it is unaffected, because the feature is skipped.
- **Tests:** 15 of 15 pass (`.venv/bin/python -m pytest`).

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

**Strategy pattern** (Challenge 2: multiple scoring modes). Each ranking strategy is a `ScoringMode` object. The ranking code takes whichever strategy it's given, so modes can be swapped at runtime without touching the ranking logic.

| Mode | Idea | Weights |
|---|---|---|
| `balanced` (default) | The original recipe | genre 1.5, mood 1.0, energy 1.0 |
| `genre-first` | Genre beats everything else combined | genre **3.5** > mood + all core numbers (3.4) |
| `mood-first` | Mood leads, genre is a tiebreaker | mood **2.5**, genre 0.75 |
| `energy-focused` | How the song *feels*, not its labels | energy **2.5**, tempo 0.4, genre 0.5, mood 0.5 |

**How did AI help you brainstorm or implement it?**

I asked the AI to brainstorm a design that keeps the code modular. It weighed three options:

1. **if/elif on a mode string inside `score_song`.** Simplest, but every new mode means editing the scoring function, and the branches would repeat the same formula.
2. **A class per mode** (`GenreFirstScorer`, `MoodFirstScorer`, …) that overrides `score()`. This is the textbook Strategy pattern, but all four modes run *the same formula* with *different weights*, so the subclasses would be near-copies.
3. **One strategy class configured with weights** (`ScoringMode`), plus a registry dict `MODES`. ✅ **Chosen.**

Option 3 is still the Strategy pattern. Each mode is an interchangeable object that encapsulates a scoring policy, and the caller picks one at runtime. Adding a mode is one line, and there's no duplicated logic. The AI noted the trade-off: if a future mode needs *different logic*, not just different weights (say, a learned model), that's the point to switch to option 2 by giving `ScoringMode` a `score()` method that subclasses override.

**How I checked it:**
- `balanced` reproduces the original output byte for byte.
- `test_genre_first_genre_weight_beats_every_core_non_genre_point` confirms genre-first's claim (3.5 > 3.4).
- I recomputed Sunrise City for pop/chill in genre-first mode by hand: 3.5 + 1.504 = **5.004**, which is the balanced score of 3.004 plus 2.0 extra genre points. It matches the output.

**How does the pattern appear in your final code?**

- **`src/recommender.py`:**
  - **`ScoringMode`:** a frozen dataclass holding one strategy's weights, with `max_core_score()`.
  - **`MODES` / `DEFAULT_MODE`:** the registry of available strategies.
  - **`score_song(user_prefs, song, mode=DEFAULT_MODE)`:** the context that uses whichever strategy it's given.
  - **`recommend_songs(..., mode=...)`** and **`Recommender(songs, mode=...)`** pass the strategy through, so the functional and OOP paths stay in sync.
- **`src/main.py`:** `--mode {balanced,genre-first,mood-first,energy-focused}` picks the strategy from the command line.
- **`tests/test_extensions.py`:** the mode tests.
