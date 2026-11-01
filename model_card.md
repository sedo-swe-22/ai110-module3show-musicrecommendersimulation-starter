# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**TuneJudge 1.0**

It works like a judge at a talent show: every song gets a scorecard, and the five highest scores win.

---

## 2. Intended Use  

**Goal / task:** given a listener's taste, suggest the 5 songs from a small catalog that fit them best, and say *why* each one was picked.

It doesn't predict whether someone will like a song in the future. It only measures how closely each song matches what the listener said they want.

**What the listener provides:** a favorite genre and mood, optional "close enough" genres and moods, and target values for energy, acousticness, valence (how happy it sounds), instrumentalness and tempo. Every field is optional.

**Assumptions it makes about the user:**
- They can describe their taste in words and numbers.
- Their taste doesn't change with time, context or activity.
- They use the same labels the catalog uses (for example "pop", not "Pop").

**Intended use:**
- A classroom project for learning how content-based recommenders turn data into rankings.
- Experimenting with weights and seeing how the rankings respond.
- Showing how bias can creep into a simple scoring rule.

**Not intended for:**
- **Real users or a real music app.** The catalog is 18 made-up songs.
- **Judging the quality of music or artists.** A low score means "doesn't match this profile", not "bad song".
- **Decisions with consequences**, such as which artists get promoted or paid. Its biases (see section 6) would be unfair at that scale.
- **Listeners with no stated preferences.** It returns arbitrary songs instead of saying "I need more information".

---

## 3. How the Model Works  

Think of the recommender as a judge at a talent show who gives every song in the catalog a scorecard, then reads out the five highest scores.

**What the judge looks at in each song:**
- its **genre** (pop, lofi, rock…) and **mood** (happy, chill, intense…)
- five sound measurements on a 0–1 scale:
  - **energy:** calm to intense
  - **acousticness:** electronic to acoustic
  - **valence:** sad to happy
  - **instrumentalness:** vocals to no vocals
  - **tempo:** beats per minute

**What the listener tells it:** a favorite genre and mood, plus optional "close enough" alternatives (for example, a lofi fan might also accept ambient or jazz). They can also give a target for each sound measurement, such as "energy around 0.4". Anything the listener leaves out is simply ignored, so nobody is penalized for not having an opinion about tempo.

**How the points add up:**
1. **Genre bonus:** 1.5 points for the favorite genre, or half (0.75) for a "close enough" genre.
2. **Mood bonus:** 1.0 point for the favorite mood, or 0.5 for a "close enough" mood.
3. **Closeness points:** for each sound measurement, the nearer the song is to the listener's target, the more points it earns. A perfect match earns the full weight and a total opposite earns zero. Energy matters most (up to 1.0), then acousticness (0.6), valence (0.4), instrumentalness (0.2) and tempo (0.2).

The best possible score is 4.9. Every point a song earns comes with a written reason, such as "mood match: chill (+1.00)", so you can always see *why* it was recommended.

**Choosing the winners:** every song gets scored and the list is sorted from highest to lowest. The top five are shown. If the listener set an energy "dealbreaker" (for example, nothing above 0.9), songs over that line are removed before judging.

**Changes from the starter logic:**
- **More data:** the catalog grew from 10 to 18 songs, and a new instrumentalness measurement was added.
- **Closeness, not size:** songs are rewarded for being *close* to what the listener wants rather than for having high or low values.
- **Partial credit:** "close enough" genres and moods earn half points.
- **Genre weight lowered from 2.0 to 1.5:** most genres appear only once in the catalog. At 2.0, a pop fan who wanted chill music was being handed an intense workout song just because it was labeled pop.

---

## 4. Data  

**Size:** 18 songs in `data/songs.csv`. The starter had 10; I added 8 more to cover genres and moods it was missing.

