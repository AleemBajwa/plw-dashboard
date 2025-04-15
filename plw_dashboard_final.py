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

# --- Summary Section ---
st.title("📊 PLW Dashboard Summary")
c1, c2, c3 = st.columns(3)
c4, c5, c6 = st.columns(3)

c1.metric("Total PLWs (CNIC)", f"{total_cnic:,}")
c2.metric("Withdrawn PLWs", f"{withdrawn_cnic:,}")
c3.metric("LHWs Eligible for Incentive", f"{eligible_cnic:,}")

c4.metric("Not Withdrawn", f"{not_withdrawn:,}")
c5.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn_amount):,}")
c6.metric("Incentive Due (Rs.)", f"{int(eligible_amount):,}")

# --- Pie Charts ---
def pie_chart(data, labels, title, colors, size=(3.2, 3.2)):
    fig, ax = plt.subplots(figsize=size)
    wedges, texts, autotexts = ax.pie(
        data,
        labels=None,
        startangle=90,
        autopct=lambda p: f"{int(p * sum(data) / 100):,}, {int(p)}%",
        colors=colors,
        textprops={"color": "white", "fontsize": 10}
    )
    ax.set_title(title)
    return fig

st.subheader("🔄 PLW Engagement Overview")
col1, col2, col3 = st.columns(3)

with col1:
    contact_counts = filtered_df["Contact with PLW (Y/N)"].value_counts()
    labels = ['yes', 'no']
    data = [contact_counts.get(label, 0) for label in labels]
    fig = pie_chart(data, labels, "Contact with PLW", ["darkgreen", "darkred"])
    st.pyplot(fig)

with col2:
    visit_counts = filtered_df["PLW visited the Campsite"].value_counts()
    labels = ['yes', 'no']
    data = [visit_counts.get(label, 0) for label in labels]
    fig = pie_chart(data, labels, "Visited Camp", ["darkgreen", "darkred"])
    st.pyplot(fig)

with col3:
    fig = pie_chart([withdrawn_cnic, not_withdrawn], ["Withdrawn", "Not Withdrawn"], "Withdrawal Count", ["darkgreen", "darkred"])
    st.pyplot(fig)

# 🔻 Add legend below the pie charts
st.markdown("""
<div style='text-align: center; padding-top: 10px;'>
    <span style='display: inline-block; margin-right: 30px;'>
        <span style='display:inline-block; width:12px; height:12px; background-color:darkgreen; margin-right:5px;'></span>
        <strong>Green:</strong> Yes / Withdrawn
    </span>
    <span style='display: inline-block;'>
        <span style='display:inline-block; width:12px; height:12px; background-color:darkred; margin-right:5px;'></span>
        <strong>Red:</strong> No / Not Withdrawn
    </span>
</div>
""", unsafe_allow_html=True)


# --- PLW Status Horizontal Bar ---
st.subheader("👤 PLW Status")
status_counts = filtered_df["Status of PLW (NWD or PWD)"].value_counts()
fig, ax = plt.subplots(figsize=(6, 3))
bars = ax.barh(status_counts.index, status_counts.values, color=plt.cm.Set2.colors)
for bar in bars:
    ax.text(bar.get_width() - 5, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width()):,}",
            ha="right", va="center", color="white", fontsize=9)
st.pyplot(fig)

# --- ADFO-wise Withdrawal % ---
st.subheader("📈 ADFO-wise Withdrawal %")
group = filtered_df.groupby("ADFO Name")
total_by_adfo = group["PLW CNIC No"].nunique()
withdraw_by_adfo = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0].groupby("ADFO Name")["PLW CNIC No"].nunique()
withdraw_pct = (withdraw_by_adfo / total_by_adfo * 100).fillna(0)

fig, ax = plt.subplots(figsize=(8, 2))
labels = ['\n'.join(textwrap.wrap(label, 8)) for label in withdraw_pct.index]
bars = ax.bar(labels, withdraw_pct.values, color=plt.cm.Paired.colors)
ax.tick_params(axis='x', labelsize=8)

for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height - 2, f"{int(height)}%", ha="center", va="top", color="white", fontsize=9)

ax.set_ylabel("Withdrawal %")
st.pyplot(fig)

# --- Benchmark vs Withdrawn (Max) ---
st.subheader("📊 ADFO: Benchmark vs Withdrawn (Rs.)")
benchmark = group["ADFO Benchmark: Withdrawal / Camp (Rs.)"].max()
withdrawn = group["Amount withdrawn from Camp (Rs.)"].sum()
labels = ['\n'.join(textwrap.wrap(label, 10)) for label in benchmark.index]
x = np.arange(len(benchmark))  # <-- This is the missing line

fig, ax = plt.subplots(figsize=(12, 8))
bar1 = ax.bar(x - 0.2, benchmark.values, 0.4, label="Benchmark", color="darkgreen")
bar2 = ax.bar(x + 0.2, withdrawn.values, 0.4, label="Withdrawn", color="darkred")

for bars in [bar1, bar2]:
    for bar in bars:
        label_height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, label_height - (0.05 * label_height),  # slightly below top
                f"{int(label_height):,}", ha="center", va="top", color="white", fontsize=10, rotation=90)


ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.tick_params(axis='x', labelsize=10)

ax.legend()
st.pyplot(fig)



# --- Reason for Non-Withdrawal ---
st.subheader("📌 Reason for Non-Withdrawal")
reason_counts = filtered_df["Reason for non-withdrawal"].value_counts()
labels = ['\n'.join(textwrap.wrap(label, 20)) for label in reason_counts.index]
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(labels, reason_counts.values, color=plt.cm.Set3.colors)
ax.tick_params(axis='y', labelsize=8)

for bar in bars:
    ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width()):,}",
            ha="right", va="center", color="black", fontsize=8)
ax.set_xlabel("PLWs")
st.pyplot(fig)

# --- Data Table + Export ---
st.subheader("📋 Filtered Data Table")
st.dataframe(filtered_df)
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", csv, "filtered_data.csv", "text/csv")
