import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

st.set_page_config(page_title="PLW Dashboard", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=xlsx"
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

# Sidebar filters
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

# Display Metrics
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

# Pie charts - side by side
st.markdown("### 🔄 PLW Engagement Overview")
c1, c2 = st.columns(2)
with c1:
    contact_counts = filtered_df["Contact with PLW (Y/N)"].value_counts()
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.pie(contact_counts, labels=[f"{k} ({v})" for k, v in contact_counts.items()],
           colors=["darkgreen", "darkred"], autopct='%1.1f%%')
    ax.set_title("Contact with PLW")
    st.pyplot(fig)

with c2:
    visit_counts = filtered_df["PLW visited the Campsite"].value_counts()
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.pie(visit_counts, labels=[f"{k} ({v})" for k, v in visit_counts.items()],
           colors=["darkgreen", "darkred"], autopct='%1.1f%%')
    ax.set_title("PLW Visited Campsite")
    st.pyplot(fig)

# PLW Status Bar
status_counts = filtered_df["Status of PLW (NWD or PWD)"].value_counts()
fig, ax = plt.subplots(figsize=(5, 3))
bars = ax.barh(status_counts.index, status_counts.values, color="teal")
for bar in bars:
    ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width())}", va='center')
ax.set_title("PLW Status")
ax.set_xlabel("Count")
st.pyplot(fig)

# Withdrawal Status Bar
fig, ax = plt.subplots(figsize=(5, 3))
vals = [withdrawn_cnic, not_withdrawn]
lbls = ["Withdrawn", "Not Withdrawn"]
colors = ["darkgreen", "darkred"]
ax.bar(lbls, vals, color=colors)
for i, v in enumerate(vals):
    ax.text(i, v + 3, str(v), ha='center')
st.pyplot(fig)

# ADFO-wise Withdrawal %
grouped = filtered_df.groupby("ADFO Name")
total_by_adfo = grouped["PLW CNIC No"].nunique()
withdraw_by_adfo = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0].groupby("ADFO Name")["PLW CNIC No"].nunique()
withdraw_pct = (withdraw_by_adfo / total_by_adfo * 100).fillna(0)

fig, ax = plt.subplots(figsize=(7, 3))
labels = ['\n'.join(textwrap.wrap(label, 10)) for label in withdraw_pct.index]
bars = ax.bar(labels, withdraw_pct.values, color="darkblue")
for bar in bars:
    height = int(bar.get_height())
    ax.text(bar.get_x() + bar.get_width()/2, height + 1, f"{height}%", ha="center", fontsize=8)
ax.set_ylabel("Withdrawal %")
st.pyplot(fig)

# Benchmark vs Withdrawn
bench = grouped["ADFO Benchmark: Withdrawal / Camp (Rs.)"].max()
withdraw_amt = grouped["Amount withdrawn from Camp (Rs.)"].sum()
x = range(len(bench))
fig, ax = plt.subplots(figsize=(8, 4))
labels = ['\n'.join(textwrap.wrap(label, 12)) for label in bench.index]
bar1 = ax.bar(x, bench.values, width=0.4, label="Benchmark", color="darkgreen")
bar2 = ax.bar([i + 0.4 for i in x], withdraw_amt.values, width=0.4, label="Withdrawn", color="darkred")
for b in bar1 + bar2:
    h = int(b.get_height())
    ax.text(b.get_x() + b.get_width()/2, h + 5, f"{h:,}", ha="center", fontsize=7)
ax.set_xticks([i + 0.2 for i in x])
ax.set_xticklabels(labels, rotation=0)
ax.set_ylabel("Rs.")
ax.legend()
st.pyplot(fig)

# Reason for Non-Withdrawal
reason_counts = filtered_df["Reason for non-withdrawal"].value_counts()
labels = ['\n'.join(textwrap.wrap(label, 14)) for label in reason_counts.index]
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(labels, reason_counts.values, color="darkred")
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height + 2, str(height), ha="center", fontsize=8)
ax.set_ylabel("PLWs")
st.pyplot(fig)

# Table and download
st.markdown("### 📋 Filtered Data Table")
st.dataframe(filtered_df)
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Filtered Data", data=csv, file_name="filtered_data.csv")
