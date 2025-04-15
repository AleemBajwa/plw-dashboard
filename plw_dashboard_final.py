import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Page configuration FIRST
st.set_page_config(layout="wide", page_title="PLW Dashboard")

# Load data
sheet_url = "https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=csv"
df = pd.read_csv(sheet_url)

# Clean column names
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Normalize Yes/No casing
yes_no_columns = ['contact_with_plw', 'plw_visited_campsite', 'plw_unable_to_withdraw']
for col in yes_no_columns:
    if col in df.columns:
        df[col] = df[col].str.strip().str.lower()

# Filters in sidebar
st.sidebar.header("Filter")
districts = st.sidebar.multiselect("Select District(s)", options=df['district'].dropna().unique(), default=df['district'].dropna().unique())
status_options = st.sidebar.multiselect("Select PLW Status", options=df['status_of_plw_(nwd_or_pwd)'].dropna().unique(), default=df['status_of_plw_(nwd_or_pwd)'].dropna().unique())

df = df[df['district'].isin(districts) & df['status_of_plw_(nwd_or_pwd)'].isin(status_options)]

# Apply logic to calculate metrics
df['eligible'] = df['plw_unable_to_withdraw'].str.lower() != 'yes'

total_plws = df['cnic'].nunique()
withdrawn_plws = df[df['amount_(rs.)'] > 0]['cnic'].nunique()
eligible_cnic = df[df['eligible']]['cnic'].nunique()
total_withdrawn = df[df['eligible']]['amount_(rs.)'].sum()
incentive_due = df[(df['eligible']) & (df['eligible_for_incentive_(cnic)'].notna())]['incentive_due_(rs.)'].sum()

# 🎯 Summary KPIs
st.markdown("## 📊 PLW Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_plws:,}")
col3.metric("Incentive Eligible (CNIC)", f"{eligible_cnic:,}")

col4, col5 = st.columns(2)
col4.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn):,}")
col5.metric("Incentive Due (Rs.)", f"{int(incentive_due):,}")

# 🥧 PLW Engagement Pie Charts
st.markdown("### 🔄 PLW Engagement Overview")
col1, col2 = st.columns(2)

def make_pie(ax, column, title):
    data = df[column].value_counts()
    colors = ['darkgreen', 'darkred']
    labels = [f"{count:,}, {int((count / data.sum()) * 100)}%" for count in data]
    wedges, texts = ax.pie(data, labels=labels, colors=colors, textprops={'color': "white"}, startangle=90)
    ax.set_title(title)

fig1, axs = plt.subplots(1, 2, figsize=(8, 4))
make_pie(axs[0], 'contact_with_plw', "Contact with PLW")
make_pie(axs[1], 'plw_visited_campsite', "Visited Camp")
col1.pyplot(fig1)

# 🥧 Withdrawal Count
st.markdown("### 💸 Withdrawal Count")
withdrawal_data = {
    'Withdrawn': df[df['amount_(rs.)'] > 0]['cnic'].nunique(),
    'Not Withdrawn': df[df['amount_(rs.)'] <= 0]['cnic'].nunique()
}
fig2, ax2 = plt.subplots()
labels = [f"{v:,}, {int((v/sum(withdrawal_data.values()))*100)}%" for v in withdrawal_data.values()]
colors = ['darkgreen', 'darkred']
ax2.pie(withdrawal_data.values(), labels=labels, colors=colors, startangle=90, textprops={'color': "white"})
ax2.set_title("Withdrawal")
st.pyplot(fig2)

# 📊 PLW Status Horizontal Bar
st.markdown("### 🧭 PLW Status")
status_counts = df['status_of_plw_(nwd_or_pwd)'].value_counts()
fig3, ax3 = plt.subplots(figsize=(7, 3))
bars = ax3.barh(status_counts.index, status_counts.values, color=plt.cm.Paired.colors)
for i, (val, bar) in enumerate(zip(status_counts.values, bars)):
    ax3.text(val + 2, i, f"{val:,}", va='center')
ax3.set_xlabel("Count")
st.pyplot(fig3)

# 📊 Reason for Non-Withdrawal
st.markdown("### 📌 Reason for Non-Withdrawal")
reasons = df['reason_for_non-withdrawal'].dropna().str.strip().value_counts()
fig4, ax4 = plt.subplots(figsize=(8, 4))
bars = ax4.barh(reasons.index, reasons.values, color='darkred')
for i, v in enumerate(reasons.values):
    ax4.text(v + 2, i, str(v), va='center')
ax4.set_xlabel("PLWs")
st.pyplot(fig4)

# 📊 ADFO-wise Withdrawal %
st.markdown("### 📉 ADFO-wise Withdrawal %")
adfo_group = df.groupby('adfo_name')
adfo_stats = adfo_group['amount_(rs.)'].agg(['count', 'sum']).reset_index()
adfo_stats['total'] = adfo_group['cnic'].nunique().values
adfo_stats['percent'] = (adfo_stats['count'] / adfo_stats['total'] * 100).fillna(0).astype(int)

fig5, ax5 = plt.subplots(figsize=(8, 4))
bars = ax5.bar(adfo_stats['adfo_name'], adfo_stats['percent'], color=plt.cm.Set2.colors)
ax5.set_ylabel("Withdrawal %")
ax5.set_xticklabels(adfo_stats['adfo_name'], rotation=45, ha='right')
for i, bar in enumerate(bars):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f"{adfo_stats['percent'][i]}%", ha='center')
st.pyplot(fig5)

# 📊 ADFO Benchmark vs Actual Withdrawal
st.markdown("### 📊 ADFO: Benchmark vs Withdrawn (Rs.)")
df['benchmark'] = df['withdrawal/camp_(rs.)']
group = df.groupby('adfo_name')
benchmark = group['benchmark'].max()
withdrawn = group['amount_(rs.)'].sum()

fig6, ax6 = plt.subplots(figsize=(9, 4))
x = np.arange(len(benchmark))
bar_width = 0.35
bars1 = ax6.bar(x - bar_width/2, benchmark.values, width=bar_width, label='Benchmark', color='darkgreen')
bars2 = ax6.bar(x + bar_width/2, withdrawn.values, width=bar_width, label='Withdrawn', color='darkred')

for i in range(len(benchmark)):
    ax6.text(x[i] - bar_width/2, benchmark.values[i] + 5000, f"{int(benchmark.values[i]):,}", ha='center')
    ax6.text(x[i] + bar_width/2, withdrawn.values[i] + 5000, f"{int(withdrawn.values[i]):,}", ha='center')

ax6.set_ylabel("Rs.")
ax6.set_xticks(x)
ax6.set_xticklabels(benchmark.index, rotation=30)
ax6.legend()
st.pyplot(fig6)
