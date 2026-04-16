"""Data models for categories and examples"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SubCategory(BaseModel):
    """Sub category definition"""
    name: str = Field(..., description="Sub category name")
    description: Optional[str] = None


class MainCategory(BaseModel):
    """Main category with sub categories"""
    name: str = Field(..., description="Main category name")
    sub_categories: List[SubCategory] = Field(..., description="List of sub categories")
    description: Optional[str] = None


class CategoryConfig(BaseModel):
    """Full category configuration for a customer"""
    main_categories: List[MainCategory] = Field(..., description="List of main categories")


class CategoryExample(BaseModel):
    """Example product for a category"""
    product_description: str = Field(..., description="Product description/name")
    main_category: str = Field(..., description="Main category assignment")
    sub_category: str = Field(..., description="Sub category assignment")
    reasoning: Optional[str] = None
    confidence: Optional[float] = Field(default=1.0)


class CategoryExamples(BaseModel):
    """Collection of examples for a category"""
    main_category: str
    sub_category: str
    examples: List[str] = Field(..., description="List of product descriptions")


class UploadCategoryRequest(BaseModel):
    """Request to add category configuration"""
    categories: CategoryConfig


class UploadExamplesRequest(BaseModel):
    """Request to add examples"""
    examples: List[CategoryExample]