**Features per song:**
- **Labels:** genre and mood. Each song has exactly one of each.
- **Numbers from 0 to 1:** energy, acousticness, valence (how happy it sounds), danceability and instrumentalness. I added instrumentalness.
- **Tempo:** in beats per minute, from 60 to 168.

Danceability is loaded but not scored, because it mostly repeats valence and energy.

**Advanced attributes (optional extension):**
- `popularity` (0–100)
- `release_decade` (1970–2020)
- `mood_tags` (3 descriptive tags per song, such as "sad;rainy;bittersweet")
- `speechiness` (sung vs. spoken)
- `liveness` (studio vs. live)

They are only scored when a listener asks for them, so the default results don't change.

**What's represented:**
- **15 genres:** lofi, pop, rock, ambient, jazz, synthwave, indie pop, hip-hop, country, classical, edm, r&b, metal, reggae, folk.
- **14 moods:** chill, happy, intense, relaxed, moody, focused, confident, nostalgic, melancholy, euphoric, romantic, angry, laid-back, wistful.

**Limits of the data:**
- **Most genres have just one song.** 13 of the 15 do; only lofi (3) and pop (2) repeat. Fans of most genres get one real match and then filler.
- **Energy has a hole.** No song falls between 0.55 and 0.75, so medium-energy listeners have little to choose from.
- **The values are invented,** not measured from real audio.
- **Some moods are missing.** There's no "sad", for example; the closest is "melancholy".
- **It's mostly Western, English-language genres.** There are no K-pop, Latin, Afrobeats or regional styles.
- **Whole parts of taste are absent:** lyrics, language, era, artist popularity and listening history.

---

## 5. Strengths  

**It works well when a listener's preferences agree with each other.** All three consistent profiles produced top 5s that match musical intuition:

- **Chill Lofi:** Library Rain, Midnight Coding, Focus Flow, then the ambient and jazz songs the profile allowed as "close enough". Every pick fits a calm, instrumental study session, and the scores match the hand-calculated values.
- **Deep Intense Rock:** Storm Runner (the only rock song) wins clearly, 4.86 vs 3.45. Metal (Iron Requiem) ranks above intense pop (Gym Hero), which is the right order for a rock fan.
- **High-Energy Pop:** Sunrise City is a near-perfect match (4.77). Indie pop and an energetic pop workout song follow.

**Patterns the scoring captures correctly:**
- **Closeness, not "more is better":** a calm listener gets calm songs and an intense listener gets intense songs, from the same formula.
- **Partial credit works:** neighbors like ambient for a lofi fan, or metal for a rock fan, rank above unrelated songs but below exact matches.
- **Variety at the top:** across 11 test profiles, 7 different songs ranked #1. No single song wins everything.
- **Every score explains itself:** each point earned has a written reason, so a surprising result can be traced in seconds.

---

## 6. Limitations and Bias 

**Main weakness: the score is really an energy score, so listeners who care about something else get ignored.** Energy carries the biggest weight (1.0), and in this catalog acousticness (r = −0.97) and tempo (r = 0.90) move almost in lockstep with it, so about 1.8 of the 2.4 numeric points measure the same "calm vs. loud" quality. In the stress test, a "sad but energetic" listener (valence target 0.1) got Gym Hero, one of the happiest-sounding songs in the catalog (valence 0.77), at #3, just because its energy matched. Happiness (valence) is worth only 0.4, so the "sad" half of the request barely counted. The catalog makes it worse: no song has energy between 0.55 and 0.75, so a listener who wants medium-energy music (say 0.65) has only two songs within 0.1 of their target, and the labels end up deciding almost everything. Doubling the energy weight in our experiment raised energy's share to about 54% of the score and made this worse, which creates an energy "filter bubble" where users are sorted into "calm" or "loud" and rarely shown songs that match their mood from the other side.

**Other biases and limitations we observed:**

