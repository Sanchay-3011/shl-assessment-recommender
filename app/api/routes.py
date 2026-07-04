from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.recommendation_service import RecommendationService
from app.utils.logger import logger

# Initialize router with no global prefix to map endpoints directly at root level
router = APIRouter(tags=["conversational-recommender"])

# Global reference for caching RecommendationService
_recommendation_service = None

def get_recommendation_service() -> RecommendationService:
    """Dependency provider for retrieving the cached RecommendationService instance."""
    global _recommendation_service
    if _recommendation_service is None:
        logger.info("Initializing RecommendationService singleton in API routes...")
        _recommendation_service = RecommendationService()
    return _recommendation_service

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Health Check",
    description="Returns the status of the service readiness. Responds with status 'ok'."
)
def health_check() -> HealthResponse:
    """Endpoint for monitoring service status."""
    return HealthResponse(status="ok")

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent Chat Endpoint",
    description="Stateless endpoint processing conversation history to recommend assessments."
)
async def chat(
    payload: ChatRequest,
    service: RecommendationService = Depends(get_recommendation_service)
) -> ChatResponse:
    """Processes dialogue messages to output conversational responses."""
    try:
        logger.info(f"Received chat endpoint request with {len(payload.messages)} dialogue turns.")
        response = service.chat(payload.messages)
        return response
    except Exception as e:
        logger.error(f"Internal error processing chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the conversation history."
        )

@router.get(
    "/chat",
    status_code=status.HTTP_200_OK,
    summary="Chat API Status check",
    description="Provides status check endpoint reachable via GET."
)
def chat_status_check():
    """Returns endpoint info to ensure it is reachable via GET requests."""
    return {"status": "active", "message": "The chat endpoint is active and expects POST requests."}
