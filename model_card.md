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

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

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

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

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