- **Exact-label matching.** "Pop" ≠ "pop" (matching is case-sensitive), and "sad" earns nothing even though "melancholy" exists. Users who describe their taste in different words than the catalog uses lose the genre and mood bonuses silently.
- **Unequal genre coverage creates uneven experiences.** 13 of 15 genres have exactly one song. A lofi fan gets a coherent, all-lofi top 5 (arguably a filter bubble of its own). A folk, country or classical fan gets one match and then four songs chosen by energy alone.
- **"Middle" songs surface far more than extreme ones for random listeners.** In a simulation of 5,000 random listeners with no genre or mood preference, Midnight Coding appeared in 49% of top 5s, but Iron Requiem, Gym Hero and Neon Overdrive appeared in only 11–12%. The linear "1 − gap" closeness favors songs near the center of the range, so very intense or very quiet songs need equally extreme listeners to be found.
- **Our own tests were biased toward high energy.** 7 of 11 test profiles asked for high energy, which is why Gym Hero looked over-recommended (8 of 11 top 5s) while four mid-energy songs never appeared. The evaluation was skewed, not just the model.
- **Arbitrary tie-breaking.** Tied songs keep their CSV order, so an empty profile "recommends" the first five rows of the file.
- **Popularity can feed a "rich get richer" loop.** The optional `popularity` feature rewards songs close to a target popularity. If many users asked for popular songs, already-popular songs would get recommended more and become more popular, and lesser-known artists would rarely surface. It's skipped unless a user asks for it, so the default profiles are unaffected.
- **Extra work for the user.** Partial credit only works if users list "close enough" genres and moods themselves. A user who doesn't know to type "indie pop" never sees it as related to pop.
- **Missing dimensions of taste.** There are no lyrics, language, era, artist familiarity or listening history, so the system can't learn that a stated preference is wrong, and it treats every listener's words at face value.

---

## 7. Evaluation  

**Profiles tested:** 11 in total, all defined in `src/main.py` (`python -m src.main all`). The full terminal output is in the README's Stress Test section.
- **The starter default:** pop/happy, energy 0.8.
- **3 consistent listeners:** High-Energy Pop, Chill Lofi and Deep Intense Rock.
- **7 adversarial edge cases:**
  - sad but energetic
  - pop genre with a chill mood
  - lofi genre with an intense mood
  - capitalized labels ("Pop" / "Happy")
  - impossible targets (energy 1.5)
  - an empty profile
  - a dealbreaker that removes almost everything

**What I looked for:** whether the top 5 "felt right" for that listener, whether the same song kept showing up everywhere, and whether a #1 won clearly or only by a hair.

**Checks I ran:**
- **Hand math:** I calculated several scores by hand and confirmed the code matches (e.g. Library Rain 4.807, Gym Hero 2.812 for pop/chill).
- **Repetition count:** how many top 5s each song appears in, across all 11 profiles.
- **Explaining #1:** I asked the AI assistant to explain step by step why a song ranked #1 and to find the smallest weight change that would flip it.
- **Weight-shift experiment (energy 1.0 → 2.0, genre 1.5 → 0.75):** I reran all 11 profiles and compared them with the baseline. The full before/after output is in the README under "Experiments You Tried".
  - **Better:** pop/happy, where the happy indie song now beats the intense workout song, and lofi-but-intense, where intense songs replace the calm lofi ones.
  - **Worse:** Deep Intense Rock, where pop Gym Hero passes metal Iron Requiem, and pop-genre-chill-mood, which lost every pop song.
  - **Unchanged:** the other 7 profiles.

  The results were **different, not more accurate**, so I reverted to the baseline. Gym Hero's repetition barely moved (8 → 7 lists), which showed the repetition wasn't caused by the genre weight.

### Comparing profiles side by side

Comparing every possible pair of 11 profiles would mean 55 comparisons, most of them uninformative. I compared **every pair of the four normal profiles** (6 pairs), plus **each edge case against its closest normal "twin"** (7 pairs). Each twin differs in only one or two settings, so any change in the output can be traced to that setting.

