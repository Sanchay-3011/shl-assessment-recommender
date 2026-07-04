# Approach Document

## 1. Design Choices & Retrieval Setup
Our architecture relies on an agentic orchestration layer (`AgentOrchestrator`) that handles conversational state management and constraints extraction before routing queries to the retrieval engine. We intentionally kept the retrieval setup strictly modular to allow for clean isolation of duties.

**Initial Approach (What Didn't Work):**
Initially, we used a Reciprocal Rank Fusion (RRF) approach combining a keyword-based BM25 index and a semantic FAISS index. The retrieval heavily relied on metadata boosting—specifically penalizing results that lacked specific tags (like "Entry-Level"). 
This approach suffered from several major flaws:
1. **Generic Word Bleeding**: The word "Programming" in a Python Developer query caused "C++ Programming" or "Visual Basic" to mistakenly surge to the top of the ranks, shielding them from language penalization logic.
2. **Over-Indexing on Metadata**: Using RRF alongside aggressive metadata rules caused "Automata Selenium" and "MS Access" (which possessed the "Entry-Level" tag) to consistently outrank "Python (New)" (which lacked the tag), directly defying semantic common sense.

**Final Approach (FAISS-Only + Scalar Adjustments):**
To resolve the ranking complexity, we migrated to a **FAISS-only semantic retrieval architecture**.
- **Semantic Foundation:** FAISS intrinsically understands the distinction between "Python" and "C++", solving keyword crossover problems. 
- **Scalar Metadata Boosting:** Instead of using hard RRF ranks, we now use the original FAISS cosine similarity score as a base. We apply a mild **20% scalar boost** to results where the job level explicitly matches the user's request. This ensures that a strong semantic match (e.g., Python) will remain at the top even if it lacks a specific metadata tag, while otherwise equally ranked results will properly separate based on seniority.
- **Competing Language Penalty:** We aggressively penalize (90% score reduction) explicitly competing languages if they are found within the target assessment's metadata and are not part of the user's requested languages.

## 2. Intent Classification, Quote Matching & Segment Extraction
We implemented an intent routing classifier (Recommendation, Refine, Greeting, Comparison, Lookup).
During testing, we resolved two critical edge cases:
1. **Intent Priority Swap**: Queries starting with "What is the difference between..." were incorrectly routed to `lookup` due to the "What is the" prefix. We resolved this by prioritizing `compare` intent checks before `lookup` checks.
2. **Quote & Segment Extraction**: We enhanced comparison target extraction by matching single/smart quotes (e.g., `'Python (New)'`). Additionally, if no quotes are used, we split queries on separator patterns (like `between X and Y`, `X vs Y`, `compare X and Y`) and clean trailing words (like *assessments*, *test*). This extracts compound names (e.g., `"OPQ Leadership Report"`) instead of splitting them into single words, which previously matched incorrect catalog entries.

## 3. Grounding & Deterministic Fallback Tables
To satisfy zero-hallucination constraints:
- **Response Validation**: Every LLM response is checked against the catalog dataset. Hallucinated recommendations are dropped.
- **Fail-Safe Shortlist Grounding**: If the LLM output fails validation or if the API key is missing/inactive, the system falls back to a deterministic path: recommendations are populated directly from the retrieved shortlist cards.
- **Deterministic Comparison Tables**: For comparison queries, if the LLM fails or is missing an API key, the system automatically builds a detailed side-by-side markdown table comparing durations, formats, languages, and descriptions directly from catalog metadata.

## 4. Deployment & Infrastructure Connection
We deployed the frontend to Vercel and the backend to Railway. We resolved cross-origin blocks and connection failures using:
- **Forced Wildcard CORS**: Allowing all origins (`*`) by default on the backend to support any Vercel dynamic preview/branch subdomain (preventing browser CORS blocking).
- **Runtime Hostname Detection**: Automatically routing API calls to the Railway backend if the browser hostname is not localhost.
- **Fallback Router Prefixes**: Mounting the API router at `/`, `/api`, and `/api/v1` to prevent `404` errors from misconfigured frontend variables.

## 5. Evaluation Approach & AI Tools
We utilized an automated offline evaluation script (`benchmark_runner.py`) using a curated JSON dataset of 40+ user queries simulating real-world scenarios.
- **Recall@10**: This was our primary North Star metric. We tracked how often the ideal assessment appeared in the top 10 results.
- **AI Tool Usage**: Google's agentic coding system (Antigravity) was used to refactor retrieval pipelines, diagnose keyword-bleeding, rapidly iterate on prompt design, and implement fallback layers.
