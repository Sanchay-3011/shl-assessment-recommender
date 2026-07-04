# SHL Assessment Recommender: Engineering Approach Document

This document outlines the architectural patterns, key design decisions, retrieval methodologies, and evaluation strategies implemented for the SHL Assessment Recommender conversational platform.

---

## 1. Problem Understanding

Recruiters and hiring managers face difficulty navigating the large SHL assessment catalog (comprising thousands of specialized tests spanning ability, personality, and technical domains). Selecting the correct test requires aligning candidate characteristics (role, seniority, technologies) with test criteria (duration, language constraints, adaptivity).

The target system must act as an **intelligent, conversational candidate recommendation helper** that:
1. Translates loose recruiter conversations into structured search constraints.
2. Interacts over multiple turns to clarify ambiguous parameters.
3. Retrieves relevant tests from the catalog without inventing/hallucinating items.
4. Generates natural-language reasoning that remains 100% grounded in verified catalog data.

---

## 2. Architectural Design Decisions

To ensure a robust, production-quality solution, we established a strict separation of concerns, isolating intent tracking, execution policies, and retrieval logic from the LLM generation layer.

### A. Non-Autonomous LLM Policy (Deterministic Flow)
A common pitfall in AI agents is letting the LLM decide execution logic (e.g. routing to retrieval, asking clarifying questions, refusing out-of-scope inputs). This introduces non-deterministic execution loops and latency overhead. 

Instead, the **Agent Orchestrator** governs the flow:
* The **Conversation Engine** parses the chat history deterministically.
* The **Policy Engine** maps context to a strict policy: `GREETING`, `REFUSAL`, `PROMPT_INJECTION`, `CLARIFICATION`, `COMPARISON`, or `END_CONVERSATION`.
* The **Groq Provider** LLM is used **only at the final step** to translate structured data (retrieved shortlists, missing slots, or comparison lists) into natural language.

### B. Dynamic Vocabulary Building
To extract technologies and job roles without hardcoding dictionaries (which become stale as the catalog changes), the system parses the catalog on startup. It builds a dynamic **vocabulary index** representing all unique terms within catalog names, ensuring zero-config alignment with catalog updates.

---

## 3. Retrieval Subsystem & Hybrid Search

The system implements a multi-stage retrieval pipeline optimized for recall and precision:

```
                  [Recruiter Query + Filters]
                              |
              +---------------+---------------+
              |                               |
              v                               v
     [BM25 Keyword Index]            [FAISS Vector Index]
     (Handles exact terms            (Handles semantic intent
       & normalized names)             & descriptions)
              |                               |
              +---------------+---------------+
                              |
                              v
                [Reciprocal Rank Fusion (RRF)]
                              |
                              v
                 [Metadata Filter Validation]
                              |
                              v
                 [Recommendation Shortlist]
```

1. **BM25 Search**: Matches exact keywords and normalized item names, ensuring terms like `.NET` or `Python (New)` are retrieved directly.
2. **FAISS Search**: Leverages dense embeddings (`all-MiniLM-L6-v2`) to capture semantic intent, matching descriptive content when a recruiter uses terms like "database developer" instead of "SQL".
3. **Reciprocal Rank Fusion (RRF)**: Merges the ranked outputs of BM25 and FAISS:
   $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{60 + Rank_m(d)}$$
4. **Metadata Filters**: Applies strict constraints (languages, job levels, durations, and adaptivity) before RRF ranking, ensuring only valid candidate tests are evaluated.

---

## 4. Grounded Prompt Engineering & Hallucination Prevention

To satisfy the **strict zero-hallucination constraint** required in enterprise HR applications:
* **Grounded Prompts**: The `PromptManager` compiles templates loaded from `app/prompts/`. The LLM is explicitly instructed that the provided structured candidate sections represent the **only source of truth**.
* **Mismatched Link Detection**: The system never asks the LLM to generate links. Instead, the `ResponseValidator` parses the output JSON, verifies that recommended item names exist in the catalog, and attaches the **exact catalog URL** programmatically.
* **LLM Structure Validation**: The LLM outputs a structured JSON matching the `ChatResponse` schema. If parsing fails, the provider retries once.
* **Temperature Zero**: The LLM runs with `temperature=0` to ensure deterministic formatting and prevent creative hallucinations.

---

## 5. Automated E2E Evaluation Strategy

We designed an isolated **AI Evaluation Package** located in the `evaluation/` directory:
* **Gold Benchmark Dataset**: Includes 50 realistic dialogue scenarios covering software engineering, sales, leadership, graduate hires, empty retrievals, contradictions, jailbreak injections, and out-of-scope requests.
* **Spy Patching Hook**: Intercepts the orchestrator execution path to verify internal classifications (intent and policy) and intermediate retrieved shortlists without altering production endpoints.
* **Granular Quality Metrics**:
  * *Conversation*: Intent Accuracy, Policy Accuracy, Clarification Accuracy, Refinement Accuracy.
  * *Retrieval*: Recall@10, Precision@5, MRR (Mean Reciprocal Rank).
  * *Grounding*: Hallucination Rate, Invalid URL Rate, Grounding Success Rate.
  * *Response Format*: Completeness Rate, Latency percentiles (P50, P95, Max).

---

## 6. Trade-offs and Future Improvements

### Trade-offs
* **Strict Clarification**: The policy engine triggers a clarification query if job level or assessment objective keys are missing. While this guarantees accurate alignment, it can increase dialogue length for users wanting general catalog suggestions.
* **Local Embeddings**: Using `all-MiniLM-L6-v2` keeps indexing fast and runs offline without API cost, but its representation capability is lower than larger cloud-based embeddings.

### Future Improvements
1. **Multi-Turn Semantic Memory**: Track historical chat contexts using dense conversational memory rather than repeating constraint keyword scans.
2. **Dynamic Stop-Word Tuning**: Filter generic terms from the catalog's dynamic vocabulary compilation step to prevent false role matching.
3. **API Rate-Limiting**: Add token-bucket rate limiters on the FastAPI `/chat` endpoint to protect downstream LLM API limits.
