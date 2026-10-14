import json
import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# Configure Page
st.set_page_config(
    page_title="Data Quality Sentinel | Operational Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Metric Cards & General Spacing
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #1e222a;
        padding: 16px;
        border-radius: 10px;
        border-left: 5px solid #2e7d32;
    }
    div[data-testid="stMetric"]:nth-child(3) {
        border-left-color: #c62828;
    }
</style>
""", unsafe_allow_html=True)

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


# Load Data
clean_df = load_warehouse_data()
quarantine_list = load_dead_letter_data()

total_clean = len(clean_df)
total_quarantined = len(quarantine_list)
total_processed = total_clean + total_quarantined
pass_rate = (total_clean / total_processed * 100) if total_processed > 0 else 0.0


# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Operational Controls")
    
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.divider()
    
    st.subheader("📌 Quick Stats")
    st.caption(f"**Database:** {'Connected' if not clean_df.empty else 'No DB Found'}")
    st.caption(f"**Quarantine Count:** {total_quarantined} items")


# --- TITLE & HEADER ---
st.title("🛡️ Data Quality Sentinel: Operations Dashboard")
st.caption("Live operational monitoring of ingested South African financial transaction batches and automated quarantine routing.")

st.divider()


# ----------------------------------------------------
# Executive Metrics Cards
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Batched Records", f"{total_processed:,}")

with col2:
    st.metric("Clean Ingested Records", f"{total_clean:,}", delta=f"{pass_rate:.1f}% Passed")

with col3:
    st.metric(
        "Quarantined Records", 
        f"{total_quarantined:,}", 
        delta=f"{100 - pass_rate:.1f}% Flagged", 
        delta_color="inverse"
    )

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
    st.subheader("Clean Data Warehouse Analytics")
    
    if clean_df.empty:
        st.info("No data currently available in SQLite warehouse.")
    else:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("#### Transaction Volume by Merchant")
            merchant_counts = (
                clean_df["merchant_name"]
                .value_counts()
                .head(10)
                .reset_index()
            )
            merchant_counts.columns = ["Merchant", "Volume"]
            
            fig_merchant = px.bar(
                merchant_counts.sort_values(by="Volume", ascending=True),
                x="Volume",
                y="Merchant",
                orientation="h",
                color="Volume",
                color_continuous_scale="Blues"
            )
            fig_merchant.update_layout(
                showlegend=False, 
                margin=dict(l=10, r=10, t=10, b=10),
                height=350
            )
            st.plotly_chart(fig_merchant, use_container_width=True)

        with col_right:
            st.markdown("#### Volume by Payment Channel")
            channel_counts = (
                clean_df["channel"]
                .value_counts()
                .reset_index()
            )
            channel_counts.columns = ["Channel", "Volume"]
            
            fig_channel = px.bar(
                channel_counts,
                x="Channel",
                y="Volume",
                color="Channel",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_channel.update_layout(
                showlegend=False, 
                margin=dict(l=10, r=10, t=10, b=10),
                height=350
            )
            st.plotly_chart(fig_channel, use_container_width=True)

        st.markdown("#### Recent Clean Records")
        
        display_df = clean_df.sort_values(by="timestamp", ascending=False).head(50)
        
        column_config = {}
        if "amount" in display_df.columns:
            column_config["amount"] = st.column_config.NumberColumn(
                "Amount",
                format="R %.2f"
            )
        if "vat_amount" in display_df.columns:
            column_config["vat_amount"] = st.column_config.NumberColumn(
                "VAT Amount",
                format="R %.2f"
            )
        if "status" in display_df.columns:
            column_config["status"] = st.column_config.SelectboxColumn(
                "Status",
                options=["SUCCESS", "FAILED", "PENDING"]
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )

# TAB 2: Quarantined Records
with tab2:
    st.subheader("Quarantined Anomaly Inspector (Dead Letter Queue)")
    
    if not quarantine_list:
        st.success("No records currently quarantined in the dead-letter queue!")
    else:
        quarantine_df = pd.DataFrame(quarantine_list)
        
        reasons_flat = []
        for item in quarantine_list:
            reasons_flat.extend(item.get("quarantine_reasons", ["UNKNOWN"]))
        
        reason_counts = (
            pd.Series(reasons_flat)
            .value_counts()
            .reset_index()
        )
        reason_counts.columns = ["Reason", "Count"]
        
        col_q1, col_q2 = st.columns([1, 2])
        
        with col_q1:
            st.markdown("#### Top Anomaly Root Causes")
            st.dataframe(
                reason_counts, 
                use_container_width=True, 
                hide_index=True
            )
            
        with col_q2:
            st.markdown("#### Anomaly Distribution")
            fig_reasons = px.pie(
                reason_counts,
                names="Reason",
                values="Count",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            fig_reasons.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
            st.plotly_chart(fig_reasons, use_container_width=True)

        st.markdown("#### Quarantined Payload Inspector")
        st.dataframe(
            quarantine_df,
            use_container_width=True,
            hide_index=True
        )

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
    st.dataframe(
        pd.DataFrame(rules_data),
        use_container_width=True,
        hide_index=True
    )