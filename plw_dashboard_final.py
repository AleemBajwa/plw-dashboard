import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import textwrap
from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np

# --- GOOGLE SHEETS CONNECTION ---

SHEET_ID = "1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA"
SHEET_NAME = "Sheet1"

@st.cache_data
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    return pd.read_csv(url)

df = load_data()
df.columns = df.columns.str.strip()

# --- CLEANING ---

for col in df.select_dtypes(include='object'):
    df[col] = df[col].astype(str).str.lower().str.strip()

# Apply conditions
df["Eligible for Incentive"] = df.apply(lambda x: "no" if x.get("plw unable to withdraw") == "yes" else x.get("eligible for incentive", "no"), axis=1)

# --- DASHBOARD TITLE ---
st.title("📊 PLW Dashboard")

# --- METRICS ---

total_plws = df["plw cnic no"].nunique()
withdrawn_plws = df[df["amount withdrawn from camp (rs.)"] > 0]["plw cnic no"].nunique()
incentive_eligible = df[(df["eligible for incentive"] == "yes") & (df["plw unable to withdraw"] != "yes")]["plw cnic no"].nunique()
total_withdrawn = df["amount withdrawn from camp (rs.)"].sum()
incentive_due = df[(df["eligible for incentive"] == "yes") & (df["plw unable to withdraw"] != "yes")]["amount (rs.)"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_plws:,}")
col3.metric("Incentive Eligible (CNIC)", f"{incentive_eligible:,}")

col4, col5, _ = st.columns(3)
col4.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn):,}")
col5.metric("Incentive Due (Rs.)", f"{int(incentive_due):,}")

# --- PIE CHART FUNCTION ---
def pie_chart(title, column, labels_map=None):
    fig, ax = plt.subplots()
    values = df[column].value_counts()
    labels = []
    for i, v in values.items():
        label = f"{v:,}, {int((v / values.sum()) * 100)}%"
        labels.append(label)

    colors = ['darkgreen' if k == 'yes' else 'darkred' for k in values.index]
    wedges, texts = ax.pie(values, colors=colors)
    for i, t in enumerate(wedges):
        x, y = t.get_center()
        angle = (t.theta2 + t.theta1) / 2
        x = 0.7 * np.cos(np.radians(angle))
        y = 0.7 * np.sin(np.radians(angle))
        ax.text(x, y, labels[i], color='white', ha='center', va='center', fontsize=12)

    ax.set_title(title)
    ax.axis('equal')
    return fig

# --- PIE CHARTS ---

st.subheader("🔄 PLW Engagement Overview")
col1, col2 = st.columns(2)
with col1:
    st.pyplot(pie_chart("Contact with PLW", "contact with plw"))
with col2:
    st.pyplot(pie_chart("Visited Camp", "plw visited the camp"))

st.subheader("💸 Withdrawn Count")
col1, col2 = st.columns(2)
with col1:
    st.pyplot(pie_chart("Withdrawal", df["amount withdrawn from camp (rs.)"].apply(lambda x: "withdrawn" if x > 0 else "not withdrawn")))

# --- HORIZONTAL BAR: PLW STATUS ---
st.subheader("🧭 PLW Status")
fig, ax = plt.subplots()
status_counts = df["status of plw (nwd or pwd)"].value_counts()
bars = ax.barh(status_counts.index, status_counts.values)
for i, bar in enumerate(bars):
    ax.text(bar.get_width() - 10, bar.get_y() + bar.get_height()/2, f"{bar.get_width():,.0f}", ha='right', va='center', color='white')
ax.set_xlabel("Count")
st.pyplot(fig)

# --- ADFO-WISE WITHDRAWAL % ---
st.subheader("📉 ADFO-wise Withdrawal %")
adfo_df = df[df["amount withdrawn from camp (rs.)"] > 0]
grouped = df.groupby("adfo name")["plw cnic no"].nunique()
withdrawn = adfo_df.groupby("adfo name")["plw cnic no"].nunique()
percent = (withdrawn / grouped * 100).fillna(0).astype(int)

fig, ax = plt.subplots()
bars = ax.bar(percent.index, percent.values, color=plt.cm.tab20.colors)
ax.set_ylabel("Withdrawal %")
for i, bar in enumerate(bars):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 5, f"{int(bar.get_height())}%", ha='center', va='top', color='black')
plt.xticks(rotation=45, ha="right")
st.pyplot(fig)

# --- ADFO Benchmark vs Withdrawn ---
st.subheader("📊 ADFO: Benchmark vs Withdrawn (Rs.)")
benchmarks = df.groupby("adfo name")["adfo benchmark: withdrawal / camp (rs.)"].max()
withdrawn = df.groupby("adfo name")["amount withdrawn from camp (rs.)"].sum()
plot_df = pd.DataFrame({"Benchmark": benchmarks, "Withdrawn": withdrawn}).fillna(0)

fig, ax = plt.subplots()
x = np.arange(len(plot_df))
bar_width = 0.35
bar1 = ax.bar(x - bar_width/2, plot_df["Benchmark"], bar_width, label="Benchmark", color="darkgreen")
bar2 = ax.bar(x + bar_width/2, plot_df["Withdrawn"], bar_width, label="Withdrawn", color="darkred")

for bars in [bar1, bar2]:
    for bar in bars:
        height = int(bar.get_height())
        ax.text(bar.get_x() + bar.get_width()/2, height, f"{height:,}", ha="center", va="bottom")

ax.set_ylabel("Rs.")
ax.set_xticks(x)
ax.set_xticklabels(plot_df.index, rotation=45, ha="right")
ax.legend()
st.pyplot(fig)

# --- HORIZONTAL BAR: REASON FOR NON-WITHDRAWAL ---
st.subheader("📌 Reason for Non-Withdrawal")
reason_counts = df["reason for non-withdrawal"].value_counts()
fig, ax = plt.subplots()
bars = ax.barh(reason_counts.index, reason_counts.values, color="darkred")
for bar in bars:
    ax.text(bar.get_width() - 10, bar.get_y() + bar.get_height()/2, f"{bar.get_width():,.0f}", ha='right', va='center', color='white')
ax.set_xlabel("PLWs")
st.pyplot(fig)
