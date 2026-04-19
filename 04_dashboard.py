# ============================================================
# STEP 4: INTERACTIVE DASHBOARD — Plotly Dash
# Jalankan: python 04_dashboard.py
# Buka browser: http://127.0.0.1:8050
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc

# ── Data ─────────────────────────────────────────────────
df = pd.read_csv("output/clean_transactions.csv", parse_dates=["date"])

PALETTE  = ["#534AB7", "#1D9E75", "#EF9F27", "#D4537E"]
CATS     = sorted(df["category"].unique())
SEGMENTS = ["New", "Occasional", "Regular", "Loyal"]
MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun",
            "Jul","Aug","Sep","Oct","Nov","Dec"]

# ── App init ─────────────────────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# ── Layout ───────────────────────────────────────────────
app.layout = dbc.Container([

    # Header
    dbc.Row([dbc.Col([
        html.H4("E-Commerce Analytics Dashboard",
                className="mt-3 mb-0 fw-bold"),
        html.P("Full Year 2023 · Retail Client",
               className="text-muted small")
    ])]),

    html.Hr(),

    # Filter bar
    dbc.Row([
        dbc.Col([
            html.Label("Category", className="small fw-bold"),
            dcc.Dropdown(
                id="cat-filter",
                options=[{"label": "All", "value": "All"}] +
                        [{"label": c, "value": c} for c in CATS],
                value="All", clearable=False
            )
        ], md=3),
        dbc.Col([
            html.Label("Channel", className="small fw-bold"),
            dcc.Dropdown(
                id="ch-filter",
                options=[{"label": "All", "value": "All"}] +
                        [{"label": c, "value": c}
                         for c in df["channel"].unique()],
                value="All", clearable=False
            )
        ], md=3),
        dbc.Col([
            html.Label("Quarter", className="small fw-bold"),
            dcc.Dropdown(
                id="q-filter",
                options=[{"label": "All", "value": "All"}] +
                        [{"label": f"Q{q}", "value": q} for q in [1,2,3,4]],
                value="All", clearable=False
            )
        ], md=2),
    ], className="mb-3"),

    # KPI Cards
    dbc.Row(id="kpi-row", className="mb-3"),

    # Row 1: Line chart + Donut
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody(
            dcc.Graph(id="line-chart", config={"displayModeBar": False})
        )), md=8),
        dbc.Col(dbc.Card(dbc.CardBody(
            dcc.Graph(id="donut-chart", config={"displayModeBar": False})
        )), md=4),
    ], className="mb-3"),

    # Row 2: Bar (segment) + Heatmap
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody(
            dcc.Graph(id="seg-chart", config={"displayModeBar": False})
        )), md=5),
        dbc.Col(dbc.Card(dbc.CardBody(
            dcc.Graph(id="heatmap", config={"displayModeBar": False})
        )), md=7),
    ], className="mb-3"),

    # Row 3: Top products table
    dbc.Row([dbc.Col(dbc.Card(dbc.CardBody([
        html.H6("Top 10 Products", className="fw-bold mb-2"),
        dash_table.DataTable(
            id="prod-table",
            columns=[
                {"name": "Product",    "id": "product_name"},
                {"name": "Category",   "id": "category"},
                {"name": "Orders",     "id": "orders"},
                {"name": "Revenue",    "id": "revenue_fmt"},
                {"name": "AOV",        "id": "aov_fmt"},
            ],
            style_cell={"fontSize": "13px", "padding": "8px"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
            style_as_list_view=True,
        )
    ])))], className="mb-4"),

], fluid=True)

