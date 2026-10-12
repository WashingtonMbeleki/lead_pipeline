import json
import os
import sqlite3
import pandas as pd
import streamlit as st

# Configure Page
st.set_page_config(
    page_title="Data Quality Sentinel | Operational Dashboard",
    page_icon="🛡️",
    layout="wide"
)

DB_PATH = "data/processed/financial_warehouse.db"
DEAD_LETTER_PATH = "logs/dead_letter_queue.json"


@st.cache_data(ttl=5)
def load_warehouse_data():
    """Loads clean transactions from SQLite warehouse."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM transactions", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


@st.cache_data(ttl=5)
def load_dead_letter_data():
    """Loads quarantined records from the dead-letter JSON queue."""
    if not os.path.exists(DEAD_LETTER_PATH):
        return []
    try:
        with open(DEAD_LETTER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception:
        return []


# Title & Header
st.title("🛡️ Data Quality Sentinel: Operations Dashboard")
st.markdown(
    "Live operational monitoring of ingested South African financial transaction batches and automated quarantine routing."
)

st.divider()

# Refresh Control
if st.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

# Load Data
clean_df = load_warehouse_data()
quarantine_list = load_dead_letter_data()

total_clean = len(clean_df)
total_quarantined = len(quarantine_list)
total_processed = total_clean + total_quarantined
pass_rate = (total_clean / total_processed * 100) if total_processed > 0 else 0.0

# ----------------------------------------------------
# Executive Metrics Cards
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Batched Records", f"{total_processed:,}")

with col2:
    st.metric("Clean Ingested Records", f"{total_clean:,}", delta=f"{pass_rate:.1f}% Passed")

with col3:
    st.metric("Quarantined Records", f"{total_quarantined:,}", delta=f"{100 - pass_rate:.1f}% Quarantined", delta_color="inverse")

with col4:
    total_val = clean_df["amount"].sum() if not clean_df.empty and "amount" in clean_df.columns else 0.0
    st.metric("Clean Settlement Value", f"R {total_val:,.2f}")

st.divider()

# ----------------------------------------------------
# Main Dashboard Body Tabs
# ----------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Warehouse Analytics", "🚨 Quarantine & Anomaly Log", "🔍 Data Quality Rules"])

# TAB 1: Clean Warehouse Analytics
with tab1:
    st.subheader("Clean Data Warehouse (SQLite)")
    
    if clean_df.empty:
        st.info("No data currently available in SQLite warehouse.")
    else:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("#### Transaction Volume by Merchant")
            merchant_counts = clean_df["merchant_name"].value_counts().head(10)
            st.bar_chart(merchant_counts)

        with col_right:
            st.markdown("#### Volume by Payment Channel")
            channel_counts = clean_df["channel"].value_counts()
            st.bar_chart(channel_counts)

        st.markdown("#### Recent Clean Records")
        st.dataframe(
            clean_df.sort_values(by="timestamp", ascending=False).head(50),
            width="stretch"
        )

# TAB 2: Quarantined Records
with tab2:
    st.subheader("Quarantined Anomaly Inspector (Dead Letter Queue)")
    
    if not quarantine_list:
        st.success("No records currently quarantined in the dead-letter queue!")
    else:
        quarantine_df = pd.DataFrame(quarantine_list)
        
        # Explode quarantine reasons for analysis
        reasons_flat = []
        for item in quarantine_list:
            reasons_flat.extend(item.get("quarantine_reasons", ["UNKNOWN"]))
        
        reason_counts = pd.Series(reasons_flat).value_counts()
        
        col_q1, col_q2 = st.columns([1, 2])
        
        with col_q1:
            st.markdown("#### Top Anomaly Root Causes")
            st.dataframe(reason_counts.rename("Count"), width="stretch")
            
        with col_q2:
            st.markdown("#### Anomaly Breakdown Chart")
            st.bar_chart(reason_counts)

        st.markdown("#### Quarantined Payload Inspector")
        st.dataframe(quarantine_df, width="stretch")

# TAB 3: Data Quality Specification Reference
with tab3:
    st.subheader("Active Data Quality Assertions")
    
    rules_data = [
        {"Column": "transaction_id", "Assertion": "Non-null, string identifier", "Action on Fail": "Quarantine"},
        {"Column": "account_number", "Assertion": "10-digit identifier, non-null", "Action on Fail": "Quarantine"},
        {"Column": "currency", "Assertion": "Must strictly equal 'ZAR'", "Action on Fail": "Quarantine"},
        {"Column": "amount", "Assertion": "Must be positive numeric value (> 0.00)", "Action on Fail": "Quarantine"},
        {"Column": "vat_amount", "Assertion": "Must not exceed transaction amount", "Action on Fail": "Quarantine"},
        {"Column": "status", "Assertion": "Allowed: ['SUCCESS', 'FAILED', 'PENDING']", "Action on Fail": "Quarantine"},
        {"Column": "channel", "Assertion": "Allowed SA payment channels", "Action on Fail": "Quarantine"},
    ]
    st.dataframe(pd.DataFrame(rules_data), width="stretch")