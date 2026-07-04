import pytest
import os
import shutil
from typing import Dict, Any, List
from app.utils.preprocessing import CatalogPreprocessor
from app.models.schemas import PreprocessedDocument, ScoredDocument
from app.retrieval.faiss_index import FAISSRetriever
from app.retrieval.semantic import SemanticRetriever

# Sample test data simulating various edge cases in Markdown format
MOCK_RAW_CATALOG_MD = """
# Catalog

## Assessment 1: Python Aptitude Test

- **Entity ID:** 100
- **Name:** Python Aptitude Test
- **Link:** https://www.shl.com/python-aptitude
- **Categories/Keys:** Aptitude
- **Job Levels:** Entry-Level, Graduate
- **Languages:** English (USA), Spanish
- **Duration:** 30 minutes
- **Remote Testing Support:** yes
- **Adaptive/IRT:** no
- **Description:** Assess basic Python programming competency.

---

## Assessment 2: Machine Learning Advanced (New)

- **Entity ID:** 101
- **Name:** Machine Learning Advanced (New)
- **Link:** https://www.shl.com/ml-advanced
- **Categories/Keys:** Knowledge & Skills
- **Job Levels:** Mid-Professional
- **Languages:** English (USA)
- **Duration:** Variable
- **Remote Testing Support:** no
- **Adaptive/IRT:** yes
- **Description:** Assess senior ML engineering skillset.

---

## Assessment 3: Python Duplicate Test

- **Entity ID:** 100
- **Name:** Python Duplicate Test
- **Link:** https://www.shl.com/python-dup
- **Categories/Keys:** Aptitude
- **Job Levels:** Entry-Level
- **Languages:** English
- **Duration:** 15 minutes
- **Remote Testing Support:** yes
- **Adaptive/IRT:** no
- **Description:** Duplicate item description.

---

## Assessment 4: Missing Languages Assessment

- **Entity ID:** 102
- **Name:** Missing Languages Assessment
- **Link:** https://www.shl.com/missing-lang
- **Categories/Keys:** Personality
- **Job Levels:** Director
- **Languages:** Not specified
- **Duration:** 45 minutes
- **Remote Testing Support:** yes
- **Adaptive/IRT:** no
- **Description:** Test language missing schema parsing.

---

## Assessment 5: Corrupt Empty ID Test

- **Entity ID:** 
- **Name:** Corrupt Empty ID Test
- **Link:** https://www.shl.com/corrupt
- **Categories/Keys:** Not specified
- **Job Levels:** Entry-Level
- **Languages:** English
- **Duration:** 20 minutes
- **Remote Testing Support:** yes
- **Adaptive/IRT:** no
- **Description:** Corrupt item.

---

## Assessment 6: Missing Name

- **Entity ID:** 103
- **Name:** 
- **Link:** https://www.shl.com/no-name
- **Categories/Keys:** Not specified
- **Job Levels:** Entry-Level
- **Languages:** English
- **Duration:** 20 minutes
- **Remote Testing Support:** yes
- **Adaptive/IRT:** no
- **Description:** Corrupt item missing name.
"""

def test_preprocessor_validation_and_derivations() -> None:
    """Verifies preprocessor handles corrupt records, duplicates, and derives correctly."""
    preprocessor = CatalogPreprocessor()
    processed_docs = preprocessor.parse_markdown_catalog(MOCK_RAW_CATALOG_MD)

    # 1. Total records check:
    # 6 items -> 1 duplicate (entity_id 100), 1 empty ID corrupt, 1 missing name corrupt.
    # Should leave exactly 3 valid documents.
    assert len(processed_docs) == 3

    # 2. Check derived fields:
    doc_100 = next(d for d in processed_docs if d.entity_id == "100")
    doc_101 = next(d for d in processed_docs if d.entity_id == "101")
    doc_102 = next(d for d in processed_docs if d.entity_id == "102")

    # duration_minutes extraction checks
    assert doc_100.duration_minutes == 30
    assert doc_101.duration_minutes is None  # 'Variable' has no digits
    assert doc_102.duration_minutes == 45

    # normalized_name validation
    assert doc_100.normalized_name == "python aptitude test"
    assert doc_101.normalized_name == "machine learning advanced (new)"

    # languages fallback validation (missing languages maps to empty list)
    assert doc_102.languages == []

    # search_text normalized structure
    assert "adaptive-no" in doc_100.search_text
    assert "remote-no" in doc_101.search_text
    assert doc_100.normalized_name in doc_100.search_text

