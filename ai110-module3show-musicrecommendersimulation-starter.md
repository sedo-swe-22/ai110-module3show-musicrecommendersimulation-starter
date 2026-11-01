# How streaming platforms predict what you'll love next

This summary comes from general knowledge of public engineering blogs and research papers, not live web searches. The platforms don't publish their exact systems, so treat the specifics as approximate.

## The big picture

Spotify, YouTube, Netflix and similar platforms don't use one algorithm. They run a **multi-stage pipeline** that combines several signals:

1. **Candidate generation** narrows millions of items to hundreds, using fast approximate methods.
2. **Ranking** scores those hundreds with a heavier model that predicts things like click, full listen, skip, save or watch time.
3. **Re-ranking** adjusts the list for diversity, freshness, fairness to artists or creators, and business rules.

Most of the signal is **implicit feedback**, meaning behavior rather than ratings. Examples are plays, skips, replays, saves, playlist adds, watch time and search queries. Skipping a song within 5 seconds is a strong negative signal. A repeat listen is a strong positive one.

## Collaborative filtering (CF)

**Idea:** "People who behave like you liked this, so you probably will too." It uses only the interaction history of many users and knows nothing about what the songs sound like.

**How it works:** Build a huge user × item matrix of plays. Then either:
- **Neighborhood methods** find users (or items) with similar patterns.
- **Matrix factorization** or **neural embeddings** learn a short vector for each user and each song, so that vectors for users and songs that go together end up close in space.

**Example:** You and another listener both play Tame Impala, Mac DeMarco and Beach House. They also love Real Estate, which you've never heard. CF recommends Real Estate to you, even if nothing in the audio would have told it so. Spotify's Discover Weekly is the best-known example, built partly on playlist co-occurrence. Songs that often appear together in user playlists are treated as related.

| Strengths | Weaknesses |
|---|---|
| Finds surprising, serendipitous matches | **Cold start:** new songs and new users have no data |
| Needs no metadata or audio analysis | **Popularity bias:** popular items get more data and more recommendations |
| Captures taste that's hard to describe | Can create filter bubbles |

## Content-based filtering (CBF)

**Idea:** "You liked songs with these attributes, so here are more songs with similar attributes." It looks at the items themselves and builds a profile of your taste from them.

**Attributes used:**
- **Metadata:** genre, artist, year, language, tags.
- **Audio features:** tempo, energy, danceability, valence (mood), acousticness, loudness. Spotify exposes many of these. Deeper models learn directly from spectrograms of the raw audio.
- **Text:** lyrics, reviews, and blog or playlist text (YouTube also uses titles, descriptions and captions).

**Example:** You mostly play low-tempo, high-acousticness, low-energy songs. CBF scores every song by how close its features are to your profile. A brand-new indie folk track with no listeners yet can still be recommended immediately.

| Strengths | Weaknesses |
|---|---|
| Handles new or obscure items (no cold start for items) | Needs good features, and "sounds similar" isn't "feels similar" |
| Transparent: you can explain *why* something was picked | Tends to over-specialize, so recommendations get narrow |
| Needs no data from other users, which is better for privacy | Can't discover cross-genre taste (e.g. that jazz fans like some lo-fi) |

## Side-by-side

| | Collaborative | Content-based |
|---|---|---|
| **Input** | Many users' behavior | Song attributes plus one user's history |
| **Asks** | "Who is similar to you?" | "What is similar to what you liked?" |
| **New song with no plays** | Fails | Works |
| **Novelty** | High | Low |
| **Explainable** | Hard | Easy |

## What the big platforms actually do

- **Hybrid systems:** CBF covers cold start for new releases and CF supplies discovery, usually blended in one model.
- **Spotify** combines CF on listening and playlist data, NLP over text about artists and songs, and audio analysis of tracks. It layers contextual signals (time of day, device, session) on top and has used bandit and reinforcement-learning methods to balance exploring new music against serving known favorites.
- **YouTube** uses a two-stage deep neural network (published in the 2016 "Deep Neural Networks for YouTube Recommendations" paper) with candidate generation and then ranking. It optimizes for **expected watch time** rather than clicks, to avoid rewarding clickbait.
- **Common modern building block:** two-tower neural networks, one tower for the user and one for the item. They are trained so that matching pairs land close together, which allows fast nearest-neighbor retrieval.

## Takeaway for this simulator

A small project like this one is naturally **content-based**. You have a handful of songs with attributes and a user profile, and you score the distance between them. Collaborative filtering needs many users' data, so you could only simulate it by inventing several fake users. A good extension is a simple hybrid that blends an attribute-similarity score with a popularity or "similar users" score.
