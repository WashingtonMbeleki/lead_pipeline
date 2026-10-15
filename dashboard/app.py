import sys
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import plotly.express as px
from data_pipeline.db import ApplicationDatabase
from engine.cv_generator import TailoredCVGenerator

st.set_page_config(page_title="Assisted Job Application Engine", layout="wide")

st.title("⚡ Dynamic Job Application & Resume Engine")
st.caption("Custom-generates tailored multi-page CVs directly from master_profile.json")

db = ApplicationDatabase("data/job_applications.db")
cv_gen = TailoredCVGenerator()

master_json_path = "data/master_profile.json"
user_skills = []
if os.path.exists(master_json_path):
    try:
        with open(master_json_path, "r", encoding="utf-8") as f:
            master_data = json.load(f)
            categories = master_data.get("skill_categories", {})
            for skill_list in categories.values():
                if isinstance(skill_list, list):
                    user_skills.extend(skill_list)
    except Exception as err:
        st.warning(f"Could not load master profile: {err}")

def load_data():
    try:
        conn = db.get_connection()
        df_jobs = pd.read_sql_query("SELECT * FROM jobs", conn)
        df_apps = pd.read_sql_query("SELECT * FROM applications", conn)
        conn.close()

        if not df_jobs.empty and not df_apps.empty:
            return pd.merge(df_apps, df_jobs, on="job_id", how="inner")
        return pd.DataFrame()
    except Exception as err:
        st.error(f"Error reading SQLite database: {err}")
        return pd.DataFrame()

df_merged = load_data()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Leads Discovered", len(df_merged))
with col2:
    high_match = len(df_merged[df_merged["match_score"] >= 0.80]) if not df_merged.empty else 0
    st.metric("High Match Leads (≥80%)", high_match)
with col3:
    applied_count = len(df_merged[df_merged["status"] == "APPLIED"]) if not df_merged.empty else 0
    st.metric("Applications Submitted", applied_count)
with col4:
    avg_score = f"{df_merged['match_score'].mean():.2f}" if not df_merged.empty else "0.00"
    st.metric("Avg Match Score", avg_score)

st.divider()

if not df_merged.empty:
    tab1, tab2, tab3 = st.tabs(["🚀 Lead Feed & Tailored CVs", "📊 Funnel Analytics", "📋 Data Ledger"])

    with tab1:
        st.subheader("Interactive Application Feed")
        
        f_col1, f_col2 = st.columns([2, 1])
        with f_col1:
            min_score = st.slider("Filter Minimum Match Score:", 0.50, 1.00, 0.70, step=0.05)
        with f_col2:
            status_filter = st.selectbox("Show Status:", ["DISCOVERED", "APPLIED", "REJECTED"])

        filtered_df = df_merged[
            (df_merged["match_score"] >= min_score) & 
            (df_merged["status"] == status_filter)
        ].sort_values(by="match_score", ascending=False)

        if not filtered_df.empty:
            for idx, row in filtered_df.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    
                    with c1:
                        st.markdown(f"### {row['title']}")
                        st.caption(f"🏢 **{row['company']}** | 📍 {row['location']}")
                        
                        raw_reason = row['failure_reason']
                        if pd.isna(raw_reason) or not isinstance(raw_reason, str):
                            matched_skills = "General Profile Alignment"
                        else:
                            matched_skills = raw_reason

                        st.markdown(f"🎯 **Matched Keywords:** `{matched_skills}`")
                    
                    with c2:
                        st.metric("Match Score", f"{row['match_score']:.2f}")
                    
                    with c3:
                        st.link_button("Open Link ↗", row["job_url"])
                        
                        if st.button("📄 Generate Custom CV", key=f"gen_cv_{row['job_id']}"):
                            skills_list = [s.strip() for s in matched_skills.split(",") if s.strip()] if matched_skills != "General Profile Alignment" else user_skills[:6]

                            pdf_path = cv_gen.generate_cv_pdf(
                                job_title=row['title'],
                                company=row['company'],
                                matched_skills=skills_list,
                                job_description=row.get('description', '')
                            )
                            st.session_state[f"ready_pdf_{row['job_id']}"] = pdf_path

                        if f"ready_pdf_{row['job_id']}" in st.session_state:
                            pdf_path = st.session_state[f"ready_pdf_{row['job_id']}"]
                            if os.path.exists(pdf_path):
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        label="📥 Download Tailored CV",
                                        data=f,
                                        file_name=os.path.basename(pdf_path),
                                        mime="application/pdf",
                                        key=f"dl_pdf_{row['job_id']}"
                                    )

                        if status_filter == "DISCOVERED":
                            if st.button("Mark Applied ✅", key=f"app_{row['job_id']}"):
                                db.update_application_status(row['job_id'], "APPLIED")
                                st.rerun()
                            if st.button("Skip / Reject ❌", key=f"rej_{row['job_id']}"):
                                db.update_application_status(row['job_id'], "REJECTED")
                                st.rerun()
        else:
            st.info(f"No leads found matching score ≥ {min_score} with status '{status_filter}'.")

    with tab2:
        st.subheader("Analytics")
        an_col1, an_col2 = st.columns(2)
        with an_col1:
            status_counts = df_merged["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig_funnel = px.bar(status_counts, x="Status", y="Count", title="Pipeline Funnel", color="Status")
            st.plotly_chart(fig_funnel, use_container_width=True)
        with an_col2:
            fig_hist = px.histogram(df_merged, x="match_score", nbins=10, title="Match Score Distribution", color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_hist, use_container_width=True)

    with tab3:
        st.subheader("Database Ledger")
        st.dataframe(
            df_merged[["title", "company", "location", "match_score", "status", "failure_reason", "job_url"]],
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("No job records found. Run pipeline scraper to ingest leads.")