def test_retrieval_indexing_lifecycle() -> None:
    """Tests fitting, serializing, lazy-loading, and scoring on retrievers."""
    preprocessor = CatalogPreprocessor()
    processed_docs = preprocessor.parse_markdown_catalog(MOCK_RAW_CATALOG_MD)

    faiss_ret = FAISSRetriever()

    # Fit indexes
    faiss_ret.fit(processed_docs)

    test_indexes_dir = "indexes/test_builds"
    os.makedirs(test_indexes_dir, exist_ok=True)
    
    faiss_filepath = os.path.join(test_indexes_dir, "faiss.index")

    try:
        # Save indices
        faiss_ret.save(faiss_filepath)

        assert os.path.exists(faiss_filepath)
        assert os.path.exists(f"{faiss_filepath}.meta")

        # Reload indexes via new instance lazy loaders
        new_faiss = FAISSRetriever()

        new_faiss.load(faiss_filepath)

        # Confirm load states
        assert len(new_faiss.documents) == 3

        # Confirm query typed results
        faiss_res = new_faiss.query("Machine learning skillset", top_n=1)
        assert len(faiss_res) == 1
        assert isinstance(faiss_res[0], ScoredDocument)
        assert isinstance(faiss_res[0].document, PreprocessedDocument)

    finally:
        # Cleanup index directory
        if os.path.exists(test_indexes_dir):
            shutil.rmtree(test_indexes_dir)

def test_semantic_retrieval_with_metadata_filtering() -> None:
    """Verifies metadata filters are applied in SemanticRetriever."""
    preprocessor = CatalogPreprocessor()
    processed_docs = preprocessor.parse_markdown_catalog(MOCK_RAW_CATALOG_MD)

    faiss_ret = FAISSRetriever()
    faiss_ret.fit(processed_docs)

    hybrid = SemanticRetriever(faiss_ret)
    # Enable debug mode logs
    hybrid.debug_mode = True

    # 1. Test job_level soft ranking (seniority affinity, not hard filter)
    res_job = hybrid.query("Test", top_n=3, filters={"job_level": "Graduate"})
    # Job level uses seniority affinity ranking (not hard filter).
    # Document 100 (Entry-Level + Graduate) should be in the results.
    assert len(res_job) >= 1
    assert any(doc.document.entity_id == "100" for doc in res_job)

    # 2. Test filtering by language constraint
    res_lang = hybrid.query("Test", top_n=3, filters={"language": "Spanish"})
    # Document 100 has Spanish; Document 102 has no languages (treated as available).
    # At minimum, document 100 should be present with Spanish.
    assert len(res_lang) >= 1
    assert any(doc.document.entity_id == "100" for doc in res_lang)

    # 3. Test filtering by max duration constraint (ID 100 is 30m, ID 102 is 45m)
    res_dur = hybrid.query("Test", top_n=3, filters={"duration": 35})
    # ID 100 (30m) fits; ID 101 (None/Variable) is not hard-filtered; ID 102 (45m) is skipped
    assert len(res_dur) >= 1
    assert any(doc.document.entity_id == "100" for doc in res_dur)

    # 4. Test filtering by adaptive constraint
    res_ad = hybrid.query("Test", top_n=3, filters={"adaptive": "yes"})
    # Only ID 101 should match
    assert len(res_ad) == 1
    assert res_ad[0].document.entity_id == "101"

    # 5. Test filtering by remote constraint
    res_rem = hybrid.query("Test", top_n=3, filters={"remote": "no"})
    # Only ID 101 should match
    assert len(res_rem) == 1
    assert res_rem[0].document.entity_id == "101"

