import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Cybersecurity Awareness Dashboard", page_icon="🔐", layout="wide")
st.title("🔐 Cybersecurity Awareness Dashboard")
st.caption("Descriptive analysis of student responses")

CORRECT = {
    "Q1_Cybersecurity_Meaning": "Protecting computers, networks and data",
    "Q2_Phishing_Recognition": "A fraudulent message designed to steal information",
    "Q3_Suspicious_Link_Action": "Do not click; verify the sender or website",
    "Q4_Malware_Meaning": "Software designed to harm or access a device without permission",
    "Q5_Online_Fraud_Recognition": "Unexpected request for money or confidential details",
    "Q6_Fake_Website_Check": "Check the web address and site security; verify independently",
    "Q7_Cybercrime_Response": "Report it to the appropriate platform or authority",
}

uploaded = st.sidebar.file_uploader("Upload your questionnaire CSV", type="csv")
if uploaded is None:
    st.info("Upload your 100-student CSV file to open the dashboard.")
    st.write("The CSV should contain the questionnaire columns, including Q1–Q7, Q8–Q11, Year_of_Study, Field_of_Study and Daily_Internet_Use.")
    st.stop()

try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Unable to read CSV: {e}")
    st.stop()

missing = [c for c in CORRECT if c not in df.columns]
if missing:
    st.error("Missing required knowledge-question columns:")
    st.write(missing)
    st.stop()

for col in CORRECT:
    df[col] = df[col].astype("string").str.strip()

df["Awareness_Score"] = sum(
    (df[col] == answer).fillna(False).astype(int)
    for col, answer in CORRECT.items()
)
df["Awareness_Percentage"] = df["Awareness_Score"] / 7 * 100
df["Awareness_Level"] = pd.cut(
    df["Awareness_Score"],
    bins=[-1, 2, 5, 7],
    labels=["Low", "Moderate", "High"]
)

st.sidebar.header("Student group filters")
filtered = df.copy()
for col in ["Year_of_Study", "Field_of_Study", "Daily_Internet_Use"]:
    if col in filtered.columns:
        vals = sorted(filtered[col].dropna().astype(str).unique())
        chosen = st.sidebar.multiselect(col.replace("_", " "), vals, default=vals)
        filtered = filtered[filtered[col].astype(str).isin(chosen)]

if filtered.empty:
    st.warning("No students match the selected filters.")
    st.stop()

a, b, c, d = st.columns(4)
a.metric("Students", len(filtered))
b.metric("Mean score", f"{filtered['Awareness_Score'].mean():.2f} / 7")
c.metric("Mean percentage", f"{filtered['Awareness_Percentage'].mean():.2f}%")
d.metric("High awareness", int((filtered["Awareness_Level"] == "High").sum()))

overview, phishing, passwords, groups, records = st.tabs([
    "Overview", "Phishing & knowledge", "Password practices", "Student groups", "Student records"
])

with overview:
    st.subheader("Awareness level distribution")
    order = ["Low", "Moderate", "High"]
    counts = filtered["Awareness_Level"].value_counts().reindex(order, fill_value=0).rename_axis("Awareness level").reset_index(name="Students")
    counts["Percentage"] = (counts["Students"] / len(filtered) * 100).round(1)
    left, right = st.columns(2)
    with left:
        fig = px.bar(counts, x="Awareness level", y="Students", text="Students", category_orders={"Awareness level": order}, title="Students by awareness level")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.pie(counts, names="Awareness level", values="Students", hole=0.35, title="Awareness-level share")
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(counts, use_container_width=True, hide_index=True)

    score_counts = filtered["Awareness_Score"].value_counts().reindex(range(8), fill_value=0).rename_axis("Score out of 7").reset_index(name="Students")
    fig = px.bar(score_counts, x="Score out of 7", y="Students", text="Students", title="Distribution of awareness scores")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True)

