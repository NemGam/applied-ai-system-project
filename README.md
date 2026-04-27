# Vibe Flow


## Project Summary
This is an extention of Project 3, Music Recommender.

This project is an AI-assisted music recommender that matches songs to user preferences using structured metadata, lyric retrieval, and optional Gemini-powered parsing, reranking, and explanations grounded with retrieved lyric snippets. It matters because it shows how a small, explainable recommendation system can combine deterministic scoring with hybrid RAG-style and LLM features while still remaining understandable and testable.

---

### Architecture Overview
![System Diagram](/assets/System_Diagram.png)


The system starts with a user request from the frontend, which the FastAPI backend processes as either manual preferences or natural-language input. That input is converted into structured preferences, then a retriever searches the local catalog using metadata and lyrics to narrow the candidate set and extract short lyric snippets when they are relevant. The deterministic recommender scores and ranks those candidates, and optional Gemini steps can rerank the top results and generate explanations using the retrieved song metadata plus lyric snippets as grounding context. The final recommendations are then returned to the frontend for display.

### Data Flow

1. The user submits either manual song preferences or a natural-language music request.
2. The backend converts that input into structured preference fields like genre, mood, context, and numeric targets.
3. The retriever searches the local song catalog using song metadata and lyrics to build a candidate set and select short matching lyric snippets.
4. The recommender scores those candidates using weighted feature matching and a small diversity reranking step.
5. If enabled, Gemini can rerank the top candidates and generate explanation text using the retrieved metadata and lyric snippets as grounding context.
6. The system returns the final recommendations, scores, retrieval details, and explanations to the frontend.

### Human and Testing Checks

- Human-authored data is part of the system: the song metadata, mood tags, contexts, and lyrics files were manually created and directly affect retrieval and ranking quality.
- Human review is part of evaluation: sample outputs, screenshots, the model card, and reflection notes are used to inspect whether recommendations make sense.
- Automated testing is included through `pytest` to check parser behavior, retrieval quality, lyric snippet grounding, ranking behavior, reranking fallbacks, lyrics access, and adversarial input handling.

### Interactions examples
"I want some chill music for studying"
![alt text](assets/ex1.png)

"Maybe some rock music?"
![alt text](assets/ex2.png)

Guardrail example
![alt text](assets/ex3.png)

## Setup Instructions

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure Gemini for natural-language parsing:

   - Copy `.env.example` to `.env` if needed
   - Set `GEMINI_API_KEY`
   - Optionally override `GEMINI_MODEL` (default: `gemini-2.0-flash`)
   - `GEMINI_RERANKING_ENABLED=true` for better contextual reranking
   - Optionally tune `GEMINI_RERANK_TOP_N` to control how many top deterministic results are sent for reranking
   - Leave `GEMINI_EXPLANATIONS_ENABLED=false` unless you explicitly want an extra Gemini call for explanation text

   Example `.env`:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   GEMINI_RERANKING_ENABLED=true
   GEMINI_RERANK_TOP_N=8
   GEMINI_EXPLANATIONS_ENABLED=true
   ```

   By default, the backend uses Gemini only for natural-language parsing. If reranking is enabled, it adds one Gemini call to reorder the top deterministic candidates, and if explanations are also enabled, that adds one more Gemini call. The number of Gemini calls does not increase when lyric grounding is enabled; the rerank and explanation prompts just include retrieved lyric snippets when they are available. If `GEMINI_API_KEY` is missing, it falls back to local heuristic parsing, deterministic ranking, and heuristic explanations.

4. Run the backend API:

   ```bash
   uvicorn backend.main:app --reload
   ```

5. Run the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. Open the app:

   ```bash
   http://127.0.0.1:5173
   ```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `backend/tests/test_recommender.py`.

### How the App Is Tested

The app is tested primarily with `pytest` on the backend. These tests cover the deterministic recommender, metadata and lyrics retrieval, lyric snippet grounding in Gemini prompts, Gemini fallback behavior, reranking validation, explanation fallbacks, lyrics endpoints, adversarial inputs, and out-of-scope request handling.

In addition to automated tests, I also checked the app manually through the frontend by submitting different prompts and preference combinations to confirm that the recommendations, explanations, and error states matched the intended behavior. This combination of automated checks and manual review helped verify both code correctness and user-facing behavior.

---

## Design Decisions

I built this system as a hybrid of deterministic recommendation logic and optional Gemini features because I wanted the core ranking to stay explainable and reliable even when the LLM is unavailable. Retrieval from metadata and lyrics was added to make natural-language requests more useful without giving the model full control over the recommendations, and the current version also passes short retrieved lyric snippets into Gemini reranking and explanation prompts so those steps are better grounded in the retrieved evidence. The main trade-off is that this design is easier to understand and test, but it is less flexible and less intelligent than a larger end-to-end learned recommender with real user behavior data.

---

## Testing Summary

The strongest parts of the system were the deterministic ranking, metadata and lyrics retrieval, the lyric-grounded Gemini prompts, and the fallback logic when Gemini features were disabled or failed. What did not work as well was handling sparse or partial preference inputs, since users who gave fewer signals could still end up with weaker scores, and Gemini-based features could sometimes fall back to heuristic behavior when the response was invalid or unavailable. The main thing I learned is that testing AI systems is not just about whether the code runs, but whether the outputs stay consistent, explainable, and robust when inputs are vague, incomplete, or off-topic.

---

## Limitations and Risks

- The catalog is very small at 100 songs, so niche requests can lead to repeated artists or genres.
- Many song labels are hand-authored, so mood, popularity, and listening context reflect my judgment rather than real listener data.
- The deterministic recommender still does not understand full lyrical meaning, language, cultural context, or real listening history; the Gemini steps only see short retrieved lyric snippets rather than full songs.
- Users with partial preference inputs can be under-scored because the scoring system works best when more preference fields are filled in.

---

## Demo

![demo video](assets/Demo.mp4)

## Reflection


**What are the limitations or biases in your system?**
- The main limitations in this system are the small local catalog, hand-authored metadata, and scoring behavior that can still underweight sparse preference inputs. That means some genres, moods, or request styles are represented better than others, and the recommendations reflect the assumptions built into the dataset.

**Could your AI be misused, and how would you prevent that?**
- This system could be misused if someone treated it like a general-purpose assistant or a real commercial recommender. I reduced that risk by keeping it limited to a local music catalog, adding deterministic fallbacks, and adding an out-of-scope guardrail for clearly non-music requests.

**What surprised you while testing your AI's reliability?**
- What surprised me most was how often the system could appear to work even when the AI-assisted parts silently fell back to heuristic behavior. That made it clear that testing AI is not just about whether the app returns an answer, but whether it returns the kind of answer you think it is returning.

**Describe your collaboration with AI during this project. Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.**
- My collaboration with AI was useful, but it still needed supervision. One helpful suggestion was using retrieval over both metadata and lyrics and then passing short lyric snippets into later Gemini steps, because that made natural-language requests more meaningful and made the explanation layer more grounded. One flawed suggestion was trusting AI-generated outputs too quickly without checking whether the backend had actually fallen back to heuristic parsing or explanations, which led to behavior that looked smarter than it really was until I verified it more carefully.

[**Model Card**](model_card.md)

---
