import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Enhanced SuperStore Dashboard", layout="wide")

# ---- Load Data ----
@st.cache_data
def load_data():
    df = pd.read_excel("Sample - Superstore.xlsx", engine="openpyxl")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df

df_original = load_data()

# ---- Sidebar Filters ----
st.sidebar.title("Filters")

# Region Filter
selected_region = st.sidebar.selectbox("Select Region", ["All"] + sorted(df_original["Region"].dropna().unique()))
filtered_df = df_original if selected_region == "All" else df_original[df_original["Region"] == selected_region]

# State Filter (Dynamic)
selected_state = st.sidebar.selectbox("Select State", ["All"] + sorted(filtered_df["State"].dropna().unique()))
filtered_df = filtered_df if selected_state == "All" else filtered_df[filtered_df["State"] == selected_state]

# Category Filter (Dynamic)
selected_category = st.sidebar.selectbox("Select Category", ["All"] + sorted(filtered_df["Category"].dropna().unique()))
filtered_df = filtered_df if selected_category == "All" else filtered_df[filtered_df["Category"] == selected_category]

# Sub-Category Filter (Dynamic)
selected_subcat = st.sidebar.selectbox("Select Sub-Category", ["All"] + sorted(filtered_df["Sub-Category"].dropna().unique()))
filtered_df = filtered_df if selected_subcat == "All" else filtered_df[filtered_df["Sub-Category"] == selected_subcat]

# Date Range Filter
min_date, max_date = filtered_df["Order Date"].min(), filtered_df["Order Date"].max()
from_date = st.sidebar.date_input("From Date", value=min_date, min_value=min_date, max_value=max_date)
to_date = st.sidebar.date_input("To Date", value=max_date, min_value=min_date, max_value=max_date)

if from_date > to_date:
    st.sidebar.error("From Date must be earlier than To Date.")

filtered_df = filtered_df[(filtered_df["Order Date"] >= pd.to_datetime(from_date)) & (filtered_df["Order Date"] <= pd.to_datetime(to_date))]

# ---- KPI Calculations ----
if filtered_df.empty:
    total_sales, total_quantity, total_profit, margin_rate = 0, 0, 0, 0
else:
    total_sales = filtered_df["Sales"].sum()
    total_quantity = filtered_df["Quantity"].sum()
    total_profit = filtered_df["Profit"].sum()
    margin_rate = (total_profit / total_sales) if total_sales != 0 else 0

# Compute previous period sales for comparison
prev_df = df_original[(df_original["Order Date"] < pd.to_datetime(from_date))]
prev_sales = prev_df["Sales"].sum()
sales_change = ((total_sales - prev_sales) / prev_sales * 100) if prev_sales != 0 else 0

# ---- KPI Display ----
kpi_cols = st.columns(4)
kpis = [
    ("Sales", f"${total_sales:,.2f}", sales_change),
    ("Quantity Sold", f"{total_quantity:,.0f}", None),
    ("Profit", f"${total_profit:,.2f}", None),
    ("Margin Rate", f"{(margin_rate * 100):.2f}%", None)
]
for col, (title, value, change) in zip(kpi_cols, kpis):
    col.markdown(f"""
        <div style='text-align: center; padding: 10px; border: 2px solid #EAEAEA; border-radius: 8px; background-color: white;'>
            <p style='color: #333; font-weight: bold; font-size: 16px;'>{title}</p>
            <p style='font-size: 24px; color: #1E90FF; font-weight: bold;'>{value}</p>
            {f"<p style='color: {'green' if change > 0 else 'red'};'>({'+' if change > 0 else ''}{change:.2f}%)</p>" if change is not None else ''}
        </div>
    """, unsafe_allow_html=True)

# ---- KPI Visualization ----
st.subheader("Visualize KPI Trends and Top Products")
selected_kpi = st.radio("Select KPI to display:", ["Sales", "Quantity", "Profit", "Margin Rate"], horizontal=True)

daily_data = filtered_df.groupby("Order Date").sum().reset_index()
daily_data["Margin Rate"] = daily_data["Profit"] / daily_data["Sales"].replace(0, 1)

top_products = filtered_df.groupby("Product Name").sum().reset_index()
top_products["Margin Rate"] = top_products["Profit"] / top_products["Sales"].replace(0, 1)
top_10 = top_products.sort_values(by=selected_kpi, ascending=False).head(10)

col1, col2 = st.columns(2)

with col1:
    fig_line = px.line(daily_data, x="Order Date", y=selected_kpi, title=f"{selected_kpi} Over Time",
                        labels={"Order Date": "Date", selected_kpi: selected_kpi}, template="plotly_white")
    fig_line.update_traces(hoverinfo="x+y", line=dict(width=2))
    st.plotly_chart(fig_line, use_container_width=True)

with col2:
    fig_bar = px.bar(top_10, x=selected_kpi, y="Product Name", orientation="h", title=f"Top 10 Products by {selected_kpi}",
                     labels={selected_kpi: selected_kpi, "Product Name": "Product"}, color=selected_kpi,
                     color_continuous_scale="Blues", template="plotly_white")
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bar, use_container_width=True)

# ---- Anomaly Alerts ----
avg_sales = df_original["Sales"].mean()
if total_sales < avg_sales * 0.5:
    st.warning("🚨 Sales are significantly lower than average! Consider investigating.")