with phishing:
    st.subheader("Phishing knowledge")
    col = "Q2_Phishing_Recognition"
    p = filtered[col].fillna("No response").value_counts().rename_axis("Response").reset_index(name="Students")
    p["Percentage"] = (p["Students"] / len(filtered) * 100).round(1)
    correct_n = int((filtered[col] == CORRECT[col]).sum())
    st.metric("Correctly identified phishing", f"{correct_n} ({correct_n / len(filtered) * 100:.1f}%)")
    st.plotly_chart(px.bar(p, x="Students", y="Response", orientation="h", text="Students", title="Responses to the phishing question"), use_container_width=True)
    st.dataframe(p, use_container_width=True, hide_index=True)

    rows = []
    for q, answer in CORRECT.items():
        n = int((filtered[q] == answer).sum())
        rows.append({"Question": q.replace("_", " "), "Correct responses": n, "Correct (%)": round(n / len(filtered) * 100, 1)})
    knowledge = pd.DataFrame(rows)
    st.plotly_chart(px.bar(knowledge, x="Correct (%)", y="Question", orientation="h", text="Correct (%)", title="Correct response rate by knowledge question"), use_container_width=True)
    st.dataframe(knowledge, use_container_width=True, hide_index=True)

with passwords:
    st.subheader("Password and account-security practices")
    practice_labels = {
        "Q8_Use_Different_Passwords": "Uses different passwords",
        "Q9_Strong_Password_Use": "Uses strong passwords",
        "Q10_MFA_Enabled": "Enables multi-factor authentication",
        "Q11_Share_Passwords": "Shares passwords",
    }
    available = [q for q in practice_labels if q in filtered.columns]
    if not available:
        st.warning("Password-practice columns were not found.")
    else:
        selected = st.selectbox("Select a practice", available, format_func=lambda x: practice_labels[x])
        vals = filtered[selected].fillna("No response").value_counts().rename_axis("Response").reset_index(name="Students")
        vals["Percentage"] = (vals["Students"] / len(filtered) * 100).round(1)
        st.plotly_chart(px.bar(vals, x="Response", y="Students", text="Students", title=practice_labels[selected]), use_container_width=True)
        st.dataframe(vals, use_container_width=True, hide_index=True)
    st.caption("Self-reported practices are analysed separately from the objective knowledge score.")

with groups:
    st.subheader("Differences between student groups")
    group_cols = [q for q in ["Year_of_Study", "Field_of_Study", "Daily_Internet_Use"] if q in filtered.columns]
    if not group_cols:
        st.warning("No student-group columns were found.")
    else:
        group = st.selectbox("Group students by", group_cols, format_func=lambda x: x.replace("_", " "))
        summary = filtered.groupby(group, dropna=False).agg(
            Students=("Awareness_Score", "size"),
            Mean_Score=("Awareness_Score", "mean"),
            Mean_Percentage=("Awareness_Percentage", "mean")
        ).reset_index()
        summary["Mean_Score"] = summary["Mean_Score"].round(2)
        summary["Mean_Percentage"] = summary["Mean_Percentage"].round(1)
        st.plotly_chart(px.bar(summary, x=group, y="Mean_Score", text="Mean_Score", title=f"Mean awareness score by {group.replace('_', ' ').lower()}"), use_container_width=True)
        st.dataframe(summary, use_container_width=True, hide_index=True)
        st.caption("These are descriptive comparisons; they do not establish cause and effect.")

with records:
    st.subheader("Student-level awareness scores")
    display = [q for q in ["Student_ID", "Year_of_Study", "Field_of_Study", "Daily_Internet_Use", "Awareness_Score", "Awareness_Percentage", "Awareness_Level"] if q in filtered.columns]
    table = filtered[display].copy()
    table["Awareness_Percentage"] = table["Awareness_Percentage"].round(2)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Download filtered scores as CSV", table.to_csv(index=False).encode("utf-8"), "awareness_scores.csv", "text/csv")

st.divider()
st.caption("Awareness score is based only on Q1–Q7. Password practices, experiences and self-assessment are reported separately. If the responses are synthetic, describe the findings as illustrative rather than actual survey results.")
