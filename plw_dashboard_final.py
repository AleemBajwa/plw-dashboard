
import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from textwrap import wrap
from matplotlib.ticker import FuncFormatter

# Function to add comma separator
def format_number(x):
    return f"{int(x):,}"

# Function to wrap labels
def wrap_labels(labels, width=15):
    return ['\n'.join(wrap(str(label), width=width)) for label in labels]

# Read Google Sheets data
sheet_url = 'https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=xlsx'
df = pd.read_excel(sheet_url)

# Standardize column names and values
df.columns = df.columns.str.strip()
for col in df.select_dtypes(include='object'):
    df[col] = df[col].astype(str).str.strip().str.lower()

# Filters
st.sidebar.header("Filter Data")
districts = st.sidebar.multiselect("Select District", options=df['district'].unique(), default=df['district'].unique())
statuses = st.sidebar.multiselect("Select PLW Status", options=df['status of plw (nwd or pwd)'].unique(), default=df['status of plw (nwd or pwd)'].unique())
df_filtered = df[df['district'].isin(districts) & df['status of plw (nwd or pwd)'].isin(statuses)]

# Summary Metrics
st.title("📊 PLW Dashboard")
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

total_cnics = df_filtered['cnic'].nunique()
withdrawn = df_filtered[df_filtered['amount (rs.)'] > 0]
withdrawn_cnics = withdrawn['cnic'].nunique()

eligible = df_filtered[
    (df_filtered['eligible for incentive'].str.lower() == 'yes') &
    (df_filtered['plw unable to withdraw'].str.lower() != 'yes')
]
incentive_cnics = eligible['cnic'].nunique()

total_withdrawn = withdrawn['amount (rs.)'].sum()
incentive_due = eligible['amount (rs.)'].sum()

col1.metric("Total PLWs (CNIC)", format_number(total_cnics))
col2.metric("Withdrawn PLWs", format_number(withdrawn_cnics))
col3.metric("Incentive Eligible (CNIC)", format_number(incentive_cnics))
col4.metric("Total Withdrawn (Rs.)", format_number(total_withdrawn))
col5.metric("Incentive Due (Rs.)", format_number(incentive_due))

# Pie Charts: Contact and Visit
st.markdown("### 🧷 PLW Engagement Overview")
pie1, pie2 = st.columns(2)

def plot_pie(ax, column, title):
    counts = df_filtered[column].value_counts()
    labels = [f"{k}, {format_number(v)}, {int(v / counts.sum() * 100)}%" for k, v in counts.items()]
    colors = ['darkgreen' if 'yes' in k else 'darkred' for k in counts.index]
    ax.pie(counts, labels=labels, colors=colors, textprops={'color': 'white', 'fontsize': 12})
    ax.set_title(title, fontsize=14)

fig1, ax1 = plt.subplots()
plot_pie(ax1, 'contact with plw', "Contact with PLW")
pie1.pyplot(fig1)

fig2, ax2 = plt.subplots()
plot_pie(ax2, 'plw visited campsite', "Visited Camp")
pie2.pyplot(fig2)

# Pie chart for withdrawal
st.markdown("### 💸 Withdrawn Count")
withdraw_counts = pd.Series({
    'Withdrawn': withdrawn['cnic'].nunique(),
    'Not Withdrawn': df_filtered['cnic'].nunique() - withdrawn['cnic'].nunique()
})

fig, ax = plt.subplots()
colors = ['darkgreen', 'darkred']
labels = [f"{format_number(v)}, {int(v / withdraw_counts.sum() * 100)}%" for v in withdraw_counts]
ax.pie(withdraw_counts, labels=labels, colors=colors, textprops={'color': 'white', 'fontsize': 12})
ax.set_title("Withdrawal", fontsize=14)
st.pyplot(fig)

# PLW Status Horizontal Chart
st.markdown("### 🧭 PLW Status")
plw_status_counts = df_filtered['plw status'].value_counts()
fig, ax = plt.subplots()
colors = sns.color_palette("pastel", len(plw_status_counts))
bars = ax.barh(plw_status_counts.index, plw_status_counts.values, color=colors)
for bar in bars:
    ax.text(bar.get_width() - 5, bar.get_y() + bar.get_height()/2, format_number(bar.get_width()), va='center', ha='right', color='black')
ax.set_xlabel("Count")
st.pyplot(fig)

# ADFO-wise % Chart
st.markdown("### 📉 ADFO-wise Withdrawal %")
adfo_grouped = df_filtered.groupby('adfo name')
percent_df = adfo_grouped['amount (rs.)'].agg(['sum', 'count']).reset_index()
percent_df['withdrawal %'] = (percent_df['sum'] / percent_df['count'] / 1000).fillna(0).astype(int)

fig, ax = plt.subplots()
sns.barplot(data=percent_df, x='adfo name', y='withdrawal %', ax=ax, palette='pastel')
for container in ax.containers:
    ax.bar_label(container, fmt='%d%%', label_type='edge')
ax.set_xticklabels(wrap_labels(percent_df['adfo name']))
ax.set_ylabel("Withdrawal %")
st.pyplot(fig)

# Benchmark vs Withdrawn
st.markdown("### 📊 ADFO: Benchmark vs Withdrawn (Rs.)")
df_benchmark = df_filtered.groupby('adfo name').agg({
    'amount (rs.)': 'sum',
    'benchmark: withdrawal / camp (rs.)': 'max'
}).reset_index()

fig, ax = plt.subplots()
x = np.arange(len(df_benchmark))
width = 0.35
bars1 = ax.bar(x - width/2, df_benchmark['benchmark: withdrawal / camp (rs.)'], width, label='Benchmark', color='darkgreen')
bars2 = ax.bar(x + width/2, df_benchmark['amount (rs.)'], width, label='Withdrawn', color='darkred')
ax.set_xticks(x)
ax.set_xticklabels(wrap_labels(df_benchmark['adfo name']))
ax.set_ylabel("Rs.")
ax.legend()
for b in bars1 + bars2:
    ax.text(b.get_x() + b.get_width()/2, b.get_height(), format_number(b.get_height()), ha='center', va='bottom', fontsize=8)
st.pyplot(fig)

# Reason for Non-Withdrawal
st.markdown("### 📌 Reason for Non-Withdrawal")
reason_counts = df_filtered['reason for non-withdrawal'].value_counts()
fig, ax = plt.subplots()
bars = ax.barh(wrap_labels(reason_counts.index), reason_counts.values, color='darkred')
for bar in bars:
    ax.text(bar.get_width() - 5, bar.get_y() + bar.get_height()/2, format_number(bar.get_width()), va='center', ha='right', color='white')
ax.set_xlabel("PLWs")
st.pyplot(fig)
