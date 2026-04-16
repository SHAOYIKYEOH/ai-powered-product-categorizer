"""CSV upload endpoint"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import logging
import re
import tempfile
from pathlib import Path
from typing import Optional

from app.services.bigquery_client import BigQueryClient
from app.services.category_manager import CategoryManager
from app.services.prompt_builder import PromptBuilder

router = APIRouter()
logger = logging.getLogger(__name__)

_VALID_COLUMN_NAME = re.compile(r'^[A-Za-z0-9_ ]+$')


def _escape_bq_string(s: str) -> str:
    """Escape a string for safe embedding inside a BigQuery single-quoted string literal."""
    return (s
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _validate_column_name(name: str, field: str) -> None:
    if not _VALID_COLUMN_NAME.match(name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field}: '{name}'. Only letters, numbers, underscores, and spaces are allowed."
        )


def _get_bq_client() -> BigQueryClient:
    try:
        return BigQueryClient()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to BigQuery: {str(e)}")


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    dataset_id: str = Form(...),
    table_id: str = Form(...),
    code_column: str = Form(default="Item_Code", description="CSV中的产品代码列名"),
    description_column: str = Form(default="Item_Description", description="CSV中的产品描述列名"),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Upload CSV and run classification pipeline with dynamic column mapping
    
    Args:
        file: CSV file upload
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID for raw data
        code_column: Column name for product code (e.g., "Item_Code", "SKU", "Product_ID")
        description_column: Column name for product description (e.g., "Item_Description", "Product Name")
        custom_prompt: Optional additional instructions for LLM
    
    Returns:
        Status and job information
    
    Example:
        POST /api/upload
        - file: data.csv
        - dataset_id: raw_data
        - table_id: scr_pricehistory
        - code_column: SKU
        - description_column: Product Name
    """
    temp_file_path = None

    # Validate user-supplied column names before any DB interaction
    _validate_column_name(code_column, "code_column")
    _validate_column_name(description_column, "description_column")

    bq_client = _get_bq_client()

    try:
        # Check if categories are configured
        categories = CategoryManager.get_categories()
        if not categories:
            raise HTTPException(
                status_code=400,
                detail="Categories not configured. Please set up categories first using POST /api/categories/config"
            )

        # Validate file
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")

        # Save uploaded file to temp location
        temp_dir = tempfile.mkdtemp()
        temp_file_path = Path(temp_dir) / file.filename

        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logger.info(f"Uploaded file saved to {temp_file_path}")
        logger.info(f"Column mapping - Code: '{code_column}', Description: '{description_column}'")

        # 1. Load CSV to BigQuery
        load_result = bq_client.load_csv_to_table(str(temp_file_path), dataset_id, table_id)
        logger.info(f"CSV loaded: {load_result}")

        project_id = bq_client.client.project

        # 2. Run cleaning query (deduplication) with dynamic column names
        cleaning_query = f"""
        CREATE OR REPLACE TABLE `{project_id}.{dataset_id}.distinct_products` AS
        WITH description_counts AS (
          SELECT
            LOWER(TRIM(`{code_column}`)) as item_code,
            COUNT(DISTINCT `{description_column}`) AS desc_count,
            MAX(`{description_column}`) AS max_description
          FROM `{project_id}.{dataset_id}.{table_id}`
          WHERE `{description_column}` IS NOT NULL
          GROUP BY `{code_column}`
        )
        SELECT
          item_code,
          CASE
            WHEN desc_count <= 2 THEN max_description
            ELSE item_code
          END AS item_description
        FROM description_counts;
        """

        bq_client.execute_query(cleaning_query, dataset_id=dataset_id)
        logger.info("Cleaning query executed (distinct_products created)")

        # 3. Build dynamic prompt from categories and examples.
        # Use a sentinel so we can split the prompt into prefix/suffix and
        # inject item_description as a real BigQuery column reference via CONCAT.
        _PLACEHOLDER = "__PRODUCT_DESCRIPTION__"
        try:
            dynamic_prompt = PromptBuilder.build_classification_prompt(
                product_description=_PLACEHOLDER,
                custom_prompt=custom_prompt,
                include_examples=True
            )
            logger.info("Dynamic prompt built successfully with customer categories and examples")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        parts = dynamic_prompt.split(_PLACEHOLDER, 1)
        prompt_prefix = _escape_bq_string(parts[0])
        prompt_suffix = _escape_bq_string(parts[1]) if len(parts) > 1 else ""

        # 4. Run classification query using BigQuery ML Gemini model
        classification_query = f"""
        CREATE OR REPLACE TABLE `{project_id}.{dataset_id}.categorized_products` AS
        WITH build_prompt AS (
          SELECT
            item_code,
            item_description,
            CONCAT('{prompt_prefix}', item_description, '{prompt_suffix}') AS prompt
          FROM `{project_id}.{dataset_id}.distinct_products`
        ),
        call_llm AS (
          SELECT
            item_code,
            item_description,
            JSON_EXTRACT_SCALAR(
              TO_JSON_STRING(ml_generate_text_result),
              '$.candidates[0].content.parts[0].text'
            ) AS llm_text
          FROM ML.GENERATE_TEXT(
            MODEL `{project_id}.{dataset_id}.gemini_model`,
            (SELECT item_code, item_description, prompt FROM build_prompt),
            STRUCT(0.0 AS temperature, 1000 AS max_output_tokens)
          )
        ),
        parsed AS (
          SELECT
            item_code,
            item_description,
            REGEXP_REPLACE(
              REGEXP_REPLACE(llm_text, r'^```json\\s*', ''),
              r'\\s*```$', ''
            ) AS clean_json
          FROM call_llm
          WHERE llm_text IS NOT NULL
        )
        SELECT
          item_code,
          item_description,
          JSON_EXTRACT_SCALAR(clean_json, '$.main_category') AS main_category,
          JSON_EXTRACT_SCALAR(clean_json, '$.sub_category') AS sub_category,
          SAFE_CAST(JSON_EXTRACT_SCALAR(clean_json, '$.confidence') AS FLOAT64) AS confidence,
          JSON_EXTRACT_SCALAR(clean_json, '$.reasoning') AS reasoning
        FROM parsed;
        """

        bq_client.execute_query(classification_query, dataset_id=dataset_id)
        logger.info("Classification query executed via BigQuery ML")

        return {
            "status": "success",
            "message": "CSV processed and classified successfully",
            "csv_loaded": load_result["rows_loaded"],
            "cleaning_status": "completed",
            "classification_status": "completed",
            "column_mapping": {
                "code_column": code_column,
                "description_column": description_column
            },
            "dataset_id": dataset_id,
            "table_id": table_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        if temp_file_path and Path(temp_file_path).exists():
            Path(temp_file_path).unlink()
