# ============================================================
# STEP 3: EDA — Temukan insight dari data
# Output: chart PNG yang bisa dipakai di presentasi klien
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

os.makedirs("output/charts", exist_ok=True)
df = pd.read_csv("output/clean_transactions.csv", parse_dates=["date"])

# ── Style global ─────────────────────────────────────────
PALETTE = ["#534AB7", "#1D9E75", "#EF9F27", "#D4537E"]
sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.1)
plt.rcParams["figure.dpi"] = 150

def fmt_rp(x, _): return f"Rp {x/1e6:.0f}M"
def savefig(name):
    plt.tight_layout()
    plt.savefig(f"output/charts/{name}.png", bbox_inches="tight")
    plt.close()
    print(f"  💾 Saved: output/charts/{name}.png")

# ────────────────────────────────────────────────────────
# Chart 1: Monthly Revenue Trend (Line Chart + YoY comparison)
# ────────────────────────────────────────────────────────
monthly = df.groupby(["year", "month"])["revenue"].sum().reset_index()

fig, ax = plt.subplots(figsize=(12, 4.5))
months_label = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]
data2023 = monthly[monthly["year"] == 2023].sort_values("month")

ax.plot(months_label, data2023["revenue"],
       marker="o", lw=2.5, ms=7, color=PALETTE[0], label="2023")
ax.fill_between(months_label, data2023["revenue"],
                alpha=0.1, color=PALETTE[0])

# Annotate peak
peak_idx = data2023["revenue"].idxmax()
peak_val  = data2023.loc[peak_idx, "revenue"]
peak_mon  = months_label[data2023["month"].tolist().index(data2023.loc[peak_idx, "month"])]
ax.annotate(f"Peak\n{fmt_rp(peak_val, None)}",
            xy=(peak_mon, peak_val), xytext=(0, 20),
            textcoords="offset points", ha="center",
            fontsize=9, color=PALETTE[0],
            arrowprops=dict(arrowstyle="->", color=PALETTE[0]))

ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_rp))
ax.set_title("Monthly Revenue Trend 2023", fontweight="bold")
ax.set_xlabel(""); ax.set_ylabel("Revenue")
savefig("01_monthly_trend")

# ────────────────────────────────────────────────────────
# Chart 2: Revenue by Category (Horizontal Bar)
# ────────────────────────────────────────────────────────
cat_rev = (df.groupby("category")["revenue"]
             .sum()
             .sort_values(ascending=True)
             .reset_index())

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(cat_rev["category"], cat_rev["revenue"],
               color=PALETTE, edgecolor="none", height=0.5)

for bar, val in zip(bars, cat_rev["revenue"]):
    ax.text(bar.get_width() + 5e6, bar.get_y() + bar.get_height()/2,
           fmt_rp(val, None), va="center", fontsize=9)

ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_rp))
ax.set_title("Revenue by Category", fontweight="bold")
savefig("02_category_revenue")

# ────────────────────────────────────────────────────────
# Chart 3: Customer Segment Analysis (Grouped Bar)
# ────────────────────────────────────────────────────────
seg = df.groupby("customer_segment").agg(
    orders  = ("transaction_id", "count"),
    revenue = ("revenue", "sum"),
    aov     = ("revenue", "mean")
).reset_index()
seg_order = ["New", "Occasional", "Regular", "Loyal"]
seg = seg.set_index("customer_segment").loc[seg_order]

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
seg["revenue"].plot(kind="bar", ax=axes[0], color=PALETTE, rot=0)
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_rp))
axes[0].set_title("Total Revenue per Segment", fontweight="bold")

seg["aov"].plot(kind="bar", ax=axes[1], color=PALETTE, rot=0)
axes[1].yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"Rp {x/1e3:.0f}K"))
axes[1].set_title("Avg Order Value per Segment", fontweight="bold")
savefig("03_segment_analysis")

# ────────────────────────────────────────────────────────
# Chart 4: Heatmap — Revenue by Day of Week × Month
# ────────────────────────────────────────────────────────
days_order = ["Monday","Tuesday","Wednesday",
              "Thursday","Friday","Saturday","Sunday"]
heat = df.groupby(["day_of_week", "month_name"])["revenue"].sum().unstack()
heat = heat.reindex(days_order)

fig, ax = plt.subplots(figsize=(13, 4))
sns.heatmap(heat/1e6, ax=ax, cmap="RdYlGn", fmt=".0f",
            annot=True, linewidths=0.3, cbar_kws={"label": "Revenue (Juta)"})
ax.set_title("Revenue Heatmap — Day vs Month", fontweight="bold")
ax.set_xlabel(""); ax.set_ylabel("")
savefig("04_heatmap_day_month")

# ────────────────────────────────────────────────────────
# Chart 5: Top 10 Products
# ────────────────────────────────────────────────────────
top10 = (df.groupby("product_name")["revenue"]
           .sum()
           .nlargest(10)
           .sort_values(ascending=True))

fig, ax = plt.subplots(figsize=(9, 5))
top10.plot(kind="barh", ax=ax, color=PALETTE[0], edgecolor="none")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_rp))
ax.set_title("Top 10 Products by Revenue", fontweight="bold")
ax.set_ylabel("")
savefig("05_top10_products")

print("\n✅ EDA selesai! 5 chart tersimpan di output/charts/")

# ── Print key insights ───────────────────────────────────
print("\n📌 KEY INSIGHTS:")
total_rev  = df["revenue"].sum()
loyal_rev  = df[df["customer_segment"] == "Loyal"]["revenue"].sum()
loyal_pct  = loyal_rev / total_rev * 100
weekend_rev = df[df["is_weekend"]]["revenue"].mean()
weekday_rev = df[~df["is_weekend"]]["revenue"].mean()
q4_rev     = df[df["quarter"] == 4]["revenue"].sum()
q4_pct     = q4_rev / total_rev * 100

print(f"  → Loyal customers = {loyal_pct:.1f}% of total revenue")
print(f"  → Weekend AOV vs Weekday: +{(weekend_rev/weekday_rev-1)*100:.1f}%")
print(f"  → Q4 contributes {q4_pct:.1f}% of annual revenue (Harbolnas!)")