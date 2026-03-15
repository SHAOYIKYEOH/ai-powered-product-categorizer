-- 1. Create the Remote Model Connection
CREATE OR REPLACE MODEL `raw_data.gemini_model`
REMOTE WITH CONNECTION `projects/YOUR_PROJECT_ID/locations/us/connections/llm_connection`
OPTIONS(endpoint = 'gemini-2.0-flash');


-- 2. Process and Categorize Products
CREATE OR REPLACE TABLE `raw_data.categorized_products` AS

WITH build_prompt AS (
  SELECT
    item_code,
    item_description,
    CONCAT(
      'You are an expert B2B product taxonomist and data engineer. Your task is to classify product names/descriptions into a two-tier hierarchy: a broad "Main Category" (for business analysis) and a specific "Sub Category" (used by the official website).\n\n',
      
      '**Tier 1: Main Categories (Choose ONLY ONE for high-level analysis):**\n',
      '1. Office Equipment\n',
      '2. Security & Access Control\n',
      '3. IT, Retail & POS\n',
      '4. Office Supplies & Consumables\n',
      '5. Furniture\n',
      '6. Others/Uncategorized\n\n',
      
      '**Tier 2: Sub Categories (Choose ONLY ONE exact match from this list):**\n',
      'Time Attendance System, Finger Print System, Face Recognition Time Recorder, Time Recorder, Guard Tour System, Bank Note Counter, Safety Box, Paper Shredder, Door Access System, Walkie Talkie, Smart Digital Lock, Laminator Machine, Binding Machine, Time Stamping Machine, Coin Counter Machine, Bank Note Detector, Trimmers & Guillotines, White Board & Notice Board, Office Furniture, Electronic Whiteboard, Cheque Writer Machine, Type Writer Machine, Barcode Scanner, CCTV, Air Purifier, Office Accessories, Cash Register Machine, Fax Machine, Keyphone System, Labeling Machine, Plastic ID Card Printer, Projector, Projection Screen, POS System, Paper Driller, Perforator Machine, Hole Puncher, Stapler, Steel Furniture, Monitor, Printing Calculator, Health Care Product, Uncategorized\n\n',
      
      '**Instructions & Mapping Guidelines:**\n',
      '- "CHUBB FIRE RESISTANCE FILLING CABINET" -> Main: Security & Access Control, Sub: Safety Box.\n',
      '- "VALUESCAN Mix Count Note Counting Machine" -> Main: IT, Retail & POS, Sub: Bank Note Counter.\n',
      '- "AMANO PR600 WATCHMAN CLOCK" -> Main: Security & Access Control, Sub: Guard Tour System.\n',
      '- Spare parts (batteries, ribbons) should go to Main: Office Supplies & Consumables, Sub: Office Accessories.\n\n',
      '- Only classify as "Binding Machine" if the product IS the machine itself, not supplies for it.\n',
      '- Only classify as "Time Recorder" if the product IS the machine, not ribbons/cards/accessories for it.\n',
      '- Any consumable, refill, replacement part, or supply FOR a machine -> Main: Office Supplies & Consumables, Sub: Office Accessories.\n',
      
      
      'CRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object. Do not include markdown formatting like ```json.\n\n',
      
      'Classify the following product:\n',
      'Product Description: ', item_description, '\n\n',
      
      'Expected JSON Output Format:\n',
      '{\n',
      '  "main_category": "Selected Tier 1 Category Name",\n',
      '  "sub_category": "Selected Tier 2 Category Name",\n',
      '  "confidence": 0.95,\n',
      '  "reasoning": "A brief 1-sentence explanation"\n',
      '}'
    ) AS full_prompt
  FROM `raw_data.distinct_products`
  WHERE item_description IS NOT NULL
  --LIMIT 5 -- Remove after testing
),

call_llm AS (
  SELECT
    item_code,
    item_description,
    REPLACE(
      REPLACE(
        JSON_EXTRACT_SCALAR(ml_generate_text_result, '$.candidates[0].content.parts[0].text'),
        '```json\n', ''
      ),
    '```', '') AS raw_json_response
  FROM ML.GENERATE_TEXT(
    MODEL `raw_data.gemini_model`,
    (SELECT item_code, item_description, full_prompt AS prompt FROM build_prompt),
    STRUCT(
      0.0 AS temperature,
      1000 AS max_output_tokens
    )
  )
)

SELECT
  item_code,
  item_description,
  JSON_EXTRACT_SCALAR(raw_json_response, '$.main_category') AS main_category,
  JSON_EXTRACT_SCALAR(raw_json_response, '$.sub_category') AS sub_category,
  CAST(JSON_EXTRACT_SCALAR(raw_json_response, '$.confidence') AS FLOAT64) AS confidence,
  JSON_EXTRACT_SCALAR(raw_json_response, '$.reasoning') AS reasoning
FROM call_llm;
