import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="PLW Dashboard", layout="wide")

# --- Load data from Google Sheets (live) ---
@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1GWJGHmXkJph1-xn7-5Z8ATfYzvnEP9K_/export?format=xlsx"
    df = pd.read_excel(url)
    df['Date of Camp'] = pd.to_datetime(df['Date of Camp'], errors='coerce')
    df['PLW CNIC No'] = df['PLW CNIC No'].astype(str)
    df['Eligible for Incentive'] = df['Eligible for Incentive'].astype(str).str.lower()
    df['Contact with PLW (Y/N)'] = df['Contact with PLW (Y/N)'].astype(str).str.lower()
    df['PLW visited the Campsite'] = df['PLW visited the Campsite'].astype(str).str.lower()
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.title("🔘 Filters")
districts = ["All"] + sorted(df["District"].dropna().unique())
adfos = ["All"] + sorted(df["ADFO Name"].dropna().unique())

selected_district = st.sidebar.selectbox("Select District", districts)
selected_adfo = st.sidebar.selectbox("Select ADFO", adfos)
date_range = st.sidebar.date_input("Select Date Range", [])

# --- Apply Filters ---
filtered_df = df.copy()
if selected_district != "All":
    filtered_df = filtered_df[filtered_df["District"] == selected_district]
if selected_adfo != "All":
    filtered_df = filtered_df[filtered_df["ADFO Name"] == selected_adfo]
if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range)
    filtered_df = filtered_df[(filtered_df["Date of Camp"] >= start_date) & (filtered_df["Date of Camp"] <= end_date)]

# --- Summary KPIs ---
total_cnic = filtered_df["PLW CNIC No"].nunique()
withdrawn_cnic = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0]["PLW CNIC No"].nunique()
not_withdrawn = total_cnic - withdrawn_cnic
total_withdrawn_amount = filtered_df["Amount withdrawn from Camp (Rs.)"].sum()

eligible_df = filtered_df[filtered_df["Eligible for Incentive"] == "yes"]
eligible_cnic = eligible_df["PLW CNIC No"].nunique()
eligible_amount = eligible_df["Amount (Rs.)"].sum()

st.title("📊 PLW Dashboard")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total PLWs (CNIC)", f"{total_cnic:,}")
    st.metric("Withdrawn PLWs (CNIC)", f"{withdrawn_cnic:,}")
with col2:
    st.metric("Not Withdrawn", f"{not_withdrawn:,}")
    st.metric("Total Withdrawn Amount", f"Rs. {int(total_withdrawn_amount):,}")
with col3:
    st.metric("Eligible for Incentive (CNIC)", f"{eligible_cnic:,}")
    st.metric("Incentive Amount (Rs.)", f"Rs. {int(eligible_amount):,}")

# --- Visuals ---
st.subheader("📈 Visuals")

col_v1, col_v2 = st.columns(2)

with col_v1:
    st.markdown("**Withdrawal Status**")
    total = total_cnic
    withdrawn = withdrawn_cnic
    not_withdrawn = total - withdrawn
    values = [withdrawn, not_withdrawn]
    labels = ["Withdrawn", "Not Withdrawn"]
    percentages = [f"{v / total * 100:.1f}%" for v in values]

    fig1, ax1 = plt.subplots()
    bars = ax1.bar(labels, values, color=["#4CAF50", "#FF5252"])
    for bar, pct, val in zip(bars, percentages, values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                 f"{val} ({pct})", ha="center", fontsize=10)
    ax1.set_ylabel("PLWs")
    st.pyplot(fig1)

with col_v2:
    st.markdown("**Contact with PLW**")
    contact_counts = filtered_df["Contact with PLW (Y/N)"].value_counts()
    contact_labels = contact_counts.index
    contact_values = contact_counts.values
    total_contact = sum(contact_values)
    pie_labels = [f"{lbl}: {val} ({val / total_contact:.0%})" for lbl, val in zip(contact_labels, contact_values)]

    fig2, ax2 = plt.subplots()
    ax2.pie(contact_values, labels=pie_labels, autopct='', colors=["#03A9F4", "#FFC107"])
    ax2.axis("equal")
    st.pyplot(fig2)

# --- Visited Campsite Pie ---
st.markdown("**PLW Visited Campsite**")
visit_counts = filtered_df["PLW visited the Campsite"].value_counts()
visit_labels = visit_counts.index
visit_values = visit_counts.values
total_visit = sum(visit_values)
pie_labels = [f"{lbl}: {val} ({val / total_visit:.0%})" for lbl, val in zip(visit_labels, visit_values)]

fig3, ax3 = plt.subplots()
ax3.pie(visit_values, labels=pie_labels, autopct='', colors=["#8BC34A", "#FF7043"])
ax3.axis("equal")
st.pyplot(fig3)

# --- ADFO-wise Withdrawal % ---
st.markdown("### 🧱 ADFO-wise Withdrawal %")
grouped = filtered_df.groupby("ADFO Name")
total_by_adfo = grouped["PLW CNIC No"].nunique()
withdraw_by_adfo = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0].groupby("ADFO Name")["PLW CNIC No"].nunique()
withdraw_pct = (withdraw_by_adfo / total_by_adfo * 100).fillna(0)

fig4, ax4 = plt.subplots(figsize=(10, 4))
bars = ax4.bar(withdraw_pct.index, withdraw_pct.values, color="#607D8B")
for bar, pct in zip(bars, withdraw_pct.values):
    ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
             f"{pct:.1f}%", ha="center", fontsize=9)
ax4.set_ylabel("Withdrawal %")
ax4.set_xlabel("ADFO Name")
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
st.pyplot(fig4)

# --- Table Viewer ---
st.markdown("### 📋 Detailed Table View")
st.dataframe(filtered_df)
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Filtered Data", data=csv, file_name="filtered_data.csv")
