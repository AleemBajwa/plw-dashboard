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
    df['Date of Camp'] = pd.to_datetime(df['Date of Camp'], errors='coerce')
    df['PLW CNIC No'] = df['PLW CNIC No'].astype(str)
    for col in ['Eligible for Incentive', 'PLW unable to withdraw', 'Contact with PLW (Y/N)', 'PLW visited the Campsite', 'Status of PLW (NWD or PWD)']:
        df[col] = df[col].astype(str).str.lower()
    return df

df = load_data()

# Sidebar filters
st.sidebar.title("Filters")
districts = ["All"] + sorted(df["District"].dropna().unique())
adfos = ["All"] + sorted(df["ADFO Name"].dropna().unique())
statuses = ["All"] + sorted(df["Status of PLW (NWD or PWD)"].dropna().unique())

selected_district = st.sidebar.selectbox("District", districts)
selected_adfo = st.sidebar.selectbox("ADFO", adfos)
selected_status = st.sidebar.selectbox("PLW Status", statuses)
date_range = st.sidebar.date_input("Date Range", [])

filtered_df = df.copy()
if selected_district != "All":
    filtered_df = filtered_df[filtered_df["District"] == selected_district]
if selected_adfo != "All":
    filtered_df = filtered_df[filtered_df["ADFO Name"] == selected_adfo]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df["Status of PLW (NWD or PWD)"] == selected_status]
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range)
    filtered_df = filtered_df[(filtered_df["Date of Camp"] >= start) & (filtered_df["Date of Camp"] <= end)]

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
col1.metric("Total PLWs (CNIC)", total_cnic)
col2.metric("Withdrawn PLWs", withdrawn_cnic)
col3.metric("Incentive Eligible (CNIC)", eligible_cnic)

st.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn_amount):,}")
st.metric("Incentive Due (Rs.)", f"{int(eligible_amount):,}")

# Pie Charts
st.subheader("📌 PLW Engagement Overview")
c1, c2 = st.columns(2)

def plot_pie(col_data, title):
    labels = col_data.index.tolist()
    sizes = col_data.values
    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct='%.1f%%', startangle=90,
                                      textprops={'color':'white', 'fontsize':10}, colors=["darkgreen", "darkred"])
    ax.legend([f"{label} ({val:,})" for label, val in zip(labels, sizes)], loc="upper left", bbox_to_anchor=(1, 1))
    ax.set_title(title, fontsize=13)
    st.pyplot(fig)

with c1:
    plot_pie(filtered_df["Contact with PLW (Y/N)"].value_counts(), "Contact with PLW")
with c2:
    plot_pie(filtered_df["PLW visited the Campsite"].value_counts(), "PLW Visited Campsite")

# Horizontal Bar: PLW Status
st.subheader("🧭 PLW Status")
status_counts = filtered_df["Status of PLW (NWD or PWD)"].value_counts()
fig, ax = plt.subplots(figsize=(6, 3))
bars = ax.barh(status_counts.index, status_counts.values, color='teal')
for bar in bars:
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
            f"{bar.get_width():.0f}", va='center', fontsize=9)
ax.set_xlabel("Count")
st.pyplot(fig)

# Pie: Withdrawal Count
st.subheader("💸 Withdrawal Count")
withdraw_vals = [withdrawn_cnic, not_withdrawn]
labels = ["Withdrawn", "Not Withdrawn"]
colors = ["darkgreen", "darkred"]
fig, ax = plt.subplots(figsize=(4, 4))
wedges, texts, autotexts = ax.pie(withdraw_vals, autopct='%.1f%%', colors=colors, textprops={'color':"white"})
ax.legend([f"{lbl} ({val:,})" for lbl, val in zip(labels, withdraw_vals)], loc="upper left", bbox_to_anchor=(1, 1))
st.pyplot(fig)

# ADFO Withdrawal %
st.subheader("📉 ADFO-wise Withdrawal %")
group = filtered_df.groupby("ADFO Name")
withdraw_pct = (filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0]
                .groupby("ADFO Name")["PLW CNIC No"]
                .nunique() / group["PLW CNIC No"].nunique() * 100).fillna(0)

fig, ax = plt.subplots(figsize=(7, 3))
labels = ['\n'.join(textwrap.wrap(label, 12)) for label in withdraw_pct.index]
bars = ax.bar(labels, withdraw_pct.values, color=plt.cm.Paired.colors)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height + 1, f"{int(height)}%", ha="center", fontsize=8)
ax.set_ylabel("Withdrawal %")
st.pyplot(fig)

# Benchmark vs Withdrawn
st.subheader("📊 ADFO: Benchmark vs Withdrawn (Rs.)")
benchmark = group["ADFO Benchmark: Withdrawal / Camp (Rs.)"].max()
withdraw = group["Amount withdrawn from Camp (Rs.)"].sum()
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(benchmark))
w = 0.35
labels = ['\n'.join(textwrap.wrap(label, 10)) for label in benchmark.index]

b1 = ax.bar(x - w/2, benchmark.values, w, label="Benchmark", color="darkgreen")
b2 = ax.bar(x + w/2, withdraw.values, w, label="Withdrawn", color="darkred")
for bars in [b1, b2]:
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500, f"{int(bar.get_height()):,}",
                ha="center", fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=0)
ax.set_ylabel("Rs.")
ax.legend()
st.pyplot(fig)

# Reason for Non-Withdrawal - horizontal bar
st.subheader("📌 Reason for Non-Withdrawal")
reasons = filtered_df["Reason for non-withdrawal"].value_counts()
wrapped = ['\n'.join(textwrap.wrap(r, 20)) for r in reasons.index]
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(wrapped, reasons.values, color='darkred')
for bar in bars:
    ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width())}",
            va="center", fontsize=8)
ax.set_xlabel("PLWs")
st.pyplot(fig)

# Table
st.subheader("📋 Filtered Data")
st.dataframe(filtered_df)
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", csv, "filtered_data.csv", "text/csv")
