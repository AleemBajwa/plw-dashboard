import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configurations
st.set_page_config(layout="wide")
st.title("📊 PLW Dashboard")

# Load data
sheet_url = "https://docs.google.com/spreadsheets/d/1cGRESCZ3ShFOF4yzvGdjopUeMRL2Uyk9tWdbg2P63FA/export?format=xlsx"
df = pd.read_excel(sheet_url)

# Clean and standardize
df = df.applymap(lambda x: str(x).strip().lower() if isinstance(x, str) else x)
df["Eligible for Incentive"] = df["Eligible for Incentive"].str.lower()
df["PLW unable to withdraw"] = df["PLW unable to withdraw"].str.lower()

# Filters
districts = df["District"].dropna().unique()
status_options = df["Status of PLW (NWD or PWD)"].dropna().unique()

with st.sidebar:
    selected_districts = st.multiselect("Select District(s)", districts, default=districts)
    selected_statuses = st.multiselect("Select PLW Status", status_options, default=status_options)

filtered_df = df[
    df["District"].isin(selected_districts) & df["Status of PLW (NWD or PWD)"].isin(selected_statuses)
]

# Metrics
total_plws = filtered_df["PLW CNIC No"].nunique()
withdrawn_plws = filtered_df[filtered_df["Amount withdrawn from Camp (Rs.)"] > 0]["PLW CNIC No"].nunique()
not_withdrawn = total_plws - withdrawn_plws

eligible_incentive_df = filtered_df[
    (filtered_df["Eligible for Incentive"] == "yes") & (filtered_df["PLW unable to withdraw"] != "yes")
]
incentive_due = eligible_incentive_df["Amount (Rs.)"].sum()
incentive_cnic = eligible_incentive_df["PLW CNIC No"].nunique()

total_withdrawn_amount = filtered_df["Amount withdrawn from Camp (Rs.)"].sum()

# Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total PLWs (CNIC)", f"{total_plws:,}")
col2.metric("Withdrawn PLWs", f"{withdrawn_plws:,}")
col3.metric("Incentive Eligible (CNIC)", f"{incentive_cnic:,}")

col4, col5 = st.columns(2)
col4.metric("Total Withdrawn (Rs.)", f"{int(total_withdrawn_amount):,}")
col5.metric("Incentive Due (Rs.)", f"{int(incentive_due):,}")

# PIE CHARTS: Contact & Visited
def draw_pie(title, col_name, labels_map, colors):
    counts = filtered_df[col_name].value_counts().to_dict()
    counts = {k.lower(): v for k, v in counts.items()}
    values = [counts.get("yes", 0), counts.get("no", 0)]
    labels = [f"{v:,}, {v / sum(values):.0%}" for v in values]

    fig, ax = plt.subplots()
    wedges, _, autotexts = ax.pie(values, labels=labels, colors=colors, startangle=90, labeldistance=0.5)
    for txt in autotexts:
        txt.set_color("white")
        txt.set_fontsize(10)
    ax.axis("equal")
    ax.set_title(title)
    return fig

st.markdown("### 🔄 PLW Engagement Overview")
col1, col2 = st.columns(2)
with col1:
    st.pyplot(draw_pie("Contact with PLW", "Contact with PLW", ["yes", "no"], ["darkred", "darkgreen"]))
with col2:
    st.pyplot(draw_pie("Visited Camp", "PLW visited the camp", ["yes", "no"], ["darkred", "darkgreen"]))

# PIE CHART: Withdrawal Count
st.markdown("### 💸 Withdrawn Count")
withdrawal_data = [withdrawn_plws, not_withdrawn]
withdrawal_labels = [f"{withdrawn_plws:,}, {withdrawn_plws / total_plws:.0%}",
                     f"{not_withdrawn:,}, {not_withdrawn / total_plws:.0%}"]
colors = ["darkgreen", "darkred"]
fig, ax = plt.subplots()
ax.pie(withdrawal_data, labels=withdrawal_labels, colors=colors, startangle=90, labeldistance=0.5)
for txt in ax.texts:
    txt.set_color("white")
    txt.set_fontsize(10)
ax.axis("equal")
ax.set_title("Withdrawal")
st.pyplot(fig)

# Horizontal Bar Chart: PLW Status
st.markdown("### 🧭 PLW Status")
status_counts = filtered_df["Status of PLW (NWD or PWD)"].value_counts()
fig, ax = plt.subplots()
bars = ax.barh(status_counts.index, status_counts.values, color=plt.cm.Paired.colors)
for bar in bars:
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
            f"{int(bar.get_width()):,}", va='center')
st.pyplot(fig)

# Bar Chart: ADFO Withdrawal %
st.markdown("### 📉 ADFO-wise Withdrawal %")
withdrawal_df = filtered_df.groupby("ADFO Name").agg(
    total=("PLW CNIC No", "nunique"),
    withdrawn=("Amount withdrawn from Camp (Rs.)", lambda x: x.gt(0).sum())
)
withdrawal_df["%"] = (withdrawal_df["withdrawn"] / withdrawal_df["total"] * 100).fillna(0).round(0).astype(int)
withdrawal_df = withdrawal_df.sort_values("%", ascending=False)

fig, ax = plt.subplots()
bars = ax.bar(withdrawal_df.index, withdrawal_df["%"], color=plt.cm.Pastel1.colors)
ax.set_ylabel("Withdrawal %")
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height - 5, f"{height}%", ha='center', va='top', fontsize=10)
plt.xticks(rotation=45, ha='right')
st.pyplot(fig)

# Grouped Bar Chart: ADFO Benchmark vs Withdrawn
st.markdown("### 📊 ADFO: Benchmark vs Withdrawn (Rs.)")
adfo_df = filtered_df.groupby("ADFO Name").agg({
    "ADFO Benchmark: Withdrawal / Camp (Rs.)": "max",
    "Amount withdrawn from Camp (Rs.)": "sum"
}).fillna(0)
fig, ax = plt.subplots()
x = np.arange(len(adfo_df.index))
width = 0.35
bar1 = ax.bar(x - width/2, adfo_df.iloc[:, 0], width, label="Benchmark", color="darkgreen")
bar2 = ax.bar(x + width/2, adfo_df.iloc[:, 1], width, label="Withdrawn", color="darkred")

for bar in bar1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height, f"{int(height):,}", ha='center', va='bottom', fontsize=8)
for bar in bar2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height, f"{int(height):,}", ha='center', va='bottom', fontsize=8)

ax.set_ylabel("Rs.")
ax.set_xticks(x)
ax.set_xticklabels(adfo_df.index, rotation=30, ha='right')
ax.legend()
st.pyplot(fig)

# Horizontal Bar Chart: Reason for Non-Withdrawal
st.markdown("### 📌 Reason for Non-Withdrawal")
reason_counts = filtered_df["Reason for non-withdrawal"].value_counts()
fig, ax = plt.subplots()
bars = ax.barh(reason_counts.index, reason_counts.values, color="darkred")
for bar in bars:
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
            f"{int(bar.get_width()):,}", va='center', color='black')
st.pyplot(fig)
