# Model Card: VibeFlow 1.0

## 1. Goal
VibeFlow is a classroom-scale music recommendation system for a local catalog. It is built to be explainable and testable, not production-ready.

It supports structured preferences and natural-language requests. The AI-assisted path can parse requests, retrieve songs from metadata and lyrics, rank them deterministically, optionally use Gemini for reranking and explanations, and in the agent flow ask for one clarification when the request is too vague.

## 2. Data Used
The catalog contains 100 songs in `backend/data/songs.csv`.

Each song includes music features and synthetic metadata such as `genre`, `mood`, `tempo_bpm`, `valence`, `danceability`, `acousticness`, `vocal_presence`, `instrumental_focus`, `listening_context`, and `replay_value`.

The system also uses local lyric files in `backend/lyrics`.

All song names, lyrics, and associated attributes are synthetic and Gemini-generated for this project. The system does not use real listening history, collaborative filtering data, or live external music databases.

## 3. System Summary
1. The user submits manual preferences or a natural-language request.
2. Gemini parses natural-language input when available, with heuristic fallback otherwise.
3. The retriever finds candidates using metadata and lyrics.
4. The deterministic recommender scores and ranks the candidates.
5. The system can ask for one clarification in the agent-style endpoint when the request is low-signal.
6. Gemini can optionally rerank top results and generate explanations.
7. If Gemini fails or is disabled, the system falls back to deterministic ranking and heuristic explanations.

The AI endpoint also includes an out-of-scope guardrail for clearly non-music requests.

## 4. Observed Behavior and Biases
The system performs best when the user gives several clear signals, such as genre, mood, context, or target energy.

Main limitations and biases:
- Users with sparse inputs can still be under-scored.
- The catalog is small and uneven across genres and moods.
- Retrieval depends heavily on word overlap in metadata and lyrics.
- The synthetic metadata and lyrics reflect project design choices, not real listener behavior.

## 5. Evaluation
Evaluation was done through manual inspection and automated tests.

Automated tests cover:
- deterministic ranking
- metadata and lyric retrieval
- Gemini fallback behavior
- reranking and explanation validation
- taste-profile personalization
- lyrics endpoint behavior
- clarification flow
- adversarial inputs
- out-of-scope handling

## 6. Intended Use
Intended use:
- classroom demonstration of recommendation concepts
- small-scale AI pipeline experimentation
- explainability and testing practice

Not intended for:
- production recommendation
- real personal listening histories
- high-stakes decisions
- general-purpose assistant use

## 7. Safety and Reliability Notes
This system does not include full moderation, but it does include:
- structured Gemini parsing targets
- deterministic fallback when Gemini fails
- candidate validation during reranking
- heuristic explanation fallback
- an out-of-scope music guardrail

## 8. Future Work
- improve scoring for sparse preference inputs
- expand the catalog
- use stronger retrieval than keyword overlap alone
- learn feature weights from user feedback
- improve domain detection and user-facing errors

## 9. Reflection
This project reinforced that useful AI systems often come from combining simpler pieces instead of relying on one model call. The most important lesson was that fallbacks, testing, and explainability matter as much as model capability.