**The four normal profiles against each other:**

| Pair | Songs shared | What changed, and why it makes sense |
|---|---|---|
| **pop/happy vs. High-Energy Pop** | 3 of 5 | Both lists start with Sunrise City. In High-Energy Pop, Rooftop Lights jumps above Gym Hero, and the last two spots change from hip-hop/synthwave to an euphoric EDM song and a rock song. High-Energy Pop tells the system more: "indie pop is close enough", "euphoric is close enough", and "I want happy-sounding music" (valence 0.85). That extra detail lets the happy indie song beat the intense workout song. The basic pop/happy profile only mentions energy, so its #4–5 are just "whatever is closest to energy 0.8". **More detail = a better list, which is what should happen.** |
| **pop/happy vs. Chill Lofi** | 0 of 5 | No overlap at all. These listeners disagree on everything: genre, mood, and energy (0.8 vs. 0.38). **Opposite tastes, opposite lists: correct.** |
| **pop/happy vs. Deep Intense Rock** | 3 of 5 | Sunrise City, Gym Hero and Concrete Poetry appear in both, because both listeners want loud music (energy 0.8 vs. 0.92). But Sunrise City is #1 for pop/happy and only #5 for rock. The same loud songs are in the running, and the genre and mood labels decide the order. **Makes sense.** |
| **High-Energy Pop vs. Chill Lofi** | 0 of 5 | A mirror image. High-Energy Pop's picks all have energy 0.76–0.95 and little acoustic sound. Chill Lofi's picks all have energy 0.28–0.42 and are mostly acoustic. The energetic profile goes for loud electronic tracks, the calm profile for soft, acoustic, mostly instrumental ones. **Exactly what the energy and acousticness targets are for.** |
| **High-Energy Pop vs. Deep Intense Rock** | 3 of 5 | The most revealing pair. Both share Sunrise City, Gym Hero and Storm Runner, **in reversed order**: Sunrise City is #1 and Storm Runner #5 for pop, and the other way round for rock. Both want loud, non-acoustic music, so the same songs qualify. The genre label (pop vs. rock) and the happiness target (0.85 vs. 0.45) decide who wins. **Valid: this shows the labels and valence doing their job once energy has narrowed the field.** |
| **Chill Lofi vs. Deep Intense Rock** | 0 of 5 | No overlap. Calm acoustic study music vs. loud aggressive guitar music. **Correct.** |

**Each edge case against its normal twin:**

| Pair | What changed, and why |
|---|---|
| **pop/happy vs. capitalized-labels** ("Pop"/"Happy") | The only difference is capital letters, yet Sunrise City falls from 3.48 to 0.98, Gym Hero disappears from the list, and a rock song enters. The system compares labels letter for letter, so "Pop" isn't "pop" and both bonuses vanish. **This does *not* make sense to a user. It's a bug.** |
| **High-Energy Pop vs. pop-genre-chill-mood** | Same favorite genre, opposite mood and energy. The two pop songs drop from #1 and #3 to #3 and #5, and three calm, chill songs take over. The mood bonus plus the closeness points (up to 3.4 together) outweigh the genre bonus (1.5). **Makes sense: when someone asks for "pop, but chill", the chill part should matter most.** |
| **Chill Lofi vs. lofi-but-intense** | Same genre, opposite mood and energy. Intense songs (Gym Hero, Storm Runner) push into the top 3, but calm lofi songs still hold #2, #4 and #5 on the genre bonus alone, even though their energy (0.35–0.42) is nowhere near the requested 0.95. **Only partly sensible.** The genre label is strong enough to keep songs that contradict the listener's energy. |
| **Deep Intense Rock vs. sad-but-energetic** | Both want loud music, but the second profile has no genre and wants sad-sounding songs (valence 0.1). Storm Runner loses its rock and intense bonuses and drops to #2. Iron Requiem, the darkest-sounding loud song (valence 0.25), moves up to #1. **That part makes sense.** But happy-sounding Gym Hero (valence 0.77) still sits at #3, because "sadness" is worth so little next to energy. |
| **Deep Intense Rock vs. strict-dealbreaker** | Same rock and energy 0.9 wishes, plus "nothing above energy 0.3". Every rock song is removed before scoring, and only an ambient track and a classical piece survive. **Correct by the rules, but unhelpful.** The listener contradicted themselves and the system never says so. |
| **High-Energy Pop vs. impossible-targets** (energy 1.5) | An impossible target effectively means "as loud and non-acoustic as possible". The list switches to the most extreme songs (Iron Requiem 0.97, Neon Overdrive 0.95), and Sunrise City drops to #5 because nothing asks for pop or happiness. **Reasonable.** The system doesn't crash; it gives the closest real songs. |
| **pop/happy vs. empty-profile** | With no preferences, every song scores 0 and the list is simply the first five rows of the file. Sunrise City is #1 only because it is the first row. **Not a valid recommendation.** The system should say "tell me more" instead. |

