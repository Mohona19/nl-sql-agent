# Natural Language → SQL Agent
**Ask business questions in plain English. Get SQL + answers instantly.**

Built with Python, Anthropic Claude API, SQLite, and Streamlit.

---

## What it does

- Type any business question in plain English
- Claude generates the correct SQL query
- Query runs against a real sales database (500 customers, 20 products, 3,000 orders)
- Results display as a table + automatic bar chart
- Plain-language explanation of what the query found

## Quick Start

### 1. Install dependencies
```bash
pip install anthropic streamlit pandas
```

### 2. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Create the database
```bash
python create_db.py
```

### 4. Run the app
```bash
streamlit run app.py
```

---

## Example questions you can ask

- "What are the top 5 products by total revenue?"
- "Which customer segment generates the most revenue?"
- "Show me the 10 customers with the highest lifetime value"
- "How has monthly revenue trended over time?"
- "What percentage of orders were cancelled last year?"
- "Which regions have the highest average order value?"


## Live Demo
Watch it in action: https://www.loom.com/share/8566a0d4d3074f0daedfb4175169e786

## Database schema

| Table | Key columns |
|-------|-------------|
| customers | customer_id, name, segment, region, signup_date, is_active |
| products | product_id, product_name, category, unit_price |
| orders | order_id, customer_id, order_date, status, discount_pct |
| order_items | item_id, order_id, product_id, quantity, unit_price, line_total |

---

## How it works

1. User types a natural language question
2. Claude receives the database schema + the question
3. Claude returns structured JSON with SQL + plain-language explanation
4. App runs the SQL against SQLite and displays results
5. If the query fails, the app automatically retries with the error message

---

## Tech stack

- **LLM**: Anthropic Claude (claude-sonnet-4-20250514)
- **Frontend**: Streamlit
- **Database**: SQLite via Python sqlite3
- **Data**: pandas

---

*Built as part of Tasmia Afroze's AI/analytics portfolio — tasmiaafroze.com*
