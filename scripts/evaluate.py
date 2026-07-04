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
    """Evaluates the retrieval quality of the RecommendationService against test cases."""
    logger.info("Starting evaluation script...")
    
    # Load environment variables
    load_dotenv()
    
    try:
        service = RecommendationService()
    except Exception as e:
        logger.error(f"Failed to initialize RecommendationService: {e}")
        sys.exit(1)

    # Test cases: tuples of (query, expected_assessment_id)
    test_cases = [
        (".NET Framework 4.5 environment diagnostics", "3827"),
        ("Model View Controller MVC dotnet security routing", "4094"),
        ("Adobe Photoshop cc layers selection painting", "3778"),
        ("Agile software testing methodology processes", "4159"),
        ("Amazon Web Services AWS development logging scalability", "4028")
    ]

    total_queries = len(test_cases)
    matched_in_top_5 = 0
    reciprocal_ranks = []

    logger.info(f"Running evaluation against {total_queries} test cases...")

    for query, expected_id in test_cases:
        logger.info(f"Evaluating query: '{query}' | Expected ID: {expected_id}")
        
        # Get recommendations
        recommendations = service.get_recommendations(query=query, limit=5)
        
        # Calculate evaluation metrics
        found_rank = -1
        for index, recommendation in enumerate(recommendations):
            rec_id = recommendation.get("entity_id") or recommendation.get("id")
            if rec_id == expected_id:
                found_rank = index + 1
                break

        if found_rank != -1:
            matched_in_top_5 += 1
            rr = 1.0 / found_rank
            reciprocal_ranks.append(rr)
            logger.info(f"-> SUCCESS: Found at rank {found_rank}")
        else:
            reciprocal_ranks.append(0.0)
            logger.warning("-> FAILURE: Expected item was not retrieved in top 5 results.")

    # Calculate final metrics
    precision_at_5 = (matched_in_top_5 / total_queries) if total_queries else 0.0
    mean_reciprocal_rank = (sum(reciprocal_ranks) / total_queries) if total_queries else 0.0

    logger.info("=========================================")
    logger.info("   EVALUATION RESULTS                    ")
    logger.info("=========================================")
    logger.info(f"Queries Tested: {total_queries}")
    logger.info(f"Precision@5:    {precision_at_5:.2%}")
    logger.info(f"MRR:            {mean_reciprocal_rank:.4f}")
    logger.info("=========================================")

if __name__ == "__main__":
    main()
