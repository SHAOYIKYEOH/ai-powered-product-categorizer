"""Service for managing categories and examples"""

import json
import logging
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# In-memory storage (replace with database for production)
categories_store = {}
examples_store = {}


class CategoryManager:
    """Manage customer category configurations and examples"""
    
    CATEGORIES_FILE = Path(__file__).parent.parent.parent / "data" / "categories.json"
    EXAMPLES_FILE = Path(__file__).parent.parent.parent / "data" / "examples.json"
    
    @classmethod
    def set_categories(cls, categories_config: dict) -> dict:
        """Store category configuration"""
        try:
            global categories_store
            categories_store = categories_config
            
            # Save to file
            cls.CATEGORIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CATEGORIES_FILE, 'w') as f:
                json.dump(categories_config, f, indent=2)
            
            logger.info(f"Categories saved: {len(categories_config.get('main_categories', []))} main categories")
            return {"status": "success", "categories_saved": len(categories_config.get('main_categories', []))}
        
        except Exception as e:
            logger.error(f"Failed to save categories: {str(e)}")
            raise
    
    @classmethod
    def get_categories(cls) -> Optional[dict]:
        """Retrieve category configuration"""
        global categories_store
        
        # Try to load from memory first
        if categories_store:
            return categories_store
        
        # Try to load from file
        try:
            if cls.CATEGORIES_FILE.exists():
                with open(cls.CATEGORIES_FILE, 'r') as f:
                    categories_store = json.load(f)
                    return categories_store
        except Exception as e:
            logger.error(f"Failed to load categories: {str(e)}")
        
        return None
    
    @classmethod
    def add_examples(cls, examples: List[dict]) -> dict:
        """Add training examples for categories"""
        try:
            global examples_store
            
            for example in examples:
                key = f"{example['main_category']}::{example['sub_category']}"
                if key not in examples_store:
                    examples_store[key] = []
                examples_store[key].append(example)
            
            # Save to file
            cls.EXAMPLES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.EXAMPLES_FILE, 'w') as f:
                json.dump(examples_store, f, indent=2)
            
            logger.info(f"Saved {len(examples)} examples")
            return {"status": "success", "examples_added": len(examples)}
        
        except Exception as e:
            logger.error(f"Failed to save examples: {str(e)}")
            raise
    
    @classmethod
    def get_examples(cls, main_category: Optional[str] = None, sub_category: Optional[str] = None) -> dict:
        """Retrieve examples, optionally filtered by category"""
        global examples_store
        
        # Try to load from memory first
        if not examples_store:
            # Try to load from file
            try:
                if cls.EXAMPLES_FILE.exists():
                    with open(cls.EXAMPLES_FILE, 'r') as f:
                        examples_store = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load examples: {str(e)}")
                return {}
        
        if not main_category:
            return examples_store
        
        # Filter by category
        filtered = {}
        if sub_category:
            key = f"{main_category}::{sub_category}"
            if key in examples_store:
                filtered[key] = examples_store[key]
        else:
            # Get all subcategories for a main category
            for key, value in examples_store.items():
                if key.startswith(f"{main_category}::"):
                    filtered[key] = value
        
        return filtered
    
    @classmethod
    def get_category_names_list(cls) -> dict:
        """Get list of all main and sub category names"""
        categories = cls.get_categories()
        if not categories:
            return {"main_categories": [], "sub_categories": []}
        
        main_list = []
        sub_list = set()
        
        for main_cat in categories.get('main_categories', []):
            main_list.append(main_cat['name'])
            for sub_cat in main_cat.get('sub_categories', []):
                sub_list.add(sub_cat['name'])
        
        return {
            "main_categories": main_list,
            "sub_categories": list(sub_list)
        }
