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

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

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
