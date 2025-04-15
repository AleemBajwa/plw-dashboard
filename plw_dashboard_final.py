import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from textwrap import fill

# Page config
st.set_page_config(page_title="PLW Dashboard", layout="wide")

# Load data
sheet_url = "https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=csv"
df = pd.read_csv(sheet_url)

# Preprocessing
df.columns = df.columns.str.strip()
df = df.applymap(lambda x: x.strip().lower() if isinstance(x, str) else x)

# Filter options
with st.sidebar:
    st.header("🔎 Filters")
    districts = df['district'].dropna().unique()
    selected_districts = st.multiselect("Select District(s):", sorted(districts), default=sorted(districts))
    plw_status_options = df['status of plw (nwd or pwd)'].dropna().unique()
    selected_plw_status = st.multiselect("Select PLW Status:", sorted(plw_status_options), default=sorted(plw_status_options))

# Filtered data
filtered_df = df[df['district'].isin(selected_districts)]
filtered_df = filtered_df[filtered_df['status of plw (nwd or pwd)'].isin(selected_plw_status)]

# Summary calculations
total_plws = filtered_df['plw cnic no'].nunique()
withdrawn_plws = filtered_df[filtered_df['amount withdrawn from camp (rs.)'] > 0]['plw cnic no'].nunique()
not_withdrawn = total_plws - withdrawn_plws

# Apply incentive logic
eligible_incentive_df = filtered_df[
    (filtered_df['eligible for incentive'] == 'yes') &
    (filtered_df['plw unable to withdraw'] != 'yes')
]
incentive_count = eligible_incentive_df['plw cnic no'].nunique()
incentive_due = eligible_incentive_df['amount (rs.)'].sum()

# Amount
total_withdrawn_amount = filtered_df['amount withdrawn from camp (rs.)'].sum()

# Summary display
st.title("📊 PLW Dashboard")
col1, col2, col3 = st.columns(3)
col4, col5, _ = st.columns(3)

col1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_plws:,}")
col3.metric("Incentive Eligible (CNIC)", f"{incentive_count:,}")
col4.metric("Total Withdrawn (Rs.)", f"{total_withdrawn_amount:,.0f}")
col5.metric("Incentive Due (Rs.)", f"{incentive_due:,.0f}")

# Pie Chart Helper
def plot_pie(labels, counts, title):
    colors = ['darkgreen', 'darkred'] if labels[0] == 'yes' else ['darkred', 'darkgreen']
    fig, ax = plt.subplots(figsize=(3, 3))
    percentages = [f"{c:,}, {c*100//sum(counts)}%" for c in counts]
    ax.pie(counts, labels=percentages, startangle=90, colors=colors, textprops={'color':'white', 'fontsize':12})
    ax.set_title(title, fontsize=14)
    return fig

# Engagement pie charts
col1, col2 = st.columns(2)
with col1:
    st.subheader("📌 PLW Engagement Overview")
    left, right = st.columns(2)
    contact_counts = filtered_df['contact with plw'].value_counts().reindex(['yes', 'no'], fill_value=0).values
    visited_counts = filtered_df['plw visited the campsite'].value_counts().reindex(['yes', 'no'], fill_value=0).values
    left.pyplot(plot_pie(['yes', 'no'], contact_counts, "Contact with PLW"))
    right.pyplot(plot_pie(['yes', 'no'], visited_counts, "Visited Camp"))

# Withdrawal Count pie chart
with col2:
    st.subheader("💵 Withdrawn Count")
    withdrawn_counts = [withdrawn_plws, not_withdrawn]
    st.pyplot(plot_pie(['withdrawn', 'not withdrawn'], withdrawn_counts, "Withdrawal"))

# ADFO-wise Benchmark vs Withdrawn Rs
st.subheader("📊 ADFO: Benchmark vs Withdrawn (Rs.)")
benchmark_grouped = filtered_df.groupby('adfo name').agg({
    'adfo benchmark: withdrawal / camp (rs.)': 'max',
    'amount withdrawn from camp (rs.)': 'sum'
}).reset_index()

fig, ax = plt.subplots(figsize=(10, 4))
x = np.arange(len(benchmark_grouped))
width = 0.35

ax.bar(x - width/2, benchmark_grouped['adfo benchmark: withdrawal / camp (rs.)'], width, label='Benchmark', color='darkgreen')
ax.bar(x + width/2, benchmark_grouped['amount withdrawn from camp (rs.)'], width, label='Withdrawn', color='darkred')

for i, v in enumerate(benchmark_grouped['adfo benchmark: withdrawal / camp (rs.)']):
    ax.text(i - width/2, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=8)
for i, v in enumerate(benchmark_grouped['amount withdrawn from camp (rs.)']):
    ax.text(i + width/2, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels([fill(label, 12) for label in benchmark_grouped['adfo name']], rotation=0)
ax.set_ylabel("Rs.")
ax.legend()
st.pyplot(fig)

# ADFO-wise Withdrawal %
st.subheader("📉 ADFO-wise Withdrawal %")
group = filtered_df.groupby('adfo name')
adfo_perc = ((group['amount withdrawn from camp (rs.)'].apply(lambda x: (x > 0).sum()) / group['plw cnic no'].nunique()) * 100).reset_index()
adfo_perc.columns = ['adfo name', 'withdrawal %']

fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(adfo_perc['adfo name'], adfo_perc['withdrawal %'], color=plt.cm.Paired.colors)
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval, f"{int(yval)}%", ha='center', va='bottom', fontsize=8)
ax.set_xticklabels([fill(label, 10) for label in adfo_perc['adfo name']], rotation=0)
ax.set_ylabel("Withdrawal %")
st.pyplot(fig)

# PLW Status Chart
st.subheader("🧭 PLW Status")
status_counts = filtered_df['status of plw (nwd or pwd)'].value_counts()
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.barh(status_counts.index, status_counts.values, color=plt.cm.Dark2.colors)
for i, v in enumerate(status_counts.values):
    ax.text(v, i, f'{v}', va='center', ha='left', fontsize=10)
ax.set_xlabel("Count")
st.pyplot(fig)

# Reason for Non Withdrawal
st.subheader("📌 Reason for Non-Withdrawal")
reason_counts = filtered_df['reason for non-withdrawal'].value_counts()
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.barh(reason_counts.index, reason_counts.values, color=plt.cm.Set1.colors)
for i, v in enumerate(reason_counts.values):
    ax.text(v, i, f'{v}', va='center', ha='left', fontsize=10)
ax.set_xlabel("PLWs")
st.pyplot(fig)
