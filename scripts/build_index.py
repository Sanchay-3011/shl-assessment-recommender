import os
import sys
from dotenv import load_dotenv

# Add project root directory to the python path to resolve modules correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.utils.logger import logger
from app.services.recommendation_service import RecommendationService

def main() -> None:
    """Entry point for rebuilding FAISS indexes from the catalog."""
    logger.info("Starting index build script...")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Load service and force-rebuild the index files
        service = RecommendationService()
        logger.info("Executing rebuild_indexes command on RecommendationService...")
        service.rebuild_indexes()
        logger.info("Search indexes build process finished successfully!")
    except Exception as e:
        logger.error(f"Failed to build indexes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