def test_retrieval_regression_queries() -> None:
    """Verifies that production queries produce distinct and correct top rankings."""
    from app.llm.conversation_engine import ConversationEngine
    from app.models.schemas import ChatMessage

    # Load actual production catalog
    catalog_path = "data/shl_assessment_catalog.md"
    if not os.path.exists(catalog_path):
        pytest.skip("Production catalog not found for integration testing")
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()
        
    preprocessor = CatalogPreprocessor()
    processed_docs = preprocessor.parse_markdown_catalog(markdown_text)
    
    faiss_ret = FAISSRetriever()
    faiss_ret.fit(processed_docs)
    hybrid = SemanticRetriever(faiss_ret)
    
    # Instantiate ConversationEngine with dynamic vocabulary matching RecommendationService
    import re
    vocab = set()
    for doc in processed_docs:
        for word in re.findall(r'\b[A-Za-z0-9+#.-]+\b', doc.name):
            if len(word) > 1 and not word.isdigit():
                vocab.add(word.lower())
    engine = ConversationEngine(vocabulary=vocab)
    
    # 1. Python Developer
    ctx = engine.process_conversation([ChatMessage(role="user", content="Entry-Level Python Developer")])
    res_py = hybrid.query(ctx.retrieval_query.query_text, top_n=5, constraints=ctx.extracted_constraints)
    assert len(res_py) > 0
    assert "python" in res_py[0].document.name.lower()
    
    # 2. Java Developer
    ctx = engine.process_conversation([ChatMessage(role="user", content="Entry-Level Java Developer")])
    res_java = hybrid.query(ctx.retrieval_query.query_text, top_n=5, constraints=ctx.extracted_constraints)
    assert len(res_java) > 0
    assert "java" in res_java[0].document.name.lower()
    
    # 3. React Developer
    ctx = engine.process_conversation([ChatMessage(role="user", content="Entry-Level React Developer")])
    res_react = hybrid.query(ctx.retrieval_query.query_text, top_n=5, constraints=ctx.extracted_constraints)
    assert len(res_react) > 0
    assert "react" in res_react[0].document.name.lower()
    
    # 4. Sales Executive
    ctx = engine.process_conversation([ChatMessage(role="user", content="Sales Executive")])
    res_sales = hybrid.query(ctx.retrieval_query.query_text, top_n=5, constraints=ctx.extracted_constraints)
    assert len(res_sales) > 0
    assert any("sales" in r.document.name.lower() for r in res_sales)
    
    # 5. Customer Support
    ctx = engine.process_conversation([ChatMessage(role="user", content="Customer Support")])
    res_support = hybrid.query(ctx.retrieval_query.query_text, top_n=5, constraints=ctx.extracted_constraints)
    assert len(res_support) > 0
    assert any(any(k in r.document.name.lower() for k in ["customer", "support", "service", "writex", "serv"]) for r in res_support)
    
    # 6. Leadership Hiring
    ctx = engine.process_conversation([ChatMessage(role="user", content="Leadership Hiring")])
    res_lead = hybrid.query(ctx.retrieval_query.query_text, top_n=5, constraints=ctx.extracted_constraints)
    assert len(res_lead) > 0
    assert any(any(k in r.document.name.lower() for k in ["leadership", "manager", "director", "executive", "lead"]) for r in res_lead)

    # Verify that the top recommendations are distinct from each other
    top_sales_name = next((r.document.name for r in res_sales if "sales" in r.document.name.lower()), res_sales[0].document.name)
    top_support_name = next((r.document.name for r in res_support if any(k in r.document.name.lower() for k in ["customer", "support", "service", "writex", "serv"])), res_support[0].document.name)
    top_names = {
        "Python": res_py[0].document.name,
        "Java": res_java[0].document.name,
        "React": res_react[0].document.name,
        "Sales": top_sales_name,
        "Support": top_support_name,
        "Leadership": res_lead[0].document.name
    }
    # Ensure they are distinct
    assert len(set(top_names.values())) == 6


