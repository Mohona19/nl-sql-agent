import sqlite3
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

conn = sqlite3.connect('/home/claude/nl_sql_agent/sales.db')

# ── CUSTOMERS ──────────────────────────────────────────────
customers = pd.DataFrame({
    'customer_id': range(1, 501),
    'name': [f"Customer_{i}" for i in range(1, 501)],
    'segment': random.choices(['Enterprise', 'Mid-Market', 'SMB'], weights=[0.2, 0.35, 0.45], k=500),
    'region': random.choices(['Northeast', 'Southeast', 'Midwest', 'West', 'International'], k=500),
    'signup_date': [
        (datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1000))).strftime('%Y-%m-%d')
        for _ in range(500)
    ],
    'is_active': random.choices([1, 0], weights=[0.82, 0.18], k=500)
})

# ── PRODUCTS ───────────────────────────────────────────────
products = pd.DataFrame({
    'product_id': range(1, 21),
    'product_name': [
        'Analytics Pro', 'Analytics Starter', 'Dashboard Builder', 'Data Pipeline',
        'AI Insights', 'Report Generator', 'CRM Connector', 'API Access',
        'Data Warehouse', 'ML Toolkit', 'Mobile App', 'SSO Module',
        'Custom Exports', 'Priority Support', 'Training Package', 'Onboarding Plus',
        'Security Suite', 'Audit Logs', 'White Label', 'Enterprise Bundle'
    ],
    'category': [
        'Core', 'Core', 'Core', 'Core', 'AI', 'Core', 'Integration', 'Integration',
        'Infrastructure', 'AI', 'Mobile', 'Security', 'Core', 'Support', 'Services',
        'Services', 'Security', 'Security', 'Enterprise', 'Enterprise'
    ],
    'unit_price': [
        299, 99, 149, 399, 599, 79, 199, 249, 899, 749, 49, 149,
        89, 299, 499, 349, 449, 199, 1499, 2499
    ]
})

# ── ORDERS ─────────────────────────────────────────────────
n_orders = 3000
order_dates = [
    (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 730))).strftime('%Y-%m-%d')
    for _ in range(n_orders)
]
orders = pd.DataFrame({
    'order_id': range(1, n_orders + 1),
    'customer_id': random.choices(range(1, 501), k=n_orders),
    'order_date': order_dates,
    'status': random.choices(['completed', 'pending', 'cancelled', 'refunded'],
                              weights=[0.78, 0.10, 0.08, 0.04], k=n_orders),
    'discount_pct': random.choices([0, 5, 10, 15, 20, 25], weights=[0.5, 0.15, 0.15, 0.1, 0.07, 0.03], k=n_orders)
})

# ── ORDER ITEMS ────────────────────────────────────────────
items = []
for order_id in range(1, n_orders + 1):
    n_items = random.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05])[0]
    chosen = random.sample(range(1, 21), n_items)
    for prod_id in chosen:
        qty = random.randint(1, 5)
        price = products.loc[products['product_id'] == prod_id, 'unit_price'].values[0]
        items.append({
            'item_id': len(items) + 1,
            'order_id': order_id,
            'product_id': prod_id,
            'quantity': qty,
            'unit_price': price,
            'line_total': round(qty * price, 2)
        })

order_items = pd.DataFrame(items)

# Save to SQLite
customers.to_sql('customers', conn, if_exists='replace', index=False)
products.to_sql('products', conn, if_exists='replace', index=False)
orders.to_sql('orders', conn, if_exists='replace', index=False)
order_items.to_sql('order_items', conn, if_exists='replace', index=False)
conn.close()

print(f"Database created successfully")
print(f"  customers: {len(customers)} rows")
print(f"  products:  {len(products)} rows")
print(f"  orders:    {len(orders)} rows")
print(f"  items:     {len(order_items)} rows")
