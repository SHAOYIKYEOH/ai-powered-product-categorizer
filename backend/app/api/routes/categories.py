"""Category management endpoints"""

from fastapi import APIRouter, HTTPException
import logging

from app.api.models.category_schemas import (
    UploadCategoryRequest,
    UploadExamplesRequest,
    CategoryExample
)
from app.services.category_manager import CategoryManager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/categories/config")
async def set_categories(request: UploadCategoryRequest):
    """
    Set/update the category configuration for a customer
    
    Args:
        request: Category configuration with main and sub categories
    
    Returns:
        Confirmation with number of categories saved
    
    Example:
    ```json
    {
      "categories": {
        "main_categories": [
          {
            "name": "Office Equipment",
            "description": "Machines and devices",
            "sub_categories": [
              {"name": "Printers", "description": "Document printers"},
              {"name": "Scanners"}
            ]
          }
        ]
      }
    }
    ```
    """
    try:
        result = CategoryManager.set_categories(request.categories.model_dump())
        return result
    
    except Exception as e:
        logger.error(f"Error setting categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/config")
async def get_categories():
    """
    Get the current category configuration
    
    Returns:
        Current category configuration
    """
    try:
        categories = CategoryManager.get_categories()
        
        if not categories:
            raise HTTPException(status_code=404, detail="No categories configured yet")
        
        return categories
    
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list")
async def get_category_names():
    """
    Get simplified list of all main and sub category names
    
    Returns:
        Lists of category names for frontend dropdown menus
    
    Example:
    ```json
    {
      "main_categories": ["Office Equipment", "Furniture"],
      "sub_categories": ["Printers", "Scanners", "Chairs"]
    }
    ```
    """
    try:
        result = CategoryManager.get_category_names_list()
        return result
    
    except Exception as e:
        logger.error(f"Error getting category names: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/examples/add")
async def add_examples(request: UploadExamplesRequest):
    """
    Add training examples for product categories
    
    Args:
        request: List of category examples with product descriptions
    
    Returns:
        Confirmation with number of examples added
    
    Example:
    ```json
    {
      "examples": [
        {
          "product_description": "HP LaserJet Pro Printer",
          "main_category": "Office Equipment",
          "sub_category": "Printers",
          "reasoning": "It's a printer device"
        },
        {
          "product_description": "Samsung Flat Panel Monitor",
          "main_category": "IT Equipment",
          "sub_category": "Monitors",
          "confidence": 0.99
        }
      ]
    }
    ```
    """
    try:
        examples_data = [ex.model_dump() for ex in request.examples]
        result = CategoryManager.add_examples(examples_data)
        return result
    
    except Exception as e:
        logger.error(f"Error adding examples: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def get_examples(
    main_category: str = None,
    sub_category: str = None
):
    """
    Get training examples, optionally filtered by category
    
    Args:
        main_category: Optional filter by main category
        sub_category: Optional filter by sub category
    
    Returns:
        Dictionary of examples grouped by category
    
    Example:
    ```json
    {
      "Office Equipment::Printers": [
        {
          "product_description": "HP LaserJet Pro",
          "main_category": "Office Equipment",
          "sub_category": "Printers"
        }
      ]
    }
    ```
    """
    try:
        examples = CategoryManager.get_examples(main_category, sub_category)
        
        if not examples:
            return {"message": "No examples found for specified filters", "data": {}}
        
        return {"total": sum(len(v) for v in examples.values()), "data": examples}
    
    except Exception as e:
        logger.error(f"Error retrieving examples: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
