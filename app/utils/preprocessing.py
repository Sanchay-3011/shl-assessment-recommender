import re
import time
from typing import Any, Dict, List, Optional, Set
from app.utils.logger import logger
from app.models.schemas import PreprocessedDocument

def clean_text(text: str) -> str:
    """Cleans text by lowercasing, removing punctuation, and collapsing whitespace.

    Args:
        text: Raw input text.

    Returns:
        Cleaned string.
    """
    if not text:
        return ""
    text = text.lower()
    # Keep alphanumeric, spaces, and hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text: str) -> List[str]:
    """Tokenizes cleaned text into a list of word tokens.

    Args:
        text: Raw input text.

    Returns:
        List of tokenized words.
    """
    cleaned = clean_text(text)
    tokens = [t for t in cleaned.split(" ") if t]
    return tokens

class CatalogPreprocessor:
    """Production-grade pipeline to preprocess and validate catalog records."""

    def __init__(self) -> None:
        self.seen_ids: Set[str] = set()

    def parse_duration_minutes(self, duration_str: str) -> Optional[int]:
        """Parses integer minutes from duration strings like '30 minutes' or 'max 20'."""
        if not duration_str:
            return None
        
        val = duration_str.lower().strip()
        if "variable" in val:
            return None

        # Extract first contiguous sequence of digits
        match = re.search(r'\d+', val)
        if match:
            return int(match.group())
        return None

    def normalize_name(self, name: str) -> str:
        """Standardizes name field to lowercase and removes excessive whitespaces."""
        if not name:
            return ""
        return re.sub(r'\s+', ' ', name.strip()).lower()

    def build_search_text(self, doc: Dict[str, Any], normalized_name: str) -> str:
        """Aggregates all relevant schema fields into a search string for BM25 keyword matching."""
        name = doc.get("name") or ""
        description = doc.get("description") or ""
        
        # Safe extraction of list attributes
        keys_str = " ".join(doc.get("keys") or [])
        job_levels_str = " ".join(doc.get("job_levels") or [])
        languages_str = " ".join(doc.get("languages") or [])
        
        duration = doc.get("duration") or ""
        adaptive = f"adaptive-{doc.get('adaptive') or ''}"
        remote = f"remote-{doc.get('remote') or ''}"

        parts = [
            name, 
            normalized_name, 
            description, 
            keys_str, 
            job_levels_str, 
            languages_str, 
            duration, 
            adaptive, 
            remote
        ]
        return " ".join([p for p in parts if p]).strip().lower()

    def build_embedding_text(self, doc: Dict[str, Any]) -> str:
        """Formats catalog fields into an enriched textual representation for dense embeddings."""
        name = doc.get("name") or ""
        description = doc.get("description") or ""
        keys_str = ", ".join(doc.get("keys") or [])
        job_levels_str = ", ".join(doc.get("job_levels") or [])
        languages_str = ", ".join(doc.get("languages") or [])

        return f"Assessment: {name}. Description: {description}. Keywords: {keys_str}. Job Levels: {job_levels_str}. Languages: {languages_str}.".strip()

    def parse_markdown_catalog(self, markdown_text: str) -> List[PreprocessedDocument]:
        """Parses raw markdown text into PreprocessedDocument chunks."""
        logger.info("Initializing markdown preprocessing pipeline...")
        start_time = time.perf_counter()
        
        self.seen_ids.clear()
        valid_records: List[PreprocessedDocument] = []
        
        # Split by the markdown separator
        chunks = markdown_text.split("---")
        
        for chunk in chunks:
            chunk = chunk.strip()
            if "## Assessment" in chunk:
                chunk = chunk[chunk.find("## Assessment"):]
            if not chunk.startswith("## Assessment"):
                continue
                
            # Extract fields using regex
            entity_id_match = re.search(r"- \*\*Entity ID:\*\* (.*)", chunk)
            name_match = re.search(r"- \*\*Name:\*\* (.*)", chunk)
            link_match = re.search(r"- \*\*Link:\*\* (.*)", chunk)
            keys_match = re.search(r"- \*\*Categories/Keys:\*\* (.*)", chunk)
            levels_match = re.search(r"- \*\*Job Levels:\*\* (.*)", chunk)
            langs_match = re.search(r"- \*\*Languages:\*\* (.*)", chunk)
            duration_match = re.search(r"- \*\*Duration:\*\* (.*)", chunk)
            remote_match = re.search(r"- \*\*Remote Testing Support:\*\* (.*)", chunk)
            adaptive_match = re.search(r"- \*\*Adaptive/IRT:\*\* (.*)", chunk)
            desc_match = re.search(r"- \*\*Description:\*\* (.*)", chunk)
            
            if not (entity_id_match and name_match):
                continue
                
            entity_id = entity_id_match.group(1).strip()
            name = name_match.group(1).strip()
            
            if not entity_id or not name:
                continue
            
            if entity_id in self.seen_ids:
                continue
            self.seen_ids.add(entity_id)
            
            # Helper to parse lists
            def parse_list(match_obj):
                if not match_obj: return []
                val = match_obj.group(1).strip()
                if val == "Not specified": return []
                return [x.strip() for x in val.split(",") if x.strip()]
            
            keys = parse_list(keys_match)
            job_levels = parse_list(levels_match)
            languages = parse_list(langs_match)
            
            duration_str = duration_match.group(1).strip() if duration_match else ""
            if duration_str == "Not specified": duration_str = ""
            
            remote_str = remote_match.group(1).strip() if remote_match else "no"
            adaptive_str = adaptive_match.group(1).strip() if adaptive_match else "no"
            
            desc_str = desc_match.group(1).strip() if desc_match else ""
            if desc_str == "Not specified": desc_str = ""
            
            normalized_name = self.normalize_name(name)
            duration_minutes = self.parse_duration_minutes(duration_str)
            
            # Mock a doc dict for build_search_text
            doc_dict = {
                "name": name,
                "description": desc_str,
                "keys": keys,
                "job_levels": job_levels,
                "languages": languages,
                "duration": duration_str,
                "remote": remote_str,
                "adaptive": adaptive_str
            }
            search_text = self.build_search_text(doc_dict, normalized_name)
            keyword_tokens = tokenize(search_text)
            
            valid_records.append(PreprocessedDocument(
                entity_id=entity_id,
                name=name,
                link=link_match.group(1).strip() if link_match else "",
                job_levels=job_levels,
                languages=languages,
                duration=duration_str,
                remote=remote_str,
                adaptive=adaptive_str,
                description=desc_str,
                keys=keys,
                duration_minutes=duration_minutes,
                normalized_name=normalized_name,
                search_text=search_text,
                embedding_text=chunk, # The raw markdown chunk itself
                keyword_tokens=keyword_tokens
            ))
            
        duration = time.perf_counter() - start_time
        logger.info(f"Preprocessing timing: {duration:.4f} seconds | Processed: {len(valid_records)} chunks.")
        return valid_records
