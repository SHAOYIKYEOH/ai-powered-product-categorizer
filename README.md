# Project Background
(To protect business confidentiality, all sensitive information in this project has been anonymized)

Founder in 2008, Sky office is an importer & distributor in all type of office automation & equipment serving customers throughtout Malaysia.

Although the company has a significant amount of sales and demographic data, its **digital transformation** is still limited. Much of the data is incomplete or unstructured. For example, many products are not categorized, and the sources of sales are not consistently recorded. As a result, it is difficult to analyze business performance or identify areas that require improvement.

### The Mission
The goal of this project is to build an **AI-powered pipeline** that automatically categorizes products, enabling better analysis and decision-making.

Problems caused by the lack of categorization:
- **Blind Spot:** Zero visibility into which product lines are actually driving profit.
- **Trend Lag:** Missing the start of a new consumer trend because "hidden" categories aren't being tracked.

The raw data can be downloaded [here](data/raw_data.csv).

The SQL queries used to clean, organize and prepare the data for this analysis are available [here].

The SQL queries used to send prompts to the AI model are available [here](ai-prompts.sql).

The results can be found [here](data/categorized_products.csv).

# Data Architecture

RAW data structure seen consists of following attributes: Date, Doc_No, Item_Code, Item_Description, Company_Name, Area, Qty, UOM, Unit_Price, DISC(Discount), Subtotal. With a total row count of 84,074 records.

### The Transformation
This architecture processes the raw transactional data by first cleaning and standardizing the dataset so that each Item_Code corresponds to a single Item_Description.

After preprocessing, an AI model accesses the data warehouse through an API to read product descriptions and automatically classify them into relevant categories.

<img width="1303" height="346" alt="image" src="https://github.com/user-attachments/assets/9aa4e3bc-72a0-44a7-a9c6-f181928c1537" />



