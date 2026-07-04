import os
import json
import pytest
from app.models.schemas import ChatMessage
from app.utils.preprocessing import CatalogPreprocessor
from app.retrieval.faiss_index import FAISSRetriever
from app.retrieval.semantic import SemanticRetriever
from app.llm.conversation_engine import ConversationEngine

def test_conversation_refinement_pipeline() -> None:
    """Verifies that retrieval results narrow down chronologically across refinement turns."""
    catalog_path = "data/shl_catelog.md"
    if not os.path.exists(catalog_path):
        pytest.skip("Production catalog not found for integration testing")
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()
        
    preprocessor = CatalogPreprocessor()
    processed_docs = preprocessor.parse_markdown_catalog(markdown_text)
    
    faiss_ret = FAISSRetriever()

    # Fit indexes
    faiss_ret.fit(processed_docs)

    hybrid = SemanticRetriever(faiss_ret)
    
    import re
    vocab = set()
    for doc in processed_docs:
        for word in re.findall(r'\b[A-Za-z0-9+#.-]+\b', doc.name):
            if len(word) > 1 and not word.isdigit():
                vocab.add(word.lower())
    engine = ConversationEngine(vocabulary=vocab)
    
    # Sequential conversation turns
    turns = [
        ChatMessage(role="user", content="Recommend Python assessments"),
        ChatMessage(role="user", content="Only adaptive"),
        ChatMessage(role="user", content="Under 50 minutes")
    ]
    
    # Step 1: Recommend Python assessments
    ctx1 = engine.process_conversation(turns[:1])
    assert ctx1.current_intent == "recommend"
    assert "Python" in ctx1.extracted_constraints.programming_languages
    res1 = hybrid.query(ctx1.retrieval_query.query_text, top_n=10, constraints=ctx1.extracted_constraints)
    assert len(res1) > 0
    
    # Step 2: Refine: Only adaptive
    ctx2 = engine.process_conversation(turns[:2])
    assert ctx2.current_intent == "refine_previous_recommendation"
    assert ctx2.extracted_constraints.adaptive == "yes"
    assert "Python" in ctx2.extracted_constraints.programming_languages
    res2 = hybrid.query(ctx2.retrieval_query.query_text, filters=ctx2.retrieval_query.filters, top_n=10, constraints=ctx2.extracted_constraints)
    
    # Step 3: Refine: Under 50 minutes
    ctx3 = engine.process_conversation(turns[:3])
    assert ctx3.current_intent == "refine_previous_recommendation"
    assert ctx3.extracted_constraints.duration == 50
    assert ctx3.extracted_constraints.adaptive == "yes"
    res3 = hybrid.query(ctx3.retrieval_query.query_text, filters=ctx3.retrieval_query.filters, top_n=10, constraints=ctx3.extracted_constraints)
    
    # The final results must satisfy the combined constraints
    for item in res3:
        assert item.document.adaptive.lower() == "yes"
        if item.document.duration_minutes is not None:
            assert item.document.duration_minutes <= 50
