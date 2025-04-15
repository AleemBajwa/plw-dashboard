import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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

# Sidebar Filters
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

# --- Visuals ---
st.subheader("📈 Visuals")

# Withdrawal Status
fig1, ax1 = plt.subplots()
vals = [withdrawn_cnic, not_withdrawn]
lbls = ["Withdrawn", "Not Withdrawn"]
colors = ["darkgreen", "darkred"]
ax1.bar(lbls, vals, color=colors)
for i, v in enumerate(vals):
    ax1.text(i, v + 2, f"{v}", ha='center')
st.pyplot(fig1)

# Contact with PLW (Pie Chart)
contact_counts = filtered_df["Contact with PLW (Y/N)"].value_counts()
fig2, ax2 = plt.subplots()
ax2.pie(contact_counts, labels=[f"{k} ({v})" for k, v in contact_counts.items()], colors=["darkgreen", "darkred"])
ax2.axis("equal")
st.pyplot(fig2)

# PLW Visited Campsite (Smaller Pie)
visit_counts = filtered_df["PLW visited the Campsite"].value_counts()
fig3, ax3 = plt.subplots(figsize=(5, 5))
ax3.pie(visit_counts, labels=[f"{k} ({v})" for k, v in visit_counts.items()], colors=["darkgreen", "darkred"])
ax3.axis("equal")
st.pyplot(fig3)

# ADFO-wise Withdrawal %
grouped = filtered_df.groupby("ADFO Name")
total_by_adfo = grouped["PLW CNIC No"].nunique()
withdraw_by_adfo = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0].groupby("ADFO Name")["PLW CNIC No"].nunique()
withdraw_pct = (withdraw_by_adfo / total_by_adfo * 100).fillna(0)

fig4, ax4 = plt.subplots(figsize=(10, 4))
bars = ax4.bar(withdraw_pct.index, withdraw_pct.values, color="darkgreen")
for bar in bars:
    height = int(bar.get_height())
    ax4.text(bar.get_x() + bar.get_width()/2, height - 5, f"{height}%", ha="center", va="top", color="white")
ax4.set_ylabel("Withdrawal %")
ax4.set_xlabel("ADFO Name")
plt.xticks(rotation=30, ha='right')
st.pyplot(fig4)

# ADFO Benchmark vs Actual
benchmark = grouped["ADFO Benchmark: Withdrawal / Camp (Rs.)"].sum()
withdrawn_amt = grouped["Amount withdrawn from Camp (Rs.)"].sum()
fig5, ax5 = plt.subplots(figsize=(10, 5))
x = range(len(benchmark))
ax5.bar(x, benchmark.values, width=0.4, label="Benchmark", align='center', color="darkred")
ax5.bar([i + 0.4 for i in x], withdrawn_amt.values, width=0.4, label="Withdrawn", align='center', color="darkgreen")
ax5.set_xticks([i + 0.2 for i in x])
ax5.set_xticklabels(benchmark.index, rotation=30, ha='right')
ax5.set_ylabel("Rs.")
ax5.legend()
st.pyplot(fig5)

# Reason for Non-withdrawal
st.markdown("### ❌ Reason for Non-Withdrawal")
reason_counts = filtered_df["Reason for non-withdrawal"].value_counts()
fig6, ax6 = plt.subplots()
ax6.bar(reason_counts.index, reason_counts.values, color="darkred")
ax6.set_ylabel("PLWs")
plt.xticks(rotation=30, ha='right')
st.pyplot(fig6)

# Status of PLW (NWD/PWD)
st.markdown("### 👤 Status of PLW")
status_counts = filtered_df["Status of PLW (NWD or PWD)"].value_counts()
fig7, ax7 = plt.subplots()
ax7.bar(status_counts.index, status_counts.values, color="darkgreen")
ax7.set_ylabel("Count")
st.pyplot(fig7)

# --- Data Table Viewer ---
st.markdown("### 📋 Detailed Table View")
st.dataframe(filtered_df)
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Filtered Data", data=csv, file_name="filtered_data.csv")
