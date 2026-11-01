# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

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

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

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

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
