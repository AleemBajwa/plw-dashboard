import streamlit as st
st.set_page_config(layout="wide")  # 🔥 MUST be placed right after the import of Streamlit
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from textwrap import wrap


# --- Load data ---
url = "https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=xlsx"
df = pd.read_excel(url)

# --- Standardize boolean-like text fields ---
df = df.applymap(lambda x: str(x).strip().lower() if isinstance(x, str) else x)

# --- Filter logic ---
st.sidebar.header("Filters")
districts = st.sidebar.multiselect("Select District(s):", options=df['District'].unique(), default=df['District'].unique())
statuses = st.sidebar.multiselect("Select Status of PLW:", options=df['Status of PLW (NWD or PWD)'].unique(), default=df['Status of PLW (NWD or PWD)'].unique())

filtered_df = df[df['District'].isin(districts) & df['Status of PLW (NWD or PWD)'].isin(statuses)]

# --- Metrics Calculations ---
total_plws = filtered_df['PLW CNIC No'].nunique()
withdrawn_plws = filtered_df[filtered_df['Amount withdrawn from Camp (Rs.)'] > 0]['PLW CNIC No'].nunique()
not_withdrawn = total_plws - withdrawn_plws

# Incentive logic: eligible = 'yes' and unable_to_withdraw ≠ 'yes'
eligible_mask = (filtered_df['Eligible for Incentive'] == 'yes') & (filtered_df['PLW unable to withdraw'] != 'yes')
incentive_count = filtered_df[eligible_mask]['PLW CNIC No'].nunique()
incentive_due = filtered_df[eligible_mask]['Amount (Rs.)'].sum()

# Total withdrawn amount
total_withdrawn = filtered_df['Amount withdrawn from Camp (Rs.)'].sum()

# --- Streamlit Page Setup ---
st.set_page_config(layout="wide")
st.markdown("<h1 style='font-size:40px;'>📊 PLW Dashboard</h1>", unsafe_allow_html=True)

# --- Summary Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_plws:,}")
col3.metric("Incentive Eligible (CNIC)", f"{incentive_count:,}")

col4, col5 = st.columns(2)
col4.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn):,}")
col5.metric("Incentive Due (Rs.)", f"{int(incentive_due):,}")

st.markdown("---")

# --- Pie Chart Helper ---
def plot_pie(data, labels, colors, title):
    fig, ax = plt.subplots()
    wedges, _, autotexts = ax.pie(
        data, labels=None, autopct='%1.0f%%', colors=colors, startangle=90,
        textprops={'color': 'white', 'fontsize': 14}
    )
    for i, a in enumerate(autotexts):
        a.set_text(f"{data[i]:,}, {a.get_text()}")
    ax.axis('equal')
    ax.set_title(title, fontsize=16)
    return fig

# --- Pie Charts ---
col1, col2 = st.columns(2)

with col1:
    contact_counts = filtered_df['Contact with PLW'].value_counts().reindex(['no', 'yes']).fillna(0)
    fig1 = plot_pie(contact_counts.values, contact_counts.index, ['darkgreen', 'darkred'], "Contact with PLW")
    st.markdown("### 🔗 PLW Engagement Overview")
    st.pyplot(fig1)

with col2:
    visit_counts = filtered_df['PLW visited the Camp'].value_counts().reindex(['no', 'yes']).fillna(0)
    fig2 = plot_pie(visit_counts.values, visit_counts.index, ['darkgreen', 'darkred'], "Visited Camp")
    st.pyplot(fig2)

col3, col4 = st.columns(2)
with col3:
    withdrawn_counts = [withdrawn_plws, not_withdrawn]
    fig3 = plot_pie(withdrawn_counts, ['Withdrawn', 'Not Withdrawn'], ['darkgreen', 'darkred'], "Withdrawal")
    st.markdown("### 💵 Withdrawn Count")
    st.pyplot(fig3)

# --- PLW Status Horizontal Bar ---
status_counts = filtered_df['Status of PLW (NWD or PWD)'].value_counts()
fig4, ax4 = plt.subplots(figsize=(6, 3))
bars = ax4.barh(status_counts.index, status_counts.values, color=plt.cm.Set2.colors)
for bar in bars:
    ax4.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width()):,}", va='center')
ax4.set_xlabel("Count")
ax4.set_title("📍 PLW Status")
st.pyplot(fig4)

# --- ADFO-wise Withdrawal % ---
withdraw_df = filtered_df.copy()
grouped = withdraw_df.groupby('ADFO Name')
percentages = (grouped.apply(lambda x: (x['Amount withdrawn from Camp (Rs.)'] > 0).sum() / x['PLW CNIC No'].nunique()) * 100).sort_values()
fig5, ax5 = plt.subplots(figsize=(8, 4))
bars = ax5.bar(percentages.index, percentages.values.round(0), color=plt.cm.Pastel1.colors)
ax5.set_title("📉 ADFO-wise Withdrawal %")
ax5.set_ylabel("Withdrawal %")
ax5.set_xticks(np.arange(len(percentages.index)))
ax5.set_xticklabels(['\n'.join(wrap(label, 12)) for label in percentages.index], rotation=45, ha='right')
for bar in bars:
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 5, f"{int(bar.get_height())}%", ha='center', color='black')
st.pyplot(fig5)

# --- ADFO-wise Benchmark vs Withdrawn ---
benchmark = grouped['ADFO Benchmark: Withdrawal / Camp (Rs.)'].max()
actual = grouped['Amount withdrawn from Camp (Rs.)'].sum()
labels = benchmark.index
x = np.arange(len(labels))
width = 0.35
fig6, ax6 = plt.subplots(figsize=(8, 4))
b1 = ax6.bar(x - width/2, benchmark.values, width, label='Benchmark', color='darkgreen')
b2 = ax6.bar(x + width/2, actual.values, width, label='Withdrawn', color='darkred')
ax6.set_ylabel("Rs.")
ax6.set_title("📊 ADFO: Benchmark vs Withdrawn")
ax6.set_xticks(x)
ax6.set_xticklabels(['\n'.join(wrap(label, 12)) for label in labels], rotation=0)
ax6.legend()
for bar in b1 + b2:
    ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{int(bar.get_height()):,}", ha='center', va='bottom', fontsize=8)
st.pyplot(fig6)

# --- Reason for Non-Withdrawal ---
reasons = filtered_df['Reason for non-withdrawal'].value_counts()
fig7, ax7 = plt.subplots(figsize=(8, 4))
bars = ax7.barh(reasons.index, reasons.values, color='darkred')
for bar in bars:
    ax7.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2, f"{int(bar.get_width()):,}", va='center')
ax7.set_title("📌 Reason for Non-Withdrawal")
ax7.set_xlabel("PLWs")
st.pyplot(fig7)
