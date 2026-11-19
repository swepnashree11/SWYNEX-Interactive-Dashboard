import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="Cafe Sales Dashboard",
    page_icon="☕",
    layout="wide"
)

# ---------------- CUSTOM DESIGN ----------------
st.markdown("""
<style>
    .stApp { background-color: #F6F7FB; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E5E9F0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 7px rgba(20, 35, 60, 0.05);
    }
    div[data-testid="stMetricLabel"] p {
        color: #68758A;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] { color: #17233C; }

    /* Sidebar background and all sidebar labels */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background-color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #17233C !important;
    }

    /* Dropdown selected value, options and date input */
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-color: #D7CBB8 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] div,
    section[data-testid="stSidebar"] [data-baseweb="select"] span,
    section[data-testid="stSidebar"] [data-baseweb="select"] input,
    section[data-testid="stSidebar"] [data-baseweb="datepicker"] input,
    section[data-testid="stSidebar"] input {
        color: #17233C !important;
        -webkit-text-fill-color: #17233C !important;
    }
    [data-baseweb="popover"] [role="option"] {
        color: #17233C !important;
        background-color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] button {
        color: #17233C !important;
        border-color: #D7CBB8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD CLEANED DATA ----------------
@st.cache_data
def load_data():
    possible_files = [
        Path("data/processed/dirty_cafe_sales_cleaned_v2.csv"),
        Path("data/processed/dirty_cafe_sales_cleaned.csv"),
        Path("SWYNEX-Data-Cleaning-Preparation/data/processed/dirty_cafe_sales_cleaned_v2.csv")
    ]

    csv_file = next((file for file in possible_files if file.exists()), None)

    if csv_file is None:
        raise FileNotFoundError(
            "Cleaned CSV not found. Keep app.py in the main project folder "
            "and the cleaned CSV inside data/processed/."
        )

    data = pd.read_csv(csv_file)

    required_columns = [
        "Transaction ID", "Item", "Quantity", "Price Per Unit",
        "Total Spent", "Payment Method", "Location", "Transaction Date"
    ]

    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Dataset dates use DD-MM-YYYY format.
    data["Transaction Date"] = pd.to_datetime(
        data["Transaction Date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    for col in ["Quantity", "Price Per Unit", "Total Spent"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    for col in ["Item", "Payment Method", "Location"]:
        data[col] = data[col].fillna("Unknown").astype(str)

    return data


try:
    df = load_data()
except Exception as error:
    st.error("The dashboard could not load the dataset.")
    st.exception(error)
    st.stop()

# ---------------- DASHBOARD HEADER ----------------
st.title("☕ Cafe Sales Dashboard")
st.markdown(
    "**Interactive overview of sales performance, transactions and payment patterns.**"
)

st.divider()

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.title("☕ Dashboard Filters")
st.sidebar.write("Choose filters to explore the sales data.")

item_options = ["All"] + sorted(df["Item"].dropna().unique().tolist())
payment_options = ["All"] + sorted(df["Payment Method"].dropna().unique().tolist())
location_options = ["All"] + sorted(df["Location"].dropna().unique().tolist())

selected_item = st.sidebar.selectbox("Item", item_options)
selected_payment = st.sidebar.selectbox("Payment Method", payment_options)
selected_location = st.sidebar.selectbox("Location", location_options)

valid_dates = df["Transaction Date"].dropna()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_dates = st.sidebar.date_input(
        "Transaction Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    selected_dates = ()

if st.sidebar.button("Reset filters"):
    st.rerun()

# ---------------- APPLY FILTERS ----------------
filtered_df = df.copy()

if selected_item != "All":
    filtered_df = filtered_df[filtered_df["Item"] == selected_item]

if selected_payment != "All":
    filtered_df = filtered_df[
        filtered_df["Payment Method"] == selected_payment
    ]

if selected_location != "All":
    filtered_df = filtered_df[
        filtered_df["Location"] == selected_location
    ]

if selected_dates and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered_df = filtered_df[
        filtered_df["Transaction Date"].dt.date.between(start_date, end_date)
    ]

# ---------------- KPI CARDS ----------------
st.subheader("Performance at a Glance")

total_revenue = filtered_df["Total Spent"].sum()
total_transactions = filtered_df["Transaction ID"].nunique()

transaction_totals = (
    filtered_df.groupby("Transaction ID")["Total Spent"].sum()
)
average_transaction = transaction_totals.mean()

total_quantity = filtered_df["Quantity"].sum()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Total Revenue", f"{total_revenue:,.2f}")
kpi2.metric("Total Transactions", f"{total_transactions:,}")
kpi3.metric(
    "Average Transaction",
    f"{average_transaction:,.2f}" if pd.notna(average_transaction) else "N/A"
)
kpi4.metric(
    "Quantity Sold",
    f"{total_quantity:,.0f}" if pd.notna(total_quantity) else "N/A"
)

st.caption("KPI values update automatically when you change the filters.")
st.divider()

# ---------------- MONTHLY REVENUE TREND ----------------
st.subheader("Monthly Revenue Trend")

dated_df = filtered_df.dropna(
    subset=["Transaction Date", "Total Spent"]
).copy()

if not dated_df.empty:
    dated_df["Month"] = dated_df["Transaction Date"].dt.to_period("M").dt.to_timestamp()

    monthly_revenue = (
        dated_df.groupby("Month", as_index=False)["Total Spent"]
        .sum()
        .sort_values("Month")
    )

    fig_month = px.line(
        monthly_revenue,
        x="Month",
        y="Total Spent",
        markers=True,
        title="Revenue by Month",
        labels={"Month": "Month", "Total Spent": "Revenue"}
    )

    fig_month.update_traces(
        line=dict(color="#D49A45", width=3),
        marker=dict(size=8, color="#17233C"),
        hovertemplate="%{x|%B %Y}<br>Revenue: %{y:,.2f}<extra></extra>"
    )
    fig_month.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=15, r=15, t=45, b=15)
    )
    st.plotly_chart(fig_month, use_container_width=True)
else:
    st.info("No valid dated sales records are available for the selected filters.")

# ---------------- ITEM AND PAYMENT CHARTS ----------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Revenue by Item")

    item_revenue = (
        filtered_df.groupby("Item", as_index=False)["Total Spent"]
        .sum()
        .sort_values("Total Spent", ascending=True)
    )

    if not item_revenue.empty:
        fig_item = px.bar(
            item_revenue,
            x="Total Spent",
            y="Item",
            orientation="h",
            color="Total Spent",
            color_continuous_scale=["#E9CFA8", "#B9782D"],
            labels={"Total Spent": "Revenue", "Item": ""}
        )
        fig_item.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=10, r=10, t=25, b=15),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_item, use_container_width=True)
    else:
        st.info("No item revenue to display.")

with chart_col2:
    st.subheader("Transactions by Payment Method")

    payment_count = (
        filtered_df.groupby("Payment Method")["Transaction ID"]
        .nunique()
        .reset_index(name="Transactions")
    )

    if not payment_count.empty:
        fig_payment = px.pie(
            payment_count,
            names="Payment Method",
            values="Transactions",
            hole=0.55,
            color_discrete_sequence=[
                "#17233C", "#D49A45", "#6F91B7", "#A9B8C9", "#D8DEE8"
            ]
        )
        fig_payment.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="%{label}<br>Transactions: %{value:,}<extra></extra>"
        )
        fig_payment.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=10, r=10, t=25, b=15),
            showlegend=False
        )
        st.plotly_chart(fig_payment, use_container_width=True)
    else:
        st.info("No payment data to display.")

# ---------------- LOCATION CHART ----------------
st.subheader("Revenue by Sales Location")

location_revenue = (
    filtered_df.groupby("Location", as_index=False)["Total Spent"]
    .sum()
    .sort_values("Total Spent", ascending=False)
)

if not location_revenue.empty:
    fig_location = px.bar(
        location_revenue,
        x="Location",
        y="Total Spent",
        color="Location",
        color_discrete_sequence=["#17233C", "#D49A45", "#6F91B7"],
        labels={"Location": "Location", "Total Spent": "Revenue"}
    )
    fig_location.update_layout(
        template="plotly_white",
        height=320,
        margin=dict(l=10, r=10, t=25, b=15),
        showlegend=False
    )
    st.plotly_chart(fig_location, use_container_width=True)
else:
    st.info("No location revenue to display.")

st.divider()

# ---------------- KEY BUSINESS INSIGHTS ----------------
st.subheader("Key Business Insights")

valid_sales = filtered_df.dropna(subset=["Total Spent"])

if not valid_sales.empty:
    item_totals = valid_sales.groupby("Item")["Total Spent"].sum()
    known_items = item_totals.drop(index="Unknown", errors="ignore")

    if not known_items.empty:
        best_item = known_items.idxmax()
        best_item_revenue = known_items.max()
        st.markdown(
            f"**Top revenue-generating item:** {best_item} recorded "
            f"{best_item_revenue:,.2f} in revenue for the selected filters."
        )

    location_totals = valid_sales.groupby("Location")["Total Spent"].sum()
    known_locations = location_totals.drop(index="Unknown", errors="ignore")

    if not known_locations.empty:
        best_location = known_locations.idxmax()
        st.markdown(
            f"**Leading sales location:** {best_location} recorded the "
            "highest revenue among the known locations."
        )

    unknown_payment_rows = (filtered_df["Payment Method"] == "Unknown").sum()
    unknown_payment_pct = (
        unknown_payment_rows / len(filtered_df) * 100
        if len(filtered_df) > 0 else 0
    )

    st.markdown(
        f"**Data quality note:** {unknown_payment_pct:.1f}% of the filtered "
        "transaction rows have an Unknown payment method. Keep this limitation "
        "in mind when interpreting payment preferences."
    )
else:
    st.info("Not enough valid sales values to generate business insights.")

# ---------------- FILTERED DATA TABLE ----------------
with st.expander("View Filtered Transaction Data"):
    quality_col1, quality_col2, quality_col3 = st.columns(3)

    quality_col1.metric("Filtered Rows", f"{len(filtered_df):,}")
    quality_col2.metric(
        "Rows with Missing Dates",
        f"{filtered_df['Transaction Date'].isna().sum():,}"
    )
    quality_col3.metric(
        "Rows with Missing Sales Values",
        f"{filtered_df['Total Spent'].isna().sum():,}"
    )

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# ---------------- FOOTER ----------------
st.divider()
st.caption(
    "Cafe Sales Analytics Dashboard | Task 3 – Interactive Dashboard | "
    "Source: cleaned Cafe Sales dataset"
)
