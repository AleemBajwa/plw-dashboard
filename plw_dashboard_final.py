
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Load Google Sheet Data
sheet_url = 'https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/gviz/tq?tqx=out:csv'
df = pd.read_csv(sheet_url)

# Standardize case and handle nulls
df = df.applymap(lambda x: x.lower().strip() if isinstance(x, str) else x)

# Fix numeric conversions
df['Amount (Rs.)'] = pd.to_numeric(df['Amount (Rs.)'], errors='coerce').fillna(0)
df['Eligible for Incentive'] = pd.to_numeric(df['Eligible for Incentive'], errors='coerce').fillna(0)

# Sidebar Filters
st.sidebar.header("Filter Data")
districts = st.sidebar.multiselect("Select District(s)", options=df['District'].dropna().unique(), default=df['District'].dropna().unique())
adfos = st.sidebar.multiselect("Select ADFO(s)", options=df['ADFO Name'].dropna().unique(), default=df['ADFO Name'].dropna().unique())
statuses = st.sidebar.multiselect("PLW Status (NWD or PWD)", options=df['Status of PLW (NWD or PWD)'].dropna().unique(), default=df['Status of PLW (NWD or PWD)'].dropna().unique())

# Apply Filters
df_filtered = df[df['District'].isin(districts) & df['ADFO Name'].isin(adfos) & df['Status of PLW (NWD or PWD)'].isin(statuses)]

# Eligibility logic
eligible_df = df_filtered[df_filtered['plw unable to withdraw'] != 'yes']

# Summary Metrics
total_plws = df_filtered['plw cnic no'].nunique()
withdrawn_count = df_filtered[df_filtered['amount (rs.)'] > 0]['plw cnic no'].nunique()
eligible_count = eligible_df[eligible_df['eligible for incentive'] == 'yes']['plw cnic no'].nunique()
total_withdrawn = df_filtered['amount (rs.)'].sum()
incentive_due = eligible_df[eligible_df['eligible for incentive'] == 'yes']['incentive'].sum()
not_withdrawn = total_plws - withdrawn_count

# Show Summary
st.title("📊 PLW Dashboard")
c1, c2, c3 = st.columns(3)
c1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
c2.metric("Withdrawn PLWs", f"{withdrawn_count:,}")
c3.metric("Incentive Eligible (CNIC)", f"{eligible_count:,}")

c4, c5, c6 = st.columns(3)
c4.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn):,}")
c5.metric("Incentive Due (Rs.)", f"{int(incentive_due):,}")
c6.metric("Not Withdrawn PLWs", f"{not_withdrawn:,}")

# Pie Chart Helper
def pie_chart(data, title, labels, colors):
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(data, labels=None, autopct='', colors=colors, startangle=90)
    for i, a in enumerate(autotexts):
        label = f"{data[i]:,}, {int(round(data[i]/sum(data)*100))}%"
        a.set_text(label)
        a.set_color('white')
        a.set_fontsize(12)
    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5))
    ax.set_title(title, fontsize=16)
    st.pyplot(fig)

# Pie Charts
yes_no = ['yes', 'no']
colors = ['darkred', 'darkgreen']

col1, col2 = st.columns(2)
with col1:
    contact_vals = df_filtered['contact with plw'].value_counts().reindex(yes_no).fillna(0).astype(int)
    pie_chart(contact_vals.values, "Contact with PLW", [f"{k}" for k in contact_vals.index], colors[::-1])

with col2:
    camp_vals = df_filtered['plw visited campsite'].value_counts().reindex(yes_no).fillna(0).astype(int)
    pie_chart(camp_vals.values, "Visited Camp", [f"{k}" for k in camp_vals.index], colors[::-1])

# Withdrawn Count Pie
withdrawn_vals = [withdrawn_count, not_withdrawn]
labels = ['Withdrawn', 'Not Withdrawn']
colors2 = ['darkgreen', 'darkred']
pie_chart(withdrawn_vals, "Withdrawal", labels, colors2)

# Horizontal Bar: PLW Status
st.subheader("🧭 PLW Status")
status_counts = df_filtered['status of plw (nwd or pwd)'].value_counts()
fig1, ax1 = plt.subplots()
bars = ax1.barh(status_counts.index, status_counts.values, color=plt.cm.Set2.colors)
for bar in bars:
    ax1.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f"{int(bar.get_width())}", va='center')
st.pyplot(fig1)

# ADFO-wise Withdrawal %
st.subheader("📉 ADFO-wise Withdrawal %")
grouped = df_filtered.groupby('adfo name').agg({'amount (rs.)': 'sum', 'plw cnic no': pd.Series.nunique})
grouped['withdrawal %'] = (grouped['amount (rs.)'] > 0).astype(int) * 100
fig2, ax2 = plt.subplots()
bars = ax2.bar(grouped.index, grouped['withdrawal %'], color=plt.cm.Paired.colors)
for bar in bars:
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{int(bar.get_height())}%", ha='center', va='bottom')
plt.xticks(rotation=30, ha='right')
st.pyplot(fig2)

# ADFO Benchmark vs Withdrawn
st.subheader("📊 ADFO: Benchmark vs Withdrawn (Rs.)")
adfo_group = df_filtered.groupby('adfo name').agg({'amount (rs.)': 'sum', 'withdrawal / camp (rs.)': 'max'}).reset_index()
fig3, ax3 = plt.subplots()
bar1 = ax3.bar(adfo_group['adfo name'], adfo_group['withdrawal / camp (rs.)'], label='Benchmark', color='darkgreen')
bar2 = ax3.bar(adfo_group['adfo name'], adfo_group['amount (rs.)'], label='Withdrawn', color='darkred')
ax3.set_ylabel("Rs.")
ax3.legend()
for i in range(len(bar1)):
    ax3.text(bar1[i].get_x(), bar1[i].get_height(), f"{int(bar1[i].get_height()):,}", ha='left', va='bottom')
    ax3.text(bar2[i].get_x()+0.2, bar2[i].get_height(), f"{int(bar2[i].get_height()):,}", ha='left', va='bottom')
plt.xticks(rotation=30, ha='right')
st.pyplot(fig3)

# Reason for Non-Withdrawal
st.subheader("📌 Reason for Non-Withdrawal")
reasons = df_filtered['reason for non withdrawal'].dropna().value_counts()
fig4, ax4 = plt.subplots()
bars = ax4.barh(reasons.index, reasons.values, color='darkred')
for bar in bars:
    ax4.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f"{int(bar.get_width())}", va='center', ha='left')
st.pyplot(fig4)
