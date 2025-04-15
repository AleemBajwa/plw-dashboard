
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from matplotlib.cm import get_cmap

st.set_page_config(page_title="PLW Dashboard", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1GWJGHmXkJph1-xn7-5Z8ATfYzvnEP9K_/export?format=xlsx"
    df = pd.read_excel(url)
    df['Date of Camp'] = pd.to_datetime(df['Date of Camp'], errors='coerce')
    df['PLW CNIC No'] = df['PLW CNIC No'].astype(str)
    df['Eligible for Incentive'] = df['Eligible for Incentive'].astype(str).str.lower()
    df['PLW unable to withdraw'] = df['PLW unable to withdraw'].astype(str).str.lower()
    df['Contact with PLW (Y/N)'] = df['Contact with PLW (Y/N)'].astype(str).str.lower()
    df['PLW visited the Campsite'] = df['PLW visited the Campsite'].astype(str).str.lower()
    df['Status of PLW (NWD or PWD)'] = df['Status of PLW (NWD or PWD)'].astype(str).str.lower()
    return df

df = load_data()

# Filters
st.sidebar.title("🔘 Filters")
districts = ["All"] + sorted(df["District"].dropna().unique())
adfos = ["All"] + sorted(df["ADFO Name"].dropna().unique())
statuses = ["All"] + sorted(df["Status of PLW (NWD or PWD)"].dropna().unique())

selected_district = st.sidebar.selectbox("Select District", districts)
selected_adfo = st.sidebar.selectbox("Select ADFO", adfos)
selected_status = st.sidebar.selectbox("Select PLW Status", statuses)
date_range = st.sidebar.date_input("Select Date Range", [])

filtered_df = df.copy()
if selected_district != "All":
    filtered_df = filtered_df[filtered_df["District"] == selected_district]
if selected_adfo != "All":
    filtered_df = filtered_df[filtered_df["ADFO Name"] == selected_adfo]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df["Status of PLW (NWD or PWD)"] == selected_status]
if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range)
    filtered_df = filtered_df[(filtered_df["Date of Camp"] >= start_date) & (filtered_df["Date of Camp"] <= end_date)]

# Metrics
total_cnic = filtered_df["PLW CNIC No"].nunique()
withdrawn_cnic = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0]["PLW CNIC No"].nunique()
not_withdrawn = total_cnic - withdrawn_cnic
total_withdrawn_amount = filtered_df["Amount withdrawn from Camp (Rs.)"].sum()

eligible_df = filtered_df[
    (filtered_df["Eligible for Incentive"] == "yes") &
    (filtered_df["PLW unable to withdraw"] != "yes")
]
eligible_cnic = eligible_df["PLW CNIC No"].nunique()
eligible_amount = eligible_df["Amount (Rs.)"].sum()

st.title("📊 PLW Dashboard")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total PLWs (CNIC)", f"{total_cnic}")
    st.metric("Withdrawn PLWs (CNIC)", f"{withdrawn_cnic}")
with col2:
    st.metric("Not Withdrawn", f"{not_withdrawn}")
    st.metric("Total Withdrawn Amount", f"Rs. {int(total_withdrawn_amount):,}")
with col3:
    st.metric("Eligible for Incentive (CNIC)", f"{eligible_cnic}")
    st.metric("Incentive Amount (Rs.)", f"Rs. {int(eligible_amount):,}")

# Visual: Reason for Non-withdrawal
st.markdown("### ❌ Reason for Non-Withdrawal")
reason_counts = filtered_df["Reason for non-withdrawal"].value_counts()
reasons = reason_counts.index.tolist()
values = reason_counts.values.tolist()
wrapped_labels = ['
'.join(textwrap.wrap(label, 12)) for label in reasons]
fig1, ax1 = plt.subplots(figsize=(10, 5))
bars = ax1.bar(wrapped_labels, values, color="darkred")
for bar in bars:
    height = bar.get_height()
    ax1.annotate(f"{int(height)}", xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3),
                 textcoords="offset points", ha='center', fontsize=9)
ax1.set_ylabel("PLWs")
plt.xticks(rotation=0)
st.pyplot(fig1)

# Visual: ADFO Benchmark vs Actual
st.markdown("### 💰 ADFO-wise Benchmark vs Actual Withdrawn (Rs.)")
grouped = filtered_df.groupby("ADFO Name")
benchmark = grouped["ADFO Benchmark: Withdrawal / Camp (Rs.)"].sum()
withdrawn_amt = grouped["Amount withdrawn from Camp (Rs.)"].sum()
labels = benchmark.index.tolist()
x = range(len(labels))
bar_width = 0.4
fig2, ax2 = plt.subplots(figsize=(10, 5))
cmap = get_cmap("tab10")
bench_colors = [cmap(i) for i in range(len(x))]
withd_colors = [cmap(i + 5) for i in range(len(x))]
wrapped_labels = ['
'.join(textwrap.wrap(label, 12)) for label in labels]
bench_bars = ax2.bar(x, benchmark.values, width=bar_width, label="Benchmark", color=bench_colors)
withd_bars = ax2.bar([i + bar_width for i in x], withdrawn_amt.values, width=bar_width, label="Withdrawn", color=withd_colors)
for bar in bench_bars + withd_bars:
    height = bar.get_height()
    ax2.annotate(f"{int(height):,}", xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3),
                 textcoords="offset points", ha='center', fontsize=8)
ax2.set_xticks([i + bar_width / 2 for i in x])
ax2.set_xticklabels(wrapped_labels, rotation=0)
ax2.set_ylabel("Rs.")
ax2.legend()
st.pyplot(fig2)

# Final Table
st.markdown("### 📋 Filtered Data Table")
st.dataframe(filtered_df)
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Filtered Data", data=csv, file_name="filtered_data.csv")
