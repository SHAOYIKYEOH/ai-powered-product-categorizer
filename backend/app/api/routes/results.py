"""Results retrieval endpoint"""

from fastapi import APIRouter, HTTPException
import logging

from app.services.bigquery_client import BigQueryClient

router = APIRouter()
logger = logging.getLogger(__name__)

bq_client = BigQueryClient()

GET_RESULTS_QUERY = """
SELECT
  item_code,
  item_description,
  main_category,
  sub_category,
  confidence,
  reasoning
FROM `{project_id}.{dataset_id}.categorized_products`
ORDER BY confidence DESC
LIMIT {limit}
"""


@router.get("/results")
async def get_results(
    dataset_id: str,
    limit: int = 100
):
    """
    Retrieve categorized products
    
    Args:
        dataset_id: BigQuery dataset ID
        limit: Maximum number of results to return
    
    Returns:
        List of categorized products with confidence scores
    """
    try:
        project_id = bq_client.client.project
        
        query = GET_RESULTS_QUERY.format(
            project_id=project_id,
            dataset_id=dataset_id,
            limit=limit
        )
        
        results = bq_client.execute_query(query, dataset_id=dataset_id)
        
        return {
            "status": "success",
            "total_results": len(results),
            "data": results
        }
    
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/summary")
async def get_results_summary(dataset_id: str):
    """
    Get summary statistics of categorization results
    
    Args:
        dataset_id: BigQuery dataset ID
    
    Returns:
        Summary with counts by category and average confidence
    """
    try:
        summary_query = """
        SELECT
          main_category,
          sub_category,
          COUNT(*) as count,
          ROUND(AVG(confidence), 4) as avg_confidence,
          MIN(confidence) as min_confidence,
          MAX(confidence) as max_confidence
        FROM `{project_id}.{dataset_id}.categorized_products`
        GROUP BY main_category, sub_category
        ORDER BY count DESC
        """
        
        project_id = bq_client.client.project
        query = summary_query.format(project_id=project_id, dataset_id=dataset_id)
        
        results = bq_client.execute_query(query, dataset_id=dataset_id)
        
        total_count = sum(r['count'] for r in results)
        
        return {
            "status": "success",
            "total_products": total_count,
            "categories_count": len(results),
            "summary_by_category": results
        }
    
    except Exception as e:
        logger.error(f"Error retrieving results summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