# ── Callback ─────────────────────────────────────────────
@app.callback(
    Output("kpi-row",     "children"),
    Output("line-chart",   "figure"),
    Output("donut-chart",  "figure"),
    Output("seg-chart",    "figure"),
    Output("heatmap",      "figure"),
    Output("prod-table",   "data"),
    Input("cat-filter",   "value"),
    Input("ch-filter",    "value"),
    Input("q-filter",     "value"),
)
def update_all(cat, ch, quarter):
    # Filter data
    d = df.copy()
    if cat != "All":     d = d[d["category"] == cat]
    if ch  != "All":     d = d[d["channel"]  == ch]
    if quarter != "All": d = d[d["quarter"]  == quarter]

    # KPI
    total_rev = d["revenue"].sum()
    total_ord = len(d)
    aov       = d["revenue"].mean()
    ret_rate  = (df[df["revenue"] < 0].shape[0] / len(df)) * 100

    def kpi_card(title, value):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.P(title, className="text-muted small mb-1"),
            html.H5(value, className="fw-bold mb-0")
        ]), className="shadow-sm"))

    kpi_cards = [
        kpi_card("Total Revenue",
                 f"Rp {total_rev/1e9:.2f}B"),
        kpi_card("Total Orders",
                 f"{total_ord:,}"),
        kpi_card("Avg Order Value",
                 f"Rp {aov/1e3:.0f}K"),
        kpi_card("Return Rate",
                 f"{ret_rate:.1f}%"),
    ]

    # Line chart
    monthly = (d.groupby("month")["revenue"]
                .sum().reindex(range(1,13), fill_value=0)
                .reset_index())
    monthly["label"] = MONTHS
    fig_line = px.area(monthly, x="label", y="revenue",
                       title="Monthly Revenue Trend",
                       color_discrete_sequence=[PALETTE[0]])
    fig_line.update_layout(showlegend=False, margin=dict(t=40,b=0,l=0,r=0),
                           yaxis_tickformat=".2s")

    # Donut
    cat_d = d.groupby("category")["revenue"].sum().reset_index()
    fig_donut = px.pie(cat_d, values="revenue", names="category",
                       title="Revenue by Category", hole=0.55,
                       color_discrete_sequence=PALETTE)
    fig_donut.update_layout(margin=dict(t=40,b=0,l=0,r=0),
                             legend=dict(orientation="h", y=-0.2))

    # Segment bar
    seg = (d.groupby("customer_segment")["revenue"]
            .sum()
            .reindex(SEGMENTS, fill_value=0)
            .reset_index())
    fig_seg = px.bar(seg, x="customer_segment", y="revenue",
                     title="Revenue by Segment",
                     color="customer_segment",
                     color_discrete_sequence=PALETTE)
    fig_seg.update_layout(showlegend=False, xaxis_title="",
                           yaxis_tickformat=".2s",
                           margin=dict(t=40,b=0,l=0,r=0))

    # Heatmap
    days_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    d["dow"] = d["date"].dt.strftime("%a")
    heat_data = (d.groupby(["dow", "month_name"])["revenue"]
                  .sum().unstack(fill_value=0)
                  .reindex(days_order))
    heat_data = heat_data.reindex(columns=MONTHS, fill_value=0)
    fig_heat = go.Figure(go.Heatmap(
        z=heat_data.values/1e6, x=MONTHS, y=days_order,
        colorscale="RdYlGn", showscale=True,
        hovertemplate="%{y} %{x}: Rp %{z:.1f}M<extra></extra>"
    ))
    fig_heat.update_layout(title="Revenue Heatmap",
                           margin=dict(t=40,b=0,l=0,r=0))

    # Top products table
    top = (d.groupby(["product_name", "category"])
            .agg(orders=("transaction_id","count"),
                 revenue=("revenue","sum"),
                 aov=("revenue","mean"))
            .reset_index()
            .nlargest(10, "revenue"))
    top["revenue_fmt"] = top["revenue"].apply(lambda x: f"Rp {x/1e6:.1f}M")
    top["aov_fmt"]     = top["aov"].apply(lambda x: f"Rp {x/1e3:.0f}K")

    return kpi_cards, fig_line, fig_donut, fig_seg, fig_heat, top.to_dict("records")

if __name__ == "__main__":
    app.run(debug=True)