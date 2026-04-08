import streamlit as st
import sqlite3
import pandas as pd
import anthropic
import json
import re

# ── PAGE CONFIG ────────────────────────────────────────────
st.set_page_config(
    page_title="NL → SQL Agent",
    page_icon="🔍",
    layout="wide"
)

# ── SCHEMA ─────────────────────────────────────────────────
SCHEMA = """
You have access to a SQLite sales database with these tables:

customers (customer_id, name, segment [Enterprise/Mid-Market/SMB], region [Northeast/Southeast/Midwest/West/International], signup_date [YYYY-MM-DD], is_active [1/0])

products (product_id, product_name, category [Core/AI/Integration/Infrastructure/Mobile/Security/Support/Services/Enterprise], unit_price)

orders (order_id, customer_id, order_date [YYYY-MM-DD], status [completed/pending/cancelled/refunded], discount_pct)

order_items (item_id, order_id, product_id, quantity, unit_price, line_total)

Key relationships:
- orders.customer_id → customers.customer_id
- order_items.order_id → orders.order_id
- order_items.product_id → products.product_id

For revenue calculations, use order_items.line_total (already accounts for quantity).
Only count orders where status = 'completed' unless the user asks otherwise.
"""

EXAMPLE_QUESTIONS = [
    "What are the top 5 products by total revenue?",
    "How many customers signed up each month in 2023?",
    "Which customer segment generates the most revenue?",
    "What is the average order value by region?",
    "Show me the 10 customers with the highest lifetime value",
    "What percentage of orders were cancelled last year?",
    "Which product categories have the best sales performance?",
    "How has monthly revenue trended over time?",
]

# ── DB HELPER ──────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return sqlite3.connect('/home/claude/nl_sql_agent/sales.db', check_same_thread=False)

def run_query(sql):
    try:
        conn = get_connection()
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)

# ── LLM CALL ──────────────────────────────────────────────
def ask_agent(question, error_feedback=None):
    client = anthropic.Anthropic()

    error_note = ""
    if error_feedback:
        error_note = f"\n\nThe previous SQL attempt failed with this error: {error_feedback}\nPlease fix the query."

    prompt = f"""{SCHEMA}

The user asked: "{question}"{error_note}

Respond with ONLY a valid JSON object in this exact format, nothing else:
{{
  "sql": "SELECT ...",
  "explanation": "Plain English explanation of what this query does and what the results mean"
}}

Rules:
- Write clean, correct SQLite SQL
- Always alias columns with readable names
- Limit results to 20 rows maximum unless the question asks for all
- Never use markdown, backticks, or any text outside the JSON
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # Strip any accidental markdown fences
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)

# ── UI ─────────────────────────────────────────────────────
st.markdown("""
<style>
.big-title { font-size: 2.2rem; font-weight: 700; margin-bottom: 0; }
.subtitle  { font-size: 1rem; color: #666; margin-top: 0.2rem; margin-bottom: 2rem; }
.sql-box   { background: #1e1e1e; color: #d4d4d4; padding: 1rem 1.2rem;
             border-radius: 8px; font-family: monospace; font-size: 0.85rem;
             white-space: pre-wrap; margin: 0.5rem 0 1rem; }
.explain   { background: #f0f7ff; border-left: 4px solid #0066cc;
             padding: 0.8rem 1rem; border-radius: 4px; margin-bottom: 1rem;
             font-size: 0.95rem; }
.chip      { display: inline-block; background: #f0f0f0; border: 1px solid #ddd;
             border-radius: 20px; padding: 4px 14px; margin: 4px 4px 4px 0;
             font-size: 0.82rem; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-title">🔍 Natural Language → SQL Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Ask business questions in plain English. Get SQL + answers instantly.</p>', unsafe_allow_html=True)

# ── EXAMPLE CHIPS ──────────────────────────────────────────
st.markdown("**Try an example:**")
cols = st.columns(4)
for i, ex in enumerate(EXAMPLE_QUESTIONS):
    if cols[i % 4].button(ex, key=f"ex_{i}", use_container_width=True):
        st.session_state["prefill"] = ex

# ── INPUT ──────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
question = st.text_input(
    "Your question",
    value=prefill,
    placeholder="e.g. What were the top 3 regions by revenue in 2024?",
    label_visibility="collapsed"
)

run = st.button("Run Query ⚡", type="primary", use_container_width=False)

# ── EXECUTION ──────────────────────────────────────────────
if run and question.strip():
    with st.spinner("Thinking..."):
        try:
            result = ask_agent(question)
            sql = result["sql"]
            explanation = result["explanation"]

            # Try running — retry once if error
            df, err = run_query(sql)
            if err:
                with st.spinner("Fixing query..."):
                    result2 = ask_agent(question, error_feedback=err)
                    sql = result2["sql"]
                    explanation = result2["explanation"]
                    df, err2 = run_query(sql)
                    if err2:
                        st.error(f"Could not generate valid SQL: {err2}")
                        st.stop()

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("**Generated SQL**")
                st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)

            with col2:
                st.markdown("**What this means**")
                st.markdown(f'<div class="explain">{explanation}</div>', unsafe_allow_html=True)

            st.markdown(f"**Results** — {len(df)} row{'s' if len(df) != 1 else ''}")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Simple chart if numeric result
            if len(df) > 1 and len(df.columns) >= 2:
                num_cols = df.select_dtypes(include='number').columns.tolist()
                str_cols = df.select_dtypes(exclude='number').columns.tolist()
                if num_cols and str_cols:
                    try:
                        chart_df = df.set_index(str_cols[0])[num_cols[0]]
                        st.bar_chart(chart_df)
                    except Exception:
                        pass

        except json.JSONDecodeError as e:
            st.error("The model returned an unexpected format. Please try rephrasing your question.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif run and not question.strip():
    st.warning("Please enter a question first.")

# ── SIDEBAR: SCHEMA ────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Database Schema")
    st.markdown("""
**customers**
- customer_id, name
- segment (Enterprise / Mid-Market / SMB)
- region (Northeast / Southeast / Midwest / West / International)
- signup_date, is_active

**products**
- product_id, product_name
- category (Core / AI / Integration / Infrastructure / Mobile / Security / Support / Services / Enterprise)
- unit_price

**orders**
- order_id, customer_id
- order_date, status
- discount_pct

**order_items**
- item_id, order_id, product_id
- quantity, unit_price, line_total
    """)
    st.markdown("---")
    st.markdown("**500** customers · **20** products · **3,000** orders · **5,000+** line items")
    st.markdown("---")
    st.caption("Built with Anthropic Claude + Streamlit")
