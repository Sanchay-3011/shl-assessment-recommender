from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.logger import logger
from app.api.routes import router as api_router, get_recommendation_service
from app.models.schemas import HealthResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for handling FastAPI startup and shutdown lifecycle events."""
    logger.info("FastAPI service lifespan is initializing...")
    # Pre-load/Warm up the recommendation service and machine learning model
    try:
        service = get_recommendation_service()
        logger.info("Warm-up complete: Recommendation engines and model loaded successfully.")
    except Exception as e:
        logger.error(f"Lifespan startup failure during model preloading: {e}")
    
    yield
    
    logger.info("FastAPI service lifespan is shutting down...")

app = FastAPI(
    title="SHL Assessment Recommender API",
    description="Hybrid retrieval (BM25 & FAISS) with LLM reranking for assessment recommendations.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
import os
origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [orig.strip() for orig in origins_env.split(",") if orig.strip()]
if not allowed_origins:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

allow_all_origins = "*" in allowed_origins or (len(allowed_origins) == 1 and allowed_origins[0] == "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allowed_origins,
    allow_credentials=False if allow_all_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)
