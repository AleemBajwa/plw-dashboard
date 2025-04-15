import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
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
st.sidebar.header("Filters")
districts = ["All"] + sorted(df["District"].dropna().unique())
adfos = ["All"] + sorted(df["ADFO Name"].dropna().unique())
statuses = ["All"] + sorted(df["Status of PLW (NWD or PWD)"].dropna().unique())

selected_district = st.sidebar.selectbox("District", districts)
selected_adfo = st.sidebar.selectbox("ADFO Name", adfos)
selected_status = st.sidebar.selectbox("PLW Status", statuses)
date_range = st.sidebar.date_input("Date Range", [])

# Apply filters
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

# Proceed to part 2?

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

# Dashboard Title & Metrics
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
    st.metric("Districts Covered", f"{filtered_df['District'].nunique()}")

# Pie Charts: Contact + Campsite
st.markdown("### 🔄 PLW Engagement Overview")
c1, c2 = st.columns(2)
for col, column_name, title in zip([c1, c2], ["Contact with PLW (Y/N)", "PLW visited the Campsite"], ["Contact with PLW", "PLW Visited Campsite"]):
    with col:
        pie_data = filtered_df[column_name].value_counts()
        fig, ax = plt.subplots(figsize=(4, 4))
        wedges, texts, autotexts = ax.pie(
            pie_data,
            labels=[f"{k} ({v:,})" for k, v in pie_data.items()],
            colors=["darkgreen", "darkred"],
            autopct=lambda pct: f"{pct:.1f}%",
            textprops={"color": "white", "fontsize": 10}
        )
        ax.set_title(title, fontsize=14)
        st.pyplot(fig)

# Horizontal bar: PLW Status
st.markdown("### PLW Status")
status_data = filtered_df["Status of PLW (NWD or PWD)"].value_counts()
fig, ax = plt.subplots(figsize=(6, 3))
bars = ax.barh(status_data.index, status_data.values, color="teal")
for bar in bars:
    ax.text(bar.get_width() - 5, bar.get_y() + bar.get_height()/2,
            f"{int(bar.get_width())}", va='center', ha='right', color='white')
ax.set_xlabel("Count")
st.pyplot(fig)

# Withdrawal Status Bar
st.markdown("### Withdrawal Status")
withdraw_data = {
    "Withdrawn": withdrawn_cnic,
    "Not Withdrawn": not_withdrawn
}
fig, ax = plt.subplots(figsize=(5, 4))
colors = ['darkgreen', 'darkred']
bars = ax.bar(withdraw_data.keys(), withdraw_data.values, color=colors)
for bar in bars:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 30,
            f"{int(bar.get_height())}", ha='center', va='top', fontsize=12, color='white')
ax.set_ylim(0, max(withdraw_data.values()) * 1.2)
st.pyplot(fig)

# Benchmark vs Withdrawn
st.markdown("### 💰 ADFO-wise Benchmark vs Actual Withdrawn")
benchmarks = filtered_df.groupby("ADFO Name")["ADFO Benchmark (Rs.)"].max()
withdrawals = filtered_df.groupby("ADFO Name")["Amount withdrawn from Camp (Rs.)"].sum()
merged = pd.DataFrame({"Benchmark": benchmarks, "Withdrawn": withdrawals}).sort_index()

fig, ax = plt.subplots(figsize=(10, 5))
merged.plot(kind='bar', ax=ax, color=["darkgreen", "darkred"])
for i, row in merged.iterrows():
    ax.text(i, row["Benchmark"] + 5000, f"{int(row['Benchmark']):,}", ha='center', fontsize=9, rotation=0)
    ax.text(i + 0.25, row["Withdrawn"] + 5000, f"{int(row['Withdrawn']):,}", ha='center', fontsize=9, rotation=0)
ax.set_ylabel("Rs.")
ax.legend()
st.pyplot(fig)

# Reason for non-withdrawal (horizontal bar)
st.markdown("### 🚫 Reason for Non-Withdrawal")
reasons = filtered_df["Reason for non-withdrawal"].dropna().value_counts()
wrapped_labels = ['\n'.join(textwrap.wrap(label, width=20)) for label in reasons.index]
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(wrapped_labels, reasons.values, color="darkred")
for bar in bars:
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
            str(bar.get_width()), va='center', fontsize=10)
st.pyplot(fig)
