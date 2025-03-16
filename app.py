import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Next-Gen SuperStore Dashboard", layout="wide")


# ---- Load Data ----
@st.cache_data
def load_data():
    df = pd.read_excel("Sample - Superstore.xlsx", engine="openpyxl")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df


df_original = load_data()

# ---- Sidebar Filters ----
st.sidebar.title("Filters")

# Multi-Page Navigation
page = st.sidebar.radio("Select View:", ["Overview", "Detailed Analysis", "Product Insights", "Custom Visualizations",
                                         "Download Report"])

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
selected_subcat = st.sidebar.selectbox("Select Sub-Category",
                                       ["All"] + sorted(filtered_df["Sub-Category"].dropna().unique()))
filtered_df = filtered_df if selected_subcat == "All" else filtered_df[filtered_df["Sub-Category"] == selected_subcat]

# Date Range Filter
min_date, max_date = filtered_df["Order Date"].min(), filtered_df["Order Date"].max()
from_date = st.sidebar.date_input("From Date", value=min_date, min_value=min_date, max_value=max_date)
to_date = st.sidebar.date_input("To Date", value=max_date, min_value=min_date, max_value=max_date)

if from_date > to_date:
    st.sidebar.error("From Date must be earlier than To Date.")

filtered_df = filtered_df[
    (filtered_df["Order Date"] >= pd.to_datetime(from_date)) & (filtered_df["Order Date"] <= pd.to_datetime(to_date))]

# ---- KPI Calculations ----
if filtered_df.empty:
    total_sales, total_quantity, total_profit, margin_rate = 0, 0, 0, 0
else:
    total_sales = filtered_df["Sales"].sum()
    total_quantity = filtered_df["Quantity"].sum()
    total_profit = filtered_df["Profit"].sum()
    margin_rate = (total_profit / total_sales) if total_sales != 0 else 0

# ---- Multi-Page Views ----
if page == "Overview":
    st.title("Business Overview")

    kpi_cols = st.columns(4)
    kpis = [
        ("Sales", f"${total_sales:,.2f}"),
        ("Quantity Sold", f"{total_quantity:,.0f}"),
        ("Profit", f"${total_profit:,.2f}"),
        ("Margin Rate", f"{(margin_rate * 100):.2f}%")
    ]
    for col, (title, value) in zip(kpi_cols, kpis):
        col.metric(title, value)

    # ---- Improved Sales Over Time Chart ----
    sales_trend = filtered_df.groupby("Order Date")["Sales"].sum().reset_index()
    fig_sales = px.line(
        sales_trend,
        x="Order Date",
        y="Sales",
        title="Sales Over Time",
        template="plotly_dark",
        line_shape="spline",
        markers=True
    )
    fig_sales.update_traces(line=dict(width=2), marker=dict(size=4))
    fig_sales.update_layout(yaxis_title="Total Sales", xaxis_title="Date")
    st.plotly_chart(fig_sales, use_container_width=True)

elif page == "Detailed Analysis":
    st.title("Detailed Sales & Profit Trends")
    selected_kpi = st.radio("Select KPI to Analyze:", ["Sales", "Profit", "Quantity"], horizontal=True)

    daily_data = filtered_df.groupby("Order Date")[
        filtered_df.select_dtypes(include=["number"]).columns].sum().reset_index()
    fig_kpi = px.area(daily_data, x="Order Date", y=selected_kpi, title=f"{selected_kpi} Trends",
                      template="plotly_dark")
    st.plotly_chart(fig_kpi, use_container_width=True)

elif page == "Product Insights":
    st.title("Product Performance")
    top_products = filtered_df.groupby("Product Name")[
        filtered_df.select_dtypes(include=["number"]).columns].sum().reset_index()
    top_10 = top_products.sort_values(by="Sales", ascending=False).head(10)

    fig_bar = px.bar(top_10, x="Sales", y="Product Name", orientation="h", title="Top 10 Best-Selling Products",
                     template="plotly_dark")
    st.plotly_chart(fig_bar, use_container_width=True)

elif page == "Custom Visualizations":
    st.title("Custom Data Visualizations")

    # Pie Chart for Sales by Category
    st.subheader("Sales Distribution by Category")
    if not filtered_df.empty:
        category_sales = filtered_df.groupby("Category")["Sales"].sum().reset_index()
        fig_pie = px.pie(category_sales, names="Category", values="Sales", title="Sales Breakdown by Category")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("No data available for category sales visualization.")

    # Box Plot for Profit Distribution
    st.subheader("Profit Distribution by Category")
    if not filtered_df.empty:
        fig_box = px.box(filtered_df, x="Category", y="Profit", title="Profit Distribution by Category")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.warning("No data available for profit visualization.")

elif page == "Download Report":
    st.title("Download Report")
    st.write("Export filtered data to CSV for further analysis.")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download CSV", data=csv, file_name="SuperStore_Report.csv", mime='text/csv')

# ---- Alerts for Sudden Drops ----
avg_sales = df_original["Sales"].mean()
if total_sales < avg_sales * 0.5:
    st.error("⚠️ Sales are significantly lower than average! Immediate attention required.")
