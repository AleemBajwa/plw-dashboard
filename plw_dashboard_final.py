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

# Filters
st.sidebar.title("🔘 Filters")
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

# Summary
st.title("📊 PLW Dashboard Summary")
c1, c2, c3 = st.columns(3)
c4, c5, c6 = st.columns(3)
c1.metric("Total PLWs (CNIC)", f"{total_cnic:,}")
c2.metric("Withdrawn PLWs", f"{withdrawn_cnic:,}")
c3.metric("LHWs Eligible for Incentive", f"{eligible_cnic:,}")
c4.metric("Not Withdrawn", f"{not_withdrawn:,}")
c5.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn_amount):,}")
c6.metric("Incentive Due (Rs.)", f"{int(eligible_amount):,}")

# Pie Chart Function
def pie_chart(data, labels, title, colors):
    fig, ax = plt.subplots(figsize=(4, 4))
    total = sum(data)
    percentages = [int(round((count / total) * 100)) for count in data]
    display_labels = [f"{label} ({count:,}, {pct}%)" for label, count, pct in zip(labels, data, percentages)]

    wedges, texts = ax.pie(
        data,
        labels=display_labels,
        startangle=90,
        colors=colors,
        labeldistance=0.1,  # bring labels inward
        textprops={"color": "white", "fontsize": 10}
    )
    ax.set_title(title)
    return fig

# Engagement Section
st.subheader("🔄 PLW Engagement Overview")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    contact_vals = filtered_df["Contact with PLW (Y/N)"].value_counts()
    fig = pie_chart(contact_vals.values, contact_vals.index, "Contact with PLW", ["darkgreen", "darkred"])
    st.pyplot(fig)

with col2:
    camp_vals = filtered_df["PLW visited the Campsite"].value_counts()
    fig = pie_chart(camp_vals.values, camp_vals.index, "Visited Camp", ["darkgreen", "darkred"])
    st.pyplot(fig)

with col3:
    fig = pie_chart([withdrawn_cnic, not_withdrawn], ["Withdrawn", "Not Withdrawn"], "Withdrawal Count", ["darkgreen", "darkred"])
    st.pyplot(fig)

# ADFO Benchmark vs Withdrawn
st.subheader("📊 ADFO: Benchmark vs Withdrawn (Rs.)")
group = filtered_df.groupby("ADFO Name")
benchmark = group["ADFO Benchmark: Withdrawal / Camp (Rs.)"].max()
withdrawn = group["Amount withdrawn from Camp (Rs.)"].sum()
x = np.arange(len(benchmark))
labels = ['\n'.join(textwrap.wrap(label, 10)) for label in benchmark.index]
fig, ax = plt.subplots(figsize=(9, 4))
b1 = ax.bar(x - 0.2, benchmark.values, width=0.4, label="Benchmark", color="darkgreen")
b2 = ax.bar(x + 0.2, withdrawn.values, width=0.4, label="Withdrawn", color="darkred")
for bar in b1 + b2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height + 2000, f"{int(height):,}", ha='center', va='bottom', fontsize=8, rotation=90)
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Rs.")
ax.legend()
st.pyplot(fig)
# --- Reason for Non-Withdrawal ---
st.subheader("📌 Reason for Non-Withdrawal")
reason_counts = filtered_df["Reason for non-withdrawal"].value_counts()
wrapped_labels = ['\n'.join(textwrap.wrap(label, 25)) for label in reason_counts.index]
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(wrapped_labels, reason_counts.values, color="darkred")
for bar in bars:
    ax.text(bar.get_width() - 5, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width()):,}",
            ha="right", va="center", color="white", fontsize=8)
ax.set_xlabel("PLWs")
st.pyplot(fig)

# --- ADFO-wise Withdrawal % ---
st.subheader("📈 ADFO-wise Withdrawal %")
group = filtered_df.groupby("ADFO Name")
total_by_adfo = group["PLW CNIC No"].nunique()
withdraw_by_adfo = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0].groupby("ADFO Name")["PLW CNIC No"].nunique()
withdraw_pct = (withdraw_by_adfo / total_by_adfo * 100).fillna(0)

fig, ax = plt.subplots(figsize=(9, 4))
labels = ['\n'.join(textwrap.wrap(label, 12)) for label in withdraw_pct.index]
bars = ax.bar(labels, withdraw_pct.values, color=plt.cm.Paired.colors)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height - 5, f"{int(height)}%", ha="center", va="top", color="white", fontsize=9)
ax.set_ylabel("Withdrawal %")
st.pyplot(fig)

# --- PLW Status Chart ---
st.subheader("👤 PLW Status")
status_counts = filtered_df["Status of PLW (NWD or PWD)"].value_counts()
fig, ax = plt.subplots(figsize=(6, 3))
bars = ax.barh(status_counts.index, status_counts.values, color=plt.cm.Set2.colors)
for bar in bars:
    ax.text(bar.get_width() - 5, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width()):,}",
            ha="right", va="center", color="black", fontsize=9)
ax.set_xlabel("Count")
st.pyplot(fig)

# --- Data Table ---
st.subheader("📋 Filtered Data Table")
st.dataframe(filtered_df)
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", csv, "filtered_data.csv", "text/csv")