def test_retrieval_extended_regression_suite() -> None:
    """Verifies that all 21 regression recruiter queries retrieve valid and relevant assessments."""
    import os
    from app.utils.preprocessing import CatalogPreprocessor
    from app.retrieval.faiss_index import FAISSRetriever
    from app.retrieval.semantic import SemanticRetriever
    from app.llm.conversation_engine import ConversationEngine
    from app.models.schemas import ChatMessage

    # Load actual production catalog
    catalog_path = "data/shl_assessment_catalog.md"
    if not os.path.exists(catalog_path):
        pytest.skip("Production catalog not found for integration testing")
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()
        
    preprocessor = CatalogPreprocessor()
    processed_docs = preprocessor.parse_markdown_catalog(markdown_text)
    
    faiss_ret = FAISSRetriever()
    faiss_ret.fit(processed_docs)
    hybrid = SemanticRetriever(faiss_ret)
    
    import re
    vocab = set()
    for doc in processed_docs:
        for word in re.findall(r'\b[A-Za-z0-9+#.-]+\b', doc.name):
            if len(word) > 1 and not word.isdigit():
                vocab.add(word.lower())
    engine = ConversationEngine(vocabulary=vocab)

    queries = [
        ("Python Developer", ["python"]),
        ("Java Developer", ["java"]),
        ("React Developer", ["react"]),
        ("Node.js Developer", ["node", "javascript", "react", "html", "web"]),
        ("Data Scientist", ["data", "statistic", "numerical"]),
        ("Machine Learning Engineer", ["machine learning", "python", "inductive reasoning", "numerical"]),
        ("Sales Executive", ["sales"]),
        ("Business Development", ["sales", "negotiation", "business development"]),
        ("Customer Support", ["customer", "support", "service", "writex"]),
        ("Call Center", ["call", "center", "phone", "customer", "support"]),
        ("Leadership Hiring", ["leadership", "manager", "director", "executive"]),
        ("Graduate Hiring", ["graduate", "verify", "ability", "numerical", "verbal", "inductive", "checking"]),
        ("Finance Analyst", ["finance", "financial", "accounting", "numerical"]),
        ("Healthcare", ["medical", "nursing", "healthcare", "verify"]),
        ("Rust Engineer", ["rust", "coding", "logic", "software"]),
        ("Backend Java", ["java", "backend"]),
        ("Full Stack Engineer", ["full stack", "javascript", "java", "software"]),
        ("DevOps Engineer", ["devops", "cloud", "linux", "docker"]),
        ("AWS Engineer", ["aws", "cloud", "amazon"]),
        ("Docker", ["docker", "cloud", "linux"]),
        ("Cloud Engineer", ["cloud", "aws", "azure"])
    ]

    for user_query, expected_keywords in queries:
        ctx = engine.process_conversation([ChatMessage(role="user", content=user_query)])
        
        # If the engine decided to clarify, test the retriever directly using the user query text
        if ctx.retrieval_query is None:
            query_text = user_query
            filters = {}
        else:
            query_text = ctx.retrieval_query.query_text
            filters = ctx.retrieval_query.filters
            
        res = hybrid.query(query_text, filters=filters, top_n=10, constraints=ctx.extracted_constraints)
        assert len(res) > 0, f"Query '{user_query}' returned zero matches."
        
        # Verify that at least one of the top 10 matches contains one of the expected keywords (case-insensitive)
        matched = False
        top_10_names = [r.document.name.lower() for r in res]
        top_10_descs = [r.document.description.lower() for r in res]
        top_10_keys = [str(r.document.keys).lower() for r in res]
        
        for keyword in expected_keywords:
            for name, desc, keys in zip(top_10_names, top_10_descs, top_10_keys):
                if keyword in name or keyword in desc or keyword in keys:
                    matched = True
                    break
            if matched:
                break
        assert matched, f"None of the top 10 recommendations for query '{user_query}' matched expected keywords {expected_keywords}. Top recommendation names: {[r.document.name for r in res]}"


def test_debug_mode_disabled_by_default() -> None:
    """Verifies that DEBUG_RETRIEVAL is false by default in SemanticRetriever initialization."""
    from app.retrieval.faiss_index import FAISSRetriever
    from app.retrieval.semantic import SemanticRetriever
    import os

    # Backup env if exists
    orig_env = os.environ.get("DEBUG_RETRIEVAL")
    if "DEBUG_RETRIEVAL" in os.environ:
        del os.environ["DEBUG_RETRIEVAL"]

    try:
        faiss_ret = FAISSRetriever()
        hybrid = SemanticRetriever(faiss_ret)
        assert hybrid.debug_mode is False
    finally:
        if orig_env is not None:
            os.environ["DEBUG_RETRIEVAL"] = orig_env


