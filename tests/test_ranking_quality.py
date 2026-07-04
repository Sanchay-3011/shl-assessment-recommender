import pytest
from app.retrieval.semantic import SemanticRetriever
from app.retrieval.faiss_index import FAISSRetriever
from app.models.schemas import PreprocessedDocument, ScoredDocument, HiringConstraints

@pytest.fixture
def retriever():
    faiss = FAISSRetriever()
    
    def make_doc(entity_id, name, description, keys, job_levels):
        return PreprocessedDocument(
            entity_id=entity_id,
            name=name,
            description=description,
            keys=keys,
            job_levels=job_levels,
            languages=["English"],
            link=f"http://example.com/{entity_id}",
            duration="10 mins",
            remote="yes",
            adaptive="no",
            normalized_name=name.lower(),
            search_text=f"{name} {description}".lower(),
            embedding_text=f"{name} {description}".lower(),
            keyword_tokens=[name.lower(), description.lower(), "developer"]
        )
        
    # Mocking some corpus data
    docs = [
        make_doc("1", "Python (New)", "Python programming.", ["Programming"], ["Entry-Level"]),
        make_doc("2", "C# (New)", "C# programming.", ["Programming"], ["Entry-Level"]),
        make_doc("3", "SQL (New)", "SQL database.", ["Programming"], ["Entry-Level"]),
        make_doc("4", "Core Java", "Java entry level.", ["Programming"], ["Entry-Level"]),
        make_doc("5", "Java EE", "Advanced Java.", ["Programming"], ["Mid-Professional"]),
        make_doc("6", "React (New)", "React frontend.", ["Programming"], ["Entry-Level"]),
        make_doc("7", "Customer Support Scenario", "Support.", ["Support"], ["Entry-Level"]),
        make_doc("8", "Sales Aptitude", "Sales.", ["Sales"], ["Entry-Level"]),
        make_doc("9", "Leadership Potential", "Leadership.", ["Leadership"], ["Executive"]),
        make_doc("10", "Java Frameworks", "Mid level Java frameworks.", ["Programming"], ["Mid-Professional"]),
    ]
    sem_retriever = SemanticRetriever(faiss)
    sem_retriever.fit(docs)
    return sem_retriever

def test_python_retrieval_drift(retriever):
    constraints = HiringConstraints(
        role="developer",
        job_level="Entry-Level",
        programming_languages=["Python"]
    )
    results = retriever.query("I want to hire an entry-level Python developer", top_n=5, constraints=constraints)
    
    # Python should be ranked above C# and SQL
    ranks = {doc.document.name: i for i, doc in enumerate(results)}
    assert "Python (New)" in ranks
    if "C# (New)" in ranks:
        assert ranks["Python (New)"] < ranks["C# (New)"]
    if "SQL (New)" in ranks:
        assert ranks["Python (New)"] < ranks["SQL (New)"]

def test_seniority_ranking_java(retriever):
    constraints = HiringConstraints(
        role="developer",
        job_level="Entry-Level",
        programming_languages=["Java"]
    )
    results = retriever.query("Entry-level Java developer", top_n=5, constraints=constraints)
    
    # Core Java (Entry-Level) should outrank Java EE (Mid-Professional)
    ranks = {doc.document.name: i for i, doc in enumerate(results)}
    assert "Core Java" in ranks
    if "Java EE" in ranks:
        assert ranks["Core Java"] < ranks["Java EE"]
    if "Java Frameworks" in ranks:
        assert ranks["Core Java"] < ranks["Java Frameworks"]

def test_sales_filtering(retriever):
    constraints = HiringConstraints(
        role="sales executive"
    )
    results = retriever.query("Sales Executive", top_n=5, constraints=constraints)
    
    ranks = {doc.document.name: i for i, doc in enumerate(results)}
    assert "Sales Aptitude" in ranks
    assert ranks["Sales Aptitude"] == 0

def test_customer_support_filtering(retriever):
    constraints = HiringConstraints(
        role="customer support"
    )
    results = retriever.query("Customer Support", top_n=5, constraints=constraints)
    
    ranks = {doc.document.name: i for i, doc in enumerate(results)}
    assert "Customer Support Scenario" in ranks
    assert ranks["Customer Support Scenario"] == 0

def test_react_filtering(retriever):
    constraints = HiringConstraints(
        role="developer",
        programming_languages=["React"]
    )
    results = retriever.query("React Developer", top_n=5, constraints=constraints)
    
    ranks = {doc.document.name: i for i, doc in enumerate(results)}
    assert "React (New)" in ranks

def test_leadership_hiring(retriever):
    constraints = HiringConstraints(
        role="director",
        job_level="Executive"
    )
    results = retriever.query("Leadership Hiring", top_n=5, constraints=constraints)
    
    ranks = {doc.document.name: i for i, doc in enumerate(results)}
    assert "Leadership Potential" in ranks
