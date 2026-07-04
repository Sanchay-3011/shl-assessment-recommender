import re
from typing import List, Set
from app.models.schemas import ScoredDocument, HiringConstraints

def _extract_tech_token(name: str) -> str:
    """Extracts the primary technology token from an assessment name.
    
    Uses the first significant word (before any parenthetical qualifiers)
    as a fingerprint for diversity grouping. Examples:
      'Java EE' → 'java'
      'Python (New)' → 'python'
      'Core Java (Advanced Level) (New)' → 'core'
      'JavaScript (New)' → 'javascript'
    """
    cleaned = re.sub(r'\(.*?\)', '', name).strip().lower()
    words = cleaned.split()
    if not words:
        return name.lower()
    # Skip generic prefixes to find the meaningful tech token
    skip_words = {"core", "advanced", "entry", "level", "basic", "fundamentals",
                  "professional", "general", "new", "ms", "microsoft"}
    for w in words:
        if w not in skip_words:
            return w
    return words[0]

class RecommendationSelector:
    """Selects, validates, deduplicates, and limits candidate search matches into a clean shortlist."""

    def select_shortlist(
        self, candidates: List[ScoredDocument], constraints: HiringConstraints
    ) -> List[ScoredDocument]:
        """Deduplicates, validates schema attributes, applies MMR diversity, caps to 10 items, and attaches retrieval reasoning."""
        seen_ids = set()
        valid_candidates = []

        for doc in candidates:
            # 1. Deduplicate by entity_id
            if doc.document.entity_id in seen_ids:
                continue
            seen_ids.add(doc.document.entity_id)

            # 2. Validate essential fields exist
            if not doc.document.name or not doc.document.link:
                continue
                
            valid_candidates.append(doc)

        # 3. Apply Two-Tier Diversity Penalty (MMR-style)
        shortlist: List[ScoredDocument] = []
        selected_tech_tokens: Set[str] = set()
        selected_keys: Set[str] = set()
        diverse_entity_ids: Set[str] = set()
        
        # Enforce a minimum semantic similarity score threshold.
        # This prevents returning completely irrelevant assessments just to pad the list to 10.
        SCORE_THRESHOLD = 0.25
        
        while valid_candidates and len(shortlist) < 10:
            # Sort remaining valid_candidates by their score (which may have been penalized)
            valid_candidates.sort(key=lambda x: x.score, reverse=True)
            
            # Pick the top candidate
            best_doc = valid_candidates.pop(0)
            
            # If the best remaining candidate is below threshold, stop filling the shortlist.
            if best_doc.score < SCORE_THRESHOLD:
                break
            
            doc_keys = [k.lower() for k in best_doc.document.keys]
            doc_tech = _extract_tech_token(best_doc.document.name)
            
            # Track if it was picked primarily because of diversity
            if selected_keys or selected_tech_tokens:
                is_diverse_key = not any(k in selected_keys for k in doc_keys) if selected_keys else True
                is_diverse_tech = doc_tech not in selected_tech_tokens if selected_tech_tokens else True
                if not is_diverse_key and not is_diverse_tech:
                    pass  # Not diverse at all
                else:
                    diverse_entity_ids.add(best_doc.document.entity_id)
            
            shortlist.append(best_doc)
            
            for k in doc_keys:
                selected_keys.add(k)
            selected_tech_tokens.add(doc_tech)
                
            # Apply two-tier diversity penalty to remaining candidates
            for remaining in valid_candidates:
                rem_keys = [k.lower() for k in remaining.document.keys]
                rem_tech = _extract_tech_token(remaining.document.name)
                
                shares_key = any(k in selected_keys for k in rem_keys)
                shares_tech = rem_tech in selected_tech_tokens
                
                if shares_tech and shares_key:
                    # Same technology AND same category — very similar, mild penalty instead of strong
                    remaining.score *= 0.85
                elif shares_tech:
                    # Same technology, different category — lighter penalty
                    remaining.score *= 0.90
                elif shares_key:
                    # Different technology, same category — barely noticeable penalty
                    remaining.score *= 0.95

        # 4. Attach retrieval reasoning matching constraints and scores
        for doc in shortlist:
            matches = []
            if constraints.role and (
                constraints.role.lower() in doc.document.name.lower() or
                constraints.role.lower() in doc.document.description.lower()
            ):
                matches.append(f"role '{constraints.role}'")
                
            if constraints.job_level:
                if constraints.job_level in doc.document.job_levels:
                    matches.append(f"exact job level '{constraints.job_level}'")
                else:
                    matches.append(f"job level fallback to '{', '.join(doc.document.job_levels)}'")
                    
            if constraints.language and any(constraints.language.lower() in l.lower() for l in doc.document.languages):
                matches.append(f"language '{constraints.language}'")
            if constraints.duration is not None and doc.document.duration_minutes is not None:
                matches.append(f"duration <= {constraints.duration}m")

            match_reason = "general relevance" if not matches else ", ".join(matches)
            diversity_note = " (Included to provide assessment diversity)" if doc.document.entity_id in diverse_entity_ids and len(shortlist) > 1 else ""
            
            doc.reasoning = f"Matched constraints: {match_reason}{diversity_note} | Retrieval score: {doc.score:.4f}"

        return shortlist
