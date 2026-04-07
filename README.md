# AI-Powered Product Categorizer

## What This Project Does

An AI-powered REST API pipeline that automatically classifies products into a two-tier category hierarchy using **Google Gemini** via **BigQuery ML**.

Upload any CSV — including raw sales transaction data — define your own categories, and the system does the rest: returning a main category, sub-category, confidence score, and reasoning for each unique product.

---

## The Problem

Small and mid-size businesses often have a significant amount of sales and demographic data, but their **digital transformation** is still limited. Much of the data is incomplete or unstructured. For example, many products are not categorized. As a result, it is difficult to analyze business performance.

One of the most common pain points is **uncategorized product data**. Businesses may have years of sales transaction records, but no way to quickly understand which categories drive the most revenue.

This project solves that. Upload your raw sales transaction CSV (messy data is fine), and the pipeline classifies it using AI — returning a clean, categorized product list.

---

## Demo

This repo uses a **restaurant menu** as the sample dataset to demonstrate the pipeline.

| Item Code | Item Name | Main Category | Sub Category | Confidence |
|---|---|---|---|---|
| MAIN005 | Grilled Ribeye Steak 300g | Main Course | Grilled & Roasted | 98% |
| BEV002 | Cappuccino | Beverages | Hot Drinks | 100% |
| DES004 | Vanilla Ice Cream 2 Scoops | Desserts | Ice Cream & Frozen | 100% |
| APP002 | Tom Yum Seafood Soup | Appetizers | Soups | 98% |
| SIDE007 | BBQ Sauce | Sides | Sauces & Dips | 100% |

Sample data: [`data/input/sample_menu.csv`](data/input/sample_menu.csv)

---

## How We Handle Messy Data

Real business data is rarely clean. A raw sales transaction CSV might have 50,000 rows where the same product appears hundreds of times with slightly different descriptions, or a single item code was reused inconsistently across years.

The pipeline handles this automatically before any AI classification happens:

**1. Flexible column mapping** — your CSV headers don't need to follow any naming convention. You have to tell the API which column is the product code and which is the description.

**2. Deduplication** — the pipeline groups all rows by product code and counts how many distinct descriptions exist per code:
- If a code has **1–2 description variations** (e.g. `"Ribeye Steak"` and `"Ribeye Steak 300g"`), it picks the best one and sends it to the AI
- If a code has **3+ wildly different descriptions** (a sign the code was reused for unrelated products), it flags it honestly — the AI will return Uncategorized with a low confidence score

**3. Normalization** — codes and descriptions are trimmed and lowercased before deduplication, so `"REPAIR NOTE"`, `"Repair Note"`, and `"  repair note  "` are treated as the same description

The result: thousands of rows of raw sales data → a few hundred unique products → each one classified by AI.

---

## How It Works

1. **Configure your categories** — POST your category taxonomy (main + sub categories) to the API
2. **Upload your CSV** — specify which columns are the item code and item description (any header names work)
3. **Pipeline runs automatically:**
   - Loads CSV into BigQuery
   - Deduplicates products (one description per item code)
   - Builds a dynamic prompt from your category config
   - Calls Gemini via `ML.GENERATE_TEXT` for each product
   - Parses and stores the JSON response
4. **Fetch results** — GET the classified products with confidence scores and reasoning

### Architecture

```
CSV Upload → BigQuery (raw table)
           → distinct_products (deduplicated)
           → ML.GENERATE_TEXT (Gemini)
           → categorized_products (final output)
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/categories/config` | Set your category taxonomy |
| GET | `/api/categories/config` | Get current categories |
| GET | `/api/categories/list` | Get flat list of category names |
| POST | `/api/examples/add` | Add few-shot examples to improve accuracy |
| GET | `/api/examples` | Get current examples |
| POST | `/api/upload` | Upload CSV and run classification pipeline |
| GET | `/api/results` | Get classified products |
| GET | `/api/results/summary` | Get summary by category |

Interactive docs available at `http://localhost:8000/docs` after starting the server.

---

## Setup

### Prerequisites
- Python 3.9+
- Google Cloud project with BigQuery enabled
- BigQuery ML remote model connected to Vertex AI (Gemini)

### 1. Create a BigQuery ML Gemini model

```sql
CREATE OR REPLACE MODEL `your_project.your_dataset.gemini_model`
  REMOTE WITH CONNECTION `your_project.your_region.your_connection`
  OPTIONS (ENDPOINT = 'gemini-1.5-flash');
```

### 2. Configure environment

```bash
cd backend
cp .env.example .env
# Edit .env with your GCP project details
```

### 3. Install dependencies and run

```bash
pip install -r requirements.txt
python main.py
```

Server starts at `http://localhost:8000`.

---

## Quick Start Example

**1. Set categories:**
```bash
curl -X POST http://localhost:8000/api/categories/config \
  -H "Content-Type: application/json" \
  -d '{
    "categories": {
      "main_categories": [
        {
          "name": "Appetizers",
          "description": "Starters and small bites",
          "sub_categories": [
            {"name": "Soups"},
            {"name": "Salads"},
            {"name": "Finger Food"}
          ]
        },
        {
          "name": "Beverages",
          "description": "Drinks both hot and cold",
          "sub_categories": [
            {"name": "Hot Drinks"},
            {"name": "Cold Drinks"},
            {"name": "Alcoholic"}
          ]
        }
      ]
    }
  }'
```

**2. Upload and classify:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@data/input/sample_menu.csv" \
  -F "dataset_id=your_dataset" \
  -F "table_id=menu_items" \
  -F "code_column=Item Code" \
  -F "description_column=Item Name"
```

**3. Get results:**
```bash
curl "http://localhost:8000/api/results?dataset_id=your_dataset"
```

---

## Project Structure

```
├── data/
│   ├── input/
│   │   └── sample_menu.csv      # Sample restaurant menu dataset
│   └── output/
│       └── categorized_menu.csv # Classified output
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Environment settings
│   ├── requirements.txt
│   └── app/
│       ├── api/
│       │   ├── routes/
│       │   │   ├── upload.py    # CSV upload & classification pipeline
│       │   │   ├── categories.py
│       │   │   └── results.py
│       │   └── models/
│       │       └── category_schemas.py
│       └── services/
│           ├── bigquery_client.py
│           ├── category_manager.py
│           └── prompt_builder.py  # Builds dynamic LLM prompts
```

---

## Stack

- **Backend:** Python / FastAPI
- **Data Warehouse:** Google BigQuery
- **AI Model:** Gemini (via BigQuery ML)
