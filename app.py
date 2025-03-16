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
page = st.sidebar.radio("Select View:",
                        ["Overview & Analysis", "Product Insights", "Custom Visualizations", "Download Report"])

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

# ---- Custom Visualizations Page ----
if page == "Custom Visualizations":
    st.title("Custom Data Visualizations")

    # Pie Chart for Sales by Category
    st.subheader("Sales Distribution by Category")
    if not filtered_df.empty:
        category_sales = filtered_df.groupby("Category")["Sales"].sum().reset_index()
        fig_pie = px.pie(category_sales, names="Category", values="Sales", title="Sales Breakdown by Category")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("No data available for category sales visualization.")

    # Scatter Plot for Sales vs. Profit
    st.subheader("Sales vs. Profit Analysis")
    if not filtered_df.empty:
        fig_scatter = px.scatter(filtered_df, x="Sales", y="Profit", color="Category", size="Quantity",
                                 title="Sales vs. Profit by Category")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No data available for sales vs. profit visualization.")

    # Box Plot for Profit Distribution
    st.subheader("Profit Distribution by Category")
    if not filtered_df.empty:
        fig_box = px.box(filtered_df, x="Category", y="Profit", title="Profit Distribution by Category")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.warning("No data available for profit visualization.")
