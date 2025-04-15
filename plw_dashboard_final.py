import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set Streamlit layout
st.set_page_config(layout="wide", page_title="PLW Dashboard")

# Load data from Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=csv"
df = pd.read_csv(sheet_url)

# Normalize column values for consistency
df.columns = df.columns.str.strip()
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].astype(str).str.strip().str.lower()

# Helper for value counts
def pie_chart_data(df, column):
    counts = df[column].value_counts()
    total = counts.sum()
    return [f"{val:,}, {int(100 * val / total)}%" for val in counts], counts.index.tolist(), counts.tolist()

# Filter UI
st.sidebar.header("Filters")
districts = st.sidebar.multiselect("District", options=df["district"].unique(), default=df["district"].unique())
adfo_names = st.sidebar.multiselect("ADFO Name", options=df["adfo name"].unique(), default=df["adfo name"].unique())
status_plw = st.sidebar.multiselect("Status of PLW", options=df["status of plw (nwd or pwd)"].unique(), default=df["status of plw (nwd or pwd)"].unique())

filtered_df = df[
    df["district"].isin(districts) &
    df["adfo name"].isin(adfo_names) &
    df["status of plw (nwd or pwd)"].isin(status_plw)
]

# Derived columns
filtered_df["amount (rs.)"] = pd.to_numeric(filtered_df["amount (rs.)"], errors="coerce").fillna(0)

withdrawn_df = filtered_df[filtered_df["withdrawn"] == "yes"]
eligible_df = filtered_df[(filtered_df["eligible for incentive"] == "yes") & (filtered_df["plw unable to withdraw"] != "yes")]

# Summary cards
col1, col2, col3 = st.columns(3)
col1.metric("Total PLWs (CNIC)", f"{filtered_df['plw cnic no'].nunique():,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_df['plw cnic no'].nunique():,}")
col3.metric("Incentive Eligible (CNIC)", f"{eligible_df['plw cnic no'].nunique():,}")
col4, col5, col6 = st.columns(3)
col4.metric("Total Withdrawn (Rs.)", f"{withdrawn_df['amount withdrawn from camp (rs.)'].sum():,.0f}")
col5.metric("Incentive Due (Rs.)", f"{eligible_df['amount (rs.)'].sum():,.0f}")
col6.metric("Not Withdrawn PLWs", f"{filtered_df['plw cnic no'].nunique() - withdrawn_df['plw cnic no'].nunique():,}")

st.markdown("---")

# Pie Charts for Contact & Visit
st.subheader("📶 PLW Engagement Overview")
pie1_labels, pie1_keys, pie1_sizes = pie_chart_data(filtered_df, "contact with plw")
pie2_labels, pie2_keys, pie2_sizes = pie_chart_data(filtered_df, "plw visited the campsite")

col1, col2 = st.columns(2)
with col1:
    fig, ax = plt.subplots()
    ax.pie(pie1_sizes, labels=None, autopct="", startangle=90, colors=["darkgreen", "darkred"])
    for i, (size, label) in enumerate(zip(pie1_sizes, pie1_labels)):
        ax.text(0.5 * np.cos(2*np.pi*i/len(pie1_sizes)), 0.5 * np.sin(2*np.pi*i/len(pie1_sizes)), label,
                ha='center', va='center', color='white', fontsize=12)
    ax.set_title("Contact with PLW")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots()
    ax.pie(pie2_sizes, labels=None, autopct="", startangle=90, colors=["darkgreen", "darkred"])
    for i, (size, label) in enumerate(zip(pie2_sizes, pie2_labels)):
        ax.text(0.5 * np.cos(2*np.pi*i/len(pie2_sizes)), 0.5 * np.sin(2*np.pi*i/len(pie2_sizes)), label,
                ha='center', va='center', color='white', fontsize=12)
    ax.set_title("Visited Camp")
    st.pyplot(fig)

# PLW Status Horizontal Bar Chart
st.subheader("🧭 PLW Status")
status_counts = filtered_df["status of plw (nwd or pwd)"].value_counts()
fig, ax = plt.subplots()
ax.barh(status_counts.index, status_counts.values, color=plt.cm.tab20.colors[:len(status_counts)])
for i, v in enumerate(status_counts.values):
    ax.text(v, i, f"{v:,}", va="center")
ax.set_xlabel("Count")
st.pyplot(fig)

# Withdrawal Count Pie
st.subheader("💸 Withdrawn Count")
withdraw_labels = ["Withdrawn", "Not Withdrawn"]
withdraw_counts = [withdrawn_df["plw cnic no"].nunique(), filtered_df["plw cnic no"].nunique() - withdrawn_df["plw cnic no"].nunique()]
fig, ax = plt.subplots()
colors = ["darkgreen", "darkred"]
ax.pie(withdraw_counts, labels=None, colors=colors, startangle=90)
for i, v in enumerate(withdraw_counts):
    percent = int((v / sum(withdraw_counts)) * 100)
    ax.text(0.5 * np.cos(2*np.pi*i/len(withdraw_counts)), 0.5 * np.sin(2*np.pi*i/len(withdraw_counts)), f"{v:,}, {percent}%",
            ha='center', va='center', color='white', fontsize=12)
ax.set_title("Withdrawal")
st.pyplot(fig)
