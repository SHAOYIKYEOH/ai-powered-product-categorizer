CREATE OR REPLACE TABLE `raw_data.distinct_products` AS
WITH description_counts AS (
  SELECT 
    item_code,
    COUNT(DISTINCT item_description) AS desc_count,
    MAX(item_description) AS max_description
  FROM `raw_data.scr_pricehistory`
  WHERE item_description IS NOT NULL
  GROUP BY item_code
)
SELECT
  item_code,
  CASE 
    WHEN desc_count <= 2 THEN max_description
    ELSE item_code
  END AS item_description
FROM description_counts;
