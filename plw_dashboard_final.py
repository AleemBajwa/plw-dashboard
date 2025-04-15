import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Page config
st.set_page_config(page_title="PLW Dashboard", layout="wide")

# Google Sheet setup
SHEET_ID = "1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA"
SHEET_NAME = "Sheet1"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip().str.lower()
    return df

df = load_data()

# Filter
with st.sidebar:
    st.header("Filter Options")
    districts = df["district"].dropna().unique()
    selected_districts = st.multiselect("Select District", sorted(districts), default=sorted(districts))
    status_list = df["status of plw (nwd or pwd)"].dropna().unique()
    selected_status = st.multiselect("Select PLW Status", sorted(status_list), default=sorted(status_list))

df_filtered = df[df["district"].isin(selected_districts) & df["status of plw (nwd or pwd)"].isin(selected_status)]

# Summary
total_plws = df_filtered["plw cnic no"].nunique()
withdrawn_count = df_filtered[df_filtered["withdrawn plw"] == "yes"]["plw cnic no"].nunique()
eligible_df = df_filtered[(df_filtered["eligible for incentive"] == "yes") & (df_filtered["plw unable to withdraw"] != "yes")]
incentive_eligible = eligible_df["plw cnic no"].nunique()
total_withdrawn = df_filtered[df_filtered["withdrawn plw"] == "yes"]["amount (rs.)"].sum()
incentive_due = eligible_df["amount (rs.)"].sum()

st.title("📊 PLW Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_count:,}")
col3.metric("Incentive Eligible (CNIC)", f"{incentive_eligible:,}")

col4, col5 = st.columns(2)
col4.metric("Total Withdrawn (Rs.)", f"{total_withdrawn:,.0f}")
col5.metric("Incentive Due (Rs.)", f"{incentive_due:,.0f}")

# Pie Chart Function
def plot_pie(data, title, labels_map):
    counts = data.value_counts()
    labels = [f"{labels_map.get(k, k)} ({v:,}, {v / counts.sum():.0%})" for k, v in counts.items()]
    colors = ['darkgreen', 'darkred']
    fig, ax = plt.subplots()
    wedges, texts = ax.pie(
        counts,
        colors=colors[:len(counts)],
        startangle=90,
        wedgeprops=dict(width=0.4)
    )
    for i, (wedge, count) in enumerate(zip(wedges, counts)):
        angle = (wedge.theta2 + wedge.theta1) / 2
        x = 0.65 * np.cos(np.deg2rad(angle))
        y = 0.65 * np.sin(np.deg2rad(angle))
        ax.text(x, y, f"{count:,}, {count / counts.sum():.0%}", ha='center', va='center', color='white', fontsize=12)
    ax.set_title(title)
    ax.axis('equal')
    return fig

# Engagement Charts
st.subheader("🔄 PLW Engagement Overview")
c1, c2 = st.columns(2)
with c1:
    fig1 = plot_pie(df_filtered["contact with plw"], "Contact with PLW", {"yes": "Yes", "no": "No"})
    st.pyplot(fig1)

with c2:
    fig2 = plot_pie(df_filtered["plw visited campsite"], "Visited Camp", {"yes": "Yes", "no": "No"})
    st.pyplot(fig2)

# Withdrawal Pie
st.subheader("💳 Withdrawn Count")
withdrawal_pie = df_filtered["withdrawn plw"].apply(lambda x: "Withdrawn" if x == "yes" else "Not Withdrawn")
fig3 = plot_pie(withdrawal_pie, "Withdrawal", {"Withdrawn": "Withdrawn", "Not Withdrawn": "Not Withdrawn"})
st.pyplot(fig3)

# ADFO-wise Benchmark vs Actual
st.subheader("📊 ADFO: Benchmark vs Withdrawn")
df_filtered["amount (rs.)"] = pd.to_numeric(df_filtered["amount (rs.)"], errors='coerce').fillna(0)
benchmark = df_filtered.groupby("adfo name")["benchmark: withdrawal / camp (rs.)"].max()
actual = df_filtered.groupby("adfo name")["amount (rs.)"].sum()
bar_df = pd.DataFrame({"Benchmark": benchmark, "Withdrawn": actual}).dropna()

fig4, ax4 = plt.subplots()
bar_df.plot(kind="bar", ax=ax4, color=["darkgreen", "darkred"], width=0.75)
for idx, row in bar_df.iterrows():
    ax4.text(idx, row["Benchmark"], f"{int(row['Benchmark']):,}", ha="center", va="bottom", fontsize=9)
    ax4.text(idx, row["Withdrawn"], f"{int(row['Withdrawn']):,}", ha="center", va="top", fontsize=9)
ax4.set_ylabel("Rs.")
ax4.set_xticklabels(bar_df.index, rotation=45, ha="right")
ax4.legend()
st.pyplot(fig4)

# ADFO-wise Withdrawal %
st.subheader("📈 ADFO-wise Withdrawal %")
withdrawn_df = df_filtered.copy()
withdrawn_df["withdrawn_flag"] = withdrawn_df["withdrawn plw"] == "yes"
withdrawn_percent = withdrawn_df.groupby("adfo name")["withdrawn_flag"].mean().sort_values(ascending=False) * 100

fig5, ax5 = plt.subplots()
withdrawn_percent.plot(kind="bar", ax=ax5, color=plt.cm.Paired(np.arange(len(withdrawn_percent))))
ax5.set_ylabel("Withdrawal %")
ax5.set_ylim(0, 100)
for i, val in enumerate(withdrawn_percent):
    ax5.text(i, val - 5, f"{val:.0f}%", ha="center", va="top", color="black")
ax5.set_xticklabels(withdrawn_percent.index, rotation=45, ha="right")
st.pyplot(fig5)

# Reason for Non-Withdrawal
st.subheader("📌 Reason for Non-Withdrawal")
non_withdrawal = df_filtered[df_filtered["plw unable to withdraw"] == "yes"]
reasons = non_withdrawal["reason for non-withdrawal"].value_counts()
wrapped_labels = ['\n'.join(textwrap.wrap(label, 25)) for label in reasons.index]

fig6, ax6 = plt.subplots()
bars = ax6.barh(wrapped_labels, reasons.values, color="darkred")
for bar in bars:
    width = bar.get_width()
    ax6.text(width - 5, bar.get_y() + bar.get_height() / 2, f"{int(width):,}", ha="right", va="center", color="white")
ax6.set_xlabel("PLWs")
st.pyplot(fig6)

# PLW Status Overview
st.subheader("🧭 PLW Status")
status_counts = df_filtered["status of plw (nwd or pwd)"].value_counts()
fig7, ax7 = plt.subplots()
bars = ax7.barh(status_counts.index, status_counts.values, color=plt.cm.Set3.colors)
for bar in bars:
    width = bar.get_width()
    ax7.text(width - 5, bar.get_y() + bar.get_height() / 2, f"{int(width):,}", ha="right", va="center", color="black")
ax7.set_xlabel("Count")
st.pyplot(fig7)