### Why does "Gym Hero" keep showing up for people who just want Happy Pop?

Think of the recommender as a judge holding a scorecard. For the basic "pop, happy, energy 0.8" listener, the card has only three lines:

| Question on the scorecard | Points available | Gym Hero | Rooftop Lights |
|---|---|---|---|
| Is it labeled "pop"? | 1.5 | ✅ 1.5 | ❌ 0 (it's labeled "indie pop") |
| Is it labeled "happy"? | 1.0 | ❌ 0 (it's labeled "intense") | ✅ 1.0 |
| How close is its energy to 0.8? | up to 1.0 | 0.87 (energy 0.93) | 0.96 (energy 0.76) |
| **Total** | | **2.37 → #2** | **1.96 → #3** |

Gym Hero is a workout anthem, not a happy song. It beats a genuinely happy song for three reasons:

1. **The "pop" sticker is worth more than the "happy" sticker** (1.5 vs. 1.0 points).
2. **The judge reads stickers literally.** "Indie pop" isn't "pop", so the happy indie song gets nothing for genre.
3. **Only two songs in the whole catalog carry the "pop" sticker.** Sunrise City takes #1, and Gym Hero automatically gets the next-best genre score.

On top of that, Gym Hero is one of the loudest songs in the catalog, so it also scores well for anyone who asks for high energy (rock fans, workout listeners, even the "sad but energetic" profile). That's why it showed up in 8 of 11 lists.

**How to make it go away:** tell the system more. The High-Energy Pop profile says "indie pop is close enough" and "I like happy-sounding music". With that, Rooftop Lights moves ahead of Gym Hero (3.86 vs. 3.76). The scoring isn't broken here. It can only judge on what the listener actually tells it.

**What surprised me:**

1. **One song shows up almost everywhere: Gym Hero, in 8 of 11 top 5s.** Sunrise City and Storm Runner appear in 7 each. The genre weight isn't the main cause, because Gym Hero got the genre bonus in only 4 of its 8 appearances. It is an extreme song (energy 0.93, almost no acoustic sound or instrumental passages), so it fits *any* high-energy request well. 7 of my 11 profiles asked for high energy, and only about 5 songs in the catalog are that loud. Meanwhile 4 songs (r&b, reggae, country and folk, all mid-energy) never appeared in any top 5, because no profile asked for mid-energy music. Part of the repetition comes from how I designed the tests, and part from the small catalog.

2. **A #1 can be a coin flip.** For the "lofi but intense" profile (genre lofi, mood intense, energy 0.95):

   | Song | Genre | Mood | Energy | Total |
   |---|---|---|---|---|
   | Gym Hero (pop / intense, 0.93) | 0 | +1.0 | 0.98 | **1.98** |
   | Midnight Coding (lofi / chill, 0.42) | +1.5 | 0 | 0.47 | 1.97 |
   | Storm Runner (rock / intense, 0.91) | 0 | +1.0 | 0.96 | 1.96 |

   Gym Hero wins by **0.01**. Two kinds of song are competing: "matches the mood and the energy" and "matches the genre only". They balance almost exactly, because the genre bonus beats the mood bonus by 0.5, and a calm lofi song loses about 0.5 energy points. Raising the genre weight from 1.5 to just 1.52 would hand #1 to a calm lofi track, for someone who asked for energy 0.95. Gym Hero is the better answer musically, but it wins by luck, not by a clear margin.

3. **Labels outweigh sound.** Focus Flow is arguably the best study track for Chill Lofi: its energy of 0.40 is the closest of any song. It still ranks 3rd, behind two songs that sound the same, only because its mood label says "focused" instead of "chill".

4. **The bottom of the list is filler.** For Deep Intense Rock, #4 is confident hip-hop and #5 is happy pop. Neither fits a rock fan. After the few loud songs run out, the ranking is decided by energy closeness alone. With only 18 songs, the top 3 are meaningful, and #4–5 often aren't.

5. **Matching is case-sensitive.** "Pop" and "Happy" (capitalized) silently lose both bonuses, and Sunrise City drops from 3.48 to 0.98.

**Overall:** the results feel right when the listener's preferences agree with each other. They get fragile when the preferences conflict, and thin once the catalog runs out of good matches.

---

## 8. Future Work  

1. **Smarter label matching.** Compare labels without caring about capitals ("Pop" = "pop"), and add a small synonym list ("sad" ≈ "melancholy", "chill" ≈ "laid-back"). This fixes two bugs found in testing without the user having to do anything.

2. **Rebalance the numbers so energy doesn't dominate.** Energy, acousticness and tempo measure almost the same thing. I'd lower acousticness and tempo and give valence more weight, so a "sad" request gets sad-sounding songs, not just ones with the right energy.

3. **Add variety and honesty to the top 5.**
   - **Variety:** allow at most one song per artist and two per genre, so a lofi fan also sees something new.
   - **Honesty:** if the best score is very low (or the profile is empty or contradicts itself), say "I need more information" instead of showing random songs.

**With more time:** a bigger catalog that fills the 0.55–0.75 energy gap, and learning from skips and replays so the system doesn't rely only on what the user types.

---

## 9. Personal Reflection  

**My biggest learning moment.** Gym Hero showed up in 8 of my 11 top-5 lists, and I was sure the genre weight was too strong. When I counted, it got the genre bonus in only half of those lists. It kept appearing because it's one of the loudest songs, and most of my test profiles asked for loud music. The bias was in my tests, not only in the model. Now I know that how you test a system can create the problem you think you're finding.

**When I had to double-check the AI.** AI was fast and helpful, but I couldn't just trust it:
- **I checked the math by hand.** I recomputed scores like Library Rain (4.807) myself to make sure the code really followed my recipe.
- **A comment didn't match the plan.** A code comment said missing preferences would "renormalize" the other weights. My plan said they would simply be skipped. It had to be caught and fixed during the plan review, or the docs and the code would have disagreed.
- **The AI used the wrong evidence.** Its first draft of the bias section used a quiet song as proof that energetic listeners were treated unfairly. That song never fit the request anyway, so the example proved nothing. The problem was real, but the evidence wasn't.

**What surprised me.** The scoring is just a weighted sum of seven numbers. But when it prints "mood match: chill (+1.00)" next to each song, it feels thoughtful, almost like it understands me. The reasons make it seem smart. That makes me think real apps feel smart partly because of how they explain themselves, not only because of how they score.

**What I'd try next.**
1. **Smarter label matching:** ignore capital letters and add synonyms, so "Pop" matches "pop" and "sad" matches "melancholy".
2. **Learning from listening:** use what people actually play and skip, not only what they type in.
