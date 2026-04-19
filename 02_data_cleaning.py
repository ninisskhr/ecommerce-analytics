# ============================================================
# STEP 2: DATA CLEANING — Bersihkan data sebelum analisis
# Ini yang paling banyak makan waktu di proyek nyata (~60-80%)
# ============================================================

import pandas as pd
import numpy as np
import os

df = pd.read_csv("data/raw_transactions.csv")

print("=" * 50)
print("📋 RAW DATA OVERVIEW")
print("=" * 50)
print(f"Shape       : {df.shape}")
print(f"Duplicates  : {df.duplicated().sum()}")
print(f"\nMissing:\n{df.isnull().sum()}")
print(f"\nNegative revenue: {(df['revenue'] < 0).sum()} rows")

# ── 1. Parse tipe data ───────────────────────────────────
df["date"]     = pd.to_datetime(df["date"])
df["revenue"]  = pd.to_numeric(df["revenue"], errors="coerce")
df["quantity"] = df["quantity"].astype("int8")

# ── 2. Pisahkan return orders (revenue negatif) ──────────
returns = df[df["revenue"] < 0].copy()
df      = df[df["revenue"] >= 0]

print(f"\n↩️  Return orders saved: {len(returns)} rows → data/returns.csv")
returns.to_csv("data/returns.csv", index=False)

# ── 3. Handle missing values ─────────────────────────────
# Revenue null → drop (tidak bisa imputasi nilai transaksi)
df = df.dropna(subset=["revenue"])

# City null → isi "Unknown" (tetap berguna untuk analisis lain)
df["city"] = df["city"].fillna("Unknown")

# ── 4. Hapus duplikat berdasarkan transaction_id ─────────
df = df.drop_duplicates(subset=["transaction_id"])

# ── 5. Feature engineering — kolom turunan ───────────────
df["year"]        = df["date"].dt.year
df["month"]       = df["date"].dt.month
df["month_name"]  = df["date"].dt.strftime("%b")
df["quarter"]     = df["date"].dt.quarter
df["day_of_week"] = df["date"].dt.day_name()
df["is_weekend"]  = df["day_of_week"].isin(["Saturday", "Sunday"])
df["margin_est"]  = df["revenue"] * 0.25  # asumsi margin 25%

# ── 6. Outlier detection (IQR method) ───────────────────
Q1 = df["revenue"].quantile(0.01)
Q3 = df["revenue"].quantile(0.99)
before = len(df)
df = df[(df["revenue"] >= Q1) & (df["revenue"] <= Q3)]
print(f"\n📊 Outliers removed: {before - len(df)} rows")

# ── 7. Simpan ─────────────────────────────────────────────
os.makedirs("output", exist_ok=True)
df.to_csv("output/clean_transactions.csv", index=False)

print("\n" + "=" * 50)
print("✅ CLEAN DATA SUMMARY")
print("=" * 50)
print(f"Final rows  : {len(df):,}")
print(f"Missing left: {df.isnull().sum().sum()}")
print(f"Date range  : {df['date'].min()} → {df['date'].max()}")
print(f"Revenue avg : Rp {df['revenue'].mean():,.0f}")
print(f"\nCategory split:\n{df['category'].value_counts(normalize=True).mul(100).round(1)}")