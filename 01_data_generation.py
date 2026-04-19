# ============================================================
# STEP 1: DATA GENERATION — Simulasi raw data transaksi klien
# Di dunia nyata: lo connect ke DB klien (PostgreSQL/BigQuery)
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Seed biar data reproducible (penting untuk presentasi ke klien!)
np.random.seed(42)
random.seed(42)

# ── Config ────────────────────────────────────────────────
N_TRANSACTIONS = 15_000
START_DATE = datetime(2023, 1, 1)
END_DATE   = datetime(2023, 12, 31)

# ── Master Data ──────────────────────────────────────────
PRODUCTS = {
    "Electronics": [
        ("Xiaomi Redmi 12",    2_199_000),
        ("Samsung QLED 55in",  8_999_000),
        ("Apple AirPods Pro",  3_799_000),
        ("Logitech MX Keys",   1_350_000),
        ("JBL Flip 6",         1_199_000),
    ],
    "Fashion": [
        ("Nike Air Max 270",   1_800_000),
        ("Uniqlo Heattech L",  299_000),
        ("Zara Blazer Set",    1_199_000),
        ("Adidas Ultraboost",  2_099_000),
        ("H&M Linen Shirt",    249_000),
    ],
    "Home & Living": [
        ("Dyson V11 Vacuum",   7_499_000),
        ("Philips Air Fryer",  1_499_000),
        ("IKEA Billy Shelf",   799_000),
        ("Kris Mattress King", 4_200_000),
        ("Tupperware Set",     349_000),
    ],
    "Beauty": [
        ("Skintific SPF 50+",       129_000),
        ("Somethinc Niacinamide",   99_000),
        ("The Ordinary AHA",        189_000),
        ("Wardah Instaperfect",     85_000),
        ("Emina BB Cream",          75_000),
    ],
}

CITIES = ["Jakarta", "Surabaya", "Bandung", "Medan",
          "Semarang", "Makassar", "Yogyakarta", "Bali"]

CITY_WEIGHTS = [0.35, 0.18, 0.14, 0.10,
                0.08, 0.07, 0.05, 0.03]

SEGMENTS    = ["New", "Occasional", "Regular", "Loyal"]
SEG_WEIGHTS = [0.30, 0.25, 0.25, 0.20]

CHANNELS = ["Organic", "Paid Social", "Email", "Marketplace"]

# ── Generate ──────────────────────────────────────────────
rows = []
for i in range(N_TRANSACTIONS):
    category = random.choices(
        list(PRODUCTS.keys()),
        weights=[0.38, 0.27, 0.21, 0.14]
    )[0]
    product, base_price = random.choice(PRODUCTS[category])

    # Seasonality: Q4 lebih tinggi (Harbolnas effect)
    rand_days = random.randint(0, (END_DATE - START_DATE).days)
    date = START_DATE + timedelta(days=rand_days)
    month_factor = 1.0 + 0.4 * np.sin((date.month - 3) * np.pi / 6)

    qty      = random.choices([1,2,3], weights=[0.7,0.2,0.1])[0]
    discount = random.choices([0,0.05,0.10,0.20],
                               weights=[0.5,0.2,0.2,0.1])[0]
    revenue  = round(base_price * qty * (1 - discount) * month_factor, -3)

    # Inject missing values (biar ada yang perlu di-clean)
    city    = random.choices(CITIES, CITY_WEIGHTS)[0]
    segment = random.choices(SEGMENTS, SEG_WEIGHTS)[0]
    channel = random.choice(CHANNELS)

    if random.random() < 0.03: city    = None  # 3% missing
    if random.random() < 0.02: revenue = None  # 2% missing
    if random.random() < 0.01: revenue = -abs(revenue or 0) # negative = return

    rows.append({
        "transaction_id": f"TXN{i+1:05d}",
        "date":           date.strftime("%Y-%m-%d"),
        "customer_id":    f"CUST{random.randint(1,5000):05d}",
        "product_name":   product,
        "category":       category,
        "quantity":       qty,
        "base_price":     base_price,
        "discount_pct":   discount,
        "revenue":        revenue,
        "city":           city,
        "customer_segment": segment,
        "channel":        channel,
    })

df = pd.DataFrame(rows)
os.makedirs("data", exist_ok=True)
df.to_csv("data/raw_transactions.csv", index=False)
print(f"✅ Generated {len(df):,} rows → data/raw_transactions.csv")
print(df.head())
print(f"\nMissing values:\n{df.isnull().sum()}")