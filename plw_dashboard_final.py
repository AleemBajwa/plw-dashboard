import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from google.oauth2 import service_account
import gspread
import numpy as np
import textwrap

# Google Sheet authentication
credentials = service_account.Credentials.from_service_account_file(
    "service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)
gc = gspread.authorize(credentials)

# Load data
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA")
worksheet = spreadsheet.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Clean columns
df.columns = df.columns.str.strip()

# Handle case insensitivity
df = df.applymap(lambda x: str(x).strip().lower() if isinstance(x, str) else x)

# Setup layout
st.set_page_config(layout="wide")
st.title("📊 PLW Dashboard")

# Filters
districts = sorted(df["District"].dropna().unique())
statuses = sorted(df["Status of PLW (NWD or PWD)"].dropna().unique())

col_filter1, col_filter2 = st.columns(2)
selected_districts = col_filter1.multiselect("Select District(s)", districts, default=districts)
selected_status = col_filter2.multiselect("Select PLW Status", statuses, default=statuses)

# Apply filters
filtered_df = df[
    df["District"].isin(selected_districts) &
    df["Status of PLW (NWD or PWD)"].isin(selected_status)
]

# Remove where PLW Unable to Withdraw is "yes"
filtered_df = filtered_df[filtered_df["PLW Unable to Withdraw"] != "yes"]

# Metric Calculations
total_plws = filtered_df["CNIC"].nunique()
withdrawn_df = filtered_df[filtered_df["Withdrawn (Yes/No)"] == "yes"]
withdrawn_count = withdrawn_df["CNIC"].nunique()
eligible_df = filtered_df[filtered_df["Eligible for Incentive"] == "yes"]
eligible_count = eligible_df["CNIC"].nunique()
withdrawn_amount = withdrawn_df["Amount (Rs.)"].sum()
incentive_due = eligible_df["Amount (Rs.)"].sum()

# Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_count:,}")
col3.metric("Incentive Eligible (CNIC)", f"{eligible_count:,}")

col4, col5 = st.columns(2)
col4.metric("Total Withdrawn (Rs.)", f"{int(withdrawn_amount):,}")
col5.metric("Incentive Due (Rs.)", f"{int(incentive_due):,}")

# Pie Chart Helper
def plot_pie(title, data, labels_map):
    values = data.value_counts()
    colors = ['darkgreen', 'darkred']
    labels = [f"{values[i]:,}, {int(values[i]/values.sum()*100)}%" for i in values.index]
    fig, ax = plt.subplots()
    wedges, texts = ax.pie(values, colors=colors, labels=labels, textprops={'color':"white"})
    ax.set_title(title)
    return fig

# Pie Charts
col1, col2 = st.columns(2)
with col1:
    st.subheader("📌 PLW Engagement Overview")
    st.pyplot(plot_pie("Contact with PLW", filtered_df["Contact with PLW"], {"yes": "Yes", "no": "No"}))

with col2:
    st.pyplot(plot_pie("Visited Camp", filtered_df["PLW Visited Campsite"], {"yes": "Yes", "no": "No"}))

# Withdrawal Pie
st.subheader("💸 Withdrawn Count")
withdrawal_fig = plot_pie("Withdrawal", filtered_df["Withdrawn (Yes/No)"], {"yes": "Withdrawn", "no": "Not Withdrawn"})
st.pyplot(withdrawal_fig)

# Bar Chart: ADFO-wise Withdrawal %
st.subheader("📉 ADFO-wise Withdrawal %")
grouped = filtered_df.groupby("ADFO Name")
withdrawal_pct = (grouped["Withdrawn (Yes/No)"].apply(lambda x: (x == "yes").sum() / len(x)) * 100).round(0)
withdrawal_pct = withdrawal_pct.sort_values(ascending=False)

fig, ax = plt.subplots()
colors = plt.cm.tab20.colors
withdrawal_pct.plot(kind="bar", ax=ax, color=colors)
ax.set_ylabel("Withdrawal %")
ax.set_ylim(0, 100)
for i, v in enumerate(withdrawal_pct):
    ax.text(i, v + 1, f"{int(v)}%", ha='center')
plt.xticks(rotation=45, ha='right')
st.pyplot(fig)

# Bar Chart: Benchmark vs Withdrawn (Rs.)
st.subheader("📊 ADFO: Benchmark vs Withdrawn (Rs.)")
benchmark_df = filtered_df.groupby("ADFO Name").agg({
    "Benchmark: Withdrawal / Camp (Rs.)": "max",
    "Amount withdrawn from Camp (Rs.)": "sum"
})
fig2, ax2 = plt.subplots()
x = np.arange(len(benchmark_df))
width = 0.35
bar1 = ax2.bar(x - width/2, benchmark_df.iloc[:, 0], width, label='Benchmark', color='darkgreen')
bar2 = ax2.bar(x + width/2, benchmark_df.iloc[:, 1], width, label='Withdrawn', color='darkred')
ax2.set_xticks(x)
ax2.set_xticklabels(benchmark_df.index, rotation=45, ha="right")
ax2.legend()
ax2.set_ylabel("Rs.")
for bars in [bar1, bar2]:
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f'{int(height):,}', xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', fontsize=8)
st.pyplot(fig2)

# Horizontal Bar Chart: Reason for Non-Withdrawal
st.subheader("📌 Reason for Non-Withdrawal")
reason_counts = filtered_df["Reason for Non-Withdrawal"].value_counts()
fig3, ax3 = plt.subplots()
bars = ax3.barh(reason_counts.index, reason_counts.values, color='darkred')
ax3.set_xlabel("PLWs")
for bar in bars:
    ax3.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
             f'{bar.get_width():.0f}', va='center')
st.pyplot(fig3)
