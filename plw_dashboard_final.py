
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

st.set_page_config(page_title="PLW Dashboard", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=xlsx"
    df = pd.read_excel(url)
    df = df.applymap(lambda x: str(x).strip().lower() if isinstance(x, str) else x)
    return df

df = load_data()

# Sidebar filters
st.sidebar.title("Filters")
districts = ["All"] + sorted(df["district"].dropna().unique())
statuses = ["All"] + sorted(df["status of plw (nwd or pwd)"].dropna().unique())

selected_district = st.sidebar.selectbox("District", districts)
selected_status = st.sidebar.selectbox("PLW Status", statuses)

filtered_df = df.copy()
if selected_district != "All":
    filtered_df = filtered_df[filtered_df["district"] == selected_district]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df["status of plw (nwd or pwd)"] == selected_status]

# Summary Calculations
total_cnic = filtered_df["plw cnic no"].nunique()
withdrawn_cnic = filtered_df[filtered_df["amount withdrawn from camp (rs.)"].astype(float) > 0]["plw cnic no"].nunique()
not_withdrawn = total_cnic - withdrawn_cnic

eligible_df = filtered_df[
    (filtered_df["eligible for incentive"] == "yes") &
    (filtered_df["plw unable to withdraw"] != "yes")
]
eligible_cnic = eligible_df["plw cnic no"].nunique()
eligible_amount = eligible_df["amount (rs.)"].astype(float).sum()
total_withdrawn_amount = filtered_df["amount withdrawn from camp (rs.)"].astype(float).sum()

# Display Summary Metrics
st.title("📊 PLW Dashboard Summary")
c1, c2, c3 = st.columns(3)
c4, c5, c6 = st.columns(3)

c1.metric("Total PLWs (CNIC)", f"{total_cnic:,}")
c2.metric("Withdrawn PLWs", f"{withdrawn_cnic:,}")
c3.metric("Incentive Eligible (CNIC)", f"{eligible_cnic:,}")

c4.metric("Not Withdrawn", f"{not_withdrawn:,}")
c5.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn_amount):,}")
c6.metric("Incentive Due (Rs.)", f"{int(eligible_amount):,}")

# Remaining charts will be added exactly as previously specified
