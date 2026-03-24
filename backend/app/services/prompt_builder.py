"""Dynamic prompt builder for LLM classification"""

import logging
from typing import Optional, List
from app.services.category_manager import CategoryManager

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Build dynamic prompts for product categorization"""
    
    @staticmethod
    def build_classification_prompt(
        product_description: str,
        custom_prompt: Optional[str] = None,
        include_examples: bool = True
    ) -> str:
        """
        Build a dynamic prompt for product classification
        
        Args:
            product_description: Product name/description to classify
            custom_prompt: Optional custom instructions from customer
            include_examples: Include training examples in prompt
        
        Returns:
            Complete prompt for LLM
        """
        
        categories_config = CategoryManager.get_categories()
        
        if not categories_config:
            raise ValueError("No category configuration found. Please set up categories first.")
        
        # Build main categories section
        main_categories_section = "**Main Categories (Choose ONE):**\n"
        main_cat_names = []
        
        for idx, main_cat in enumerate(categories_config.get('main_categories', []), 1):
            main_cat_names.append(main_cat['name'])
            desc = f" - {main_cat.get('description', '')}" if main_cat.get('description') else ""
            main_categories_section += f"{idx}. {main_cat['name']}{desc}\n"
        
        # Build sub categories section
        sub_categories_section = "**Sub Categories (Choose EXACT match):**\n"
        sub_cat_mapping = {}  # Map sub category to main category for validation
        
        for main_cat in categories_config.get('main_categories', []):
            for sub_cat in main_cat.get('sub_categories', []):
                sub_cat_name = sub_cat['name']
                sub_cat_mapping[sub_cat_name] = main_cat['name']
                desc = f" - {sub_cat.get('description', '')}" if sub_cat.get('description') else ""
                sub_categories_section += f"- {sub_cat_name}{desc}\n"
        
        # Build examples section
        examples_section = ""
        if include_examples:
            examples = CategoryManager.get_examples()
            if examples:
                examples_section += "\n**Examples of correct classifications:**\n"
                for idx, (key, example_list) in enumerate(examples.items(), 1):
                    if idx > 10:  # Limit to first 10 categories in prompt
                        break
                    main, sub = key.split("::")
                    if example_list:
                        first_example = example_list[0] if isinstance(example_list, list) else example_list
                        if isinstance(first_example, dict):
                            product = first_example.get('product_description', first_example)
                        else:
                            product = first_example
                        examples_section += f"- \"{product}\" → Main: {main}, Sub: {sub}\n"
        
        # Build final prompt
        prompt = f"""You are an expert B2B product taxonomist and data engineer. Your task is to classify product names/descriptions into a two-tier hierarchy.

{main_categories_section}

{sub_categories_section}
{examples_section}

**Critical Instructions:**
- You MUST respond ONLY with a valid JSON object
- Do not include markdown formatting like ```json
- Ensure main_category matches one from the list above
- Ensure sub_category matches one from the list above
- Assign a confidence score (0.0 to 1.0) for classification confidence
- Provide a brief 1-sentence reasoning

{f"**Additional Instructions from Customer:**{custom_prompt}" if custom_prompt else ""}

**Classify the following product:**
Product Description: {product_description}

**Expected JSON Output Format:**
{{
  "main_category": "Category Name",
  "sub_category": "Sub Category Name",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}}
"""
        
        logger.debug(f"Built prompt with {len(main_cat_names)} main categories")
        return prompt
    
    @staticmethod
    def build_batch_classification_prompt(
        products: List[str],
        custom_prompt: Optional[str] = None,
        include_examples: bool = True
    ) -> str:
        """
        Build a prompt for classifying multiple products at once
        
        Args:
            products: List of product descriptions
            custom_prompt: Optional custom instructions
            include_examples: Include training examples
        
        Returns:
            Complete prompt for batch classification
        """
        
        categories_config = CategoryManager.get_categories()
        
        if not categories_config:
            raise ValueError("No category configuration found. Please set up categories first.")
        
        # Build categories info (same as single product)
        main_categories_section = "**Main Categories (Choose ONE):**\n"
        for idx, main_cat in enumerate(categories_config.get('main_categories', []), 1):
            desc = f" - {main_cat.get('description', '')}" if main_cat.get('description') else ""
            main_categories_section += f"{idx}. {main_cat['name']}{desc}\n"
        
        sub_categories_section = "**Sub Categories (Choose EXACT match):**\n"
        for main_cat in categories_config.get('main_categories', []):
            for sub_cat in main_cat.get('sub_categories', []):
                sub_cat_name = sub_cat['name']
                desc = f" - {sub_cat.get('description', '')}" if sub_cat.get('description') else ""
                sub_categories_section += f"- {sub_cat_name}{desc}\n"
        
        # Build examples section
        examples_section = ""
        if include_examples:
            examples = CategoryManager.get_examples()
            if examples:
                examples_section += "\n**Examples:**\n"
                for idx, (key, example_list) in enumerate(examples.items(), 1):
                    if idx > 5:
                        break
                    main, sub = key.split("::")
                    if example_list:
                        first_example = example_list[0] if isinstance(example_list, list) else example_list
                        if isinstance(first_example, dict):
                            product = first_example.get('product_description', first_example)
                        else:
                            product = first_example
                        examples_section += f"- \"{product}\" → {main} / {sub}\n"
        
        # Format products list
        products_str = "\n".join([f"{i+1}. {prod}" for i, prod in enumerate(products)])
        
        prompt = f"""You are an expert B2B product taxonomist. Classify the following {len(products)} products.

{main_categories_section}

{sub_categories_section}
{examples_section}

**Instructions:**
- Respond with ONLY a valid JSON array
- No markdown, no code blocks
- Each product gets one classification
- Include confidence score for each

**Products to classify:**
{products_str}

**Expected JSON Format:**
[
  {{
    "product_description": "Product 1",
    "main_category": "Category Name",
    "sub_category": "Sub Category Name",
    "confidence": 0.95,
    "reasoning": "Brief explanation"
  }},
  ...
]
"""
        
        return prompt
