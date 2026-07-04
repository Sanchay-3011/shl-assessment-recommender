from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """Schema for service health check response."""
    status: Literal["ok"] = Field(default="ok", description="Service readiness status")

class ChatMessage(BaseModel):
    """Schema representing a single message in the conversation history."""
    role: Literal["user", "assistant", "system"] = Field(..., description="Sender role of the message")
    content: str = Field(..., min_length=1, description="Message text content")

class ChatRequest(BaseModel):
    """Schema for chat agent queries."""
    messages: List[ChatMessage] = Field(..., min_length=1, description="Sequential dialogue logs representing the conversation")

class RecommendationItem(BaseModel):
    """Schema for a recommended assessment from the official SHL catalog."""
    name: str = Field(..., description="Official name of the assessment")
    url: str = Field(..., description="Direct SHL catalog URL for the assessment")
    test_type: str = Field(..., description="Class of assessment (e.g. 'K' for Knowledge & Skills, 'P' for Personality)")
    description: Optional[str] = Field(None, description="Detailed description")
    duration: Optional[str] = Field(None, description="Duration text")
    adaptive: Optional[bool] = Field(None, description="Adaptive test flag")
    remote: Optional[bool] = Field(None, description="Remote proctoring flag")
    languages: Optional[List[str]] = Field(default_factory=list, description="Supported languages")
    job_levels: Optional[List[str]] = Field(default_factory=list, description="Target job levels")

class ChatResponse(BaseModel):
    """Schema representing the conversational agent response."""
    reply: str = Field(..., description="Natural language response text from the agent")
    recommendations: List[RecommendationItem] = Field(
        default_factory=list,
        description="Array of 1 to 10 recommended assessments when the agent has committed to a shortlist. Empty otherwise."
    )
    end_of_conversation: bool = Field(
        ...,
        description="Flag indicating if the recommendation loop is complete and conversation is finished"
    )

class PreprocessedDocument(BaseModel):
    """Schema representing a preprocessed and validated catalog item with derived fields."""
    entity_id: str = Field(..., description="The unique identifier of the assessment")
    name: str = Field(..., description="The official name of the assessment")
    link: str = Field(..., description="URL to the assessment detail page")
    job_levels: List[str] = Field(default_factory=list, description="Target job levels for the test")
    languages: List[str] = Field(default_factory=list, description="Supported languages")
    duration: str = Field(..., description="Raw text representing the test duration")
    remote: str = Field(..., description="Whether the test can be taken remotely ('yes' or 'no')")
    adaptive: str = Field(..., description="Whether the test is adaptive ('yes' or 'no')")
    description: str = Field(..., description="Brief description of the test")
    keys: List[str] = Field(default_factory=list, description="Categories or tags")

    # Derived fields
    duration_minutes: Optional[int] = Field(None, description="Derived integer test duration in minutes")
    normalized_name: str = Field(..., description="Lowercase, normalized representation of the test name")
    search_text: str = Field(..., description="Aggregated text string optimized for BM25 keyword search")
    embedding_text: str = Field(..., description="Enriched text template optimized for semantic representation")
    keyword_tokens: List[str] = Field(default_factory=list, description="Tokenized terms from the search text")

class ScoredDocument(BaseModel):
    """Typed container representing a retrieved document and its matching score."""
    document: PreprocessedDocument = Field(..., description="The matching catalog item")
    score: float = Field(..., description="The matching similarity or relevance score")
    reasoning: Optional[str] = Field(None, description="Internal explanation or mapping constraints for this match")

class HiringConstraints(BaseModel):
    """Structured hiring constraints extracted from user conversation history."""
    role: Optional[str] = Field(None, description="Extracted job role targeted for the assessment")
    skills: List[str] = Field(default_factory=list, description="Target skills/technologies mentioned")
    programming_languages: List[str] = Field(default_factory=list, description="Target programming languages")
    job_level: Optional[str] = Field(None, description="Hiring seniority job level")
    experience: Optional[str] = Field(None, description="Experience/tenure details")
    duration: Optional[int] = Field(None, description="Explicit test duration limit in minutes")
    language: Optional[str] = Field(None, description="Preferred language for the assessment")
    adaptive: Optional[str] = Field(None, description="Adaptive requirement ('yes' or 'no')")
    remote: Optional[str] = Field(None, description="Remote proctoring requirement ('yes' or 'no')")
    assessment_keys: List[str] = Field(default_factory=list, description="Assessment keys/types matched from the catalog keys schema")

class RetrievalQuery(BaseModel):
    """Structured query object for BM25 and FAISS indexing services."""
    query_text: str = Field(..., description="Raw text string optimized for keyword search")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-value filters to execute")

class ConversationContext(BaseModel):
    """Structured, single-source-of-truth object describing the processed conversation state."""
    current_intent: Literal[
        "recommend", "compare", "refine_previous_recommendation", "clarify", "greeting", "out_of_scope", "prompt_injection", "lookup"
    ] = Field(..., description="Classified intent of the current user message context")
    extracted_constraints: HiringConstraints = Field(..., description="Latest compiled hiring constraints state")
    constraint_history: List[HiringConstraints] = Field(default_factory=list, description="Chronological update log of constraints across turns")
    missing_constraints: List[str] = Field(default_factory=list, description="List of required constraints not yet provided by the user")
    needs_clarification: bool = Field(..., description="Whether the agent needs to ask for clarification before searching")
    clarification_question: Optional[str] = Field(None, description="Formulated clarification question text targeting the highest-priority missing slot")
    retrieval_query: Optional[RetrievalQuery] = Field(None, description="Structured query context to run retrieval, if ready")
    comparison_targets: List[str] = Field(default_factory=list, description="Extracted name targets to compare side-by-side")
    confidence_score: float = Field(..., description="Current confidence rating (0.0 to 1.0) derived from missing slots and search parameters")
    conversation_complete: bool = Field(..., description="Flag indicating if the recommendation loop is complete and ready to finish")
    refusal_reason: Optional[str] = Field(None, description="Explanation text for prompt injections or out of scope queries")
