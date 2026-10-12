import json
import os
import sqlite3
import sys
import pandas as pd
import great_expectations as gx

RAW_DATA_PATH = "data/raw/sa_financial_transactions.csv"
DB_PATH = "data/processed/financial_warehouse.db"
DEAD_LETTER_PATH = "logs/dead_letter_queue.json"

def run_pipeline():
    if not os.path.exists(RAW_DATA_PATH):
        print(f"Error: {RAW_DATA_PATH} not found.")
        sys.exit(1)

    print("Loading dataset into Pandas...")
    df = pd.read_csv(RAW_DATA_PATH)

    # ----------------------------------------------------
    # Great Expectations v1.x Validation Suite
    # ----------------------------------------------------
    print("Running Great Expectations v1.x validation...")
    context = gx.get_context()
    data_source = context.data_sources.add_pandas(name="financial_datasource")
    data_asset = data_source.add_dataframe_asset(name="transactions_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("transactions_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name="sa_financial_suite")
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="transaction_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="account_number"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(column="currency", value_set=["ZAR"]))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0.01, max_value=1000000.00))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(column="status", value_set=["SUCCESS", "FAILED", "PENDING"]))

    validation_result = batch.validate(suite)
    print(f"Great Expectations Overall Success: {validation_result.success}")

    # ----------------------------------------------------
    # Defensive Routing (Row-by-Row Isolation)
    # ----------------------------------------------------
    valid_rows = []
    quarantined_rows = []

    for idx, row in df.iterrows():
        reasons = []
        
        if pd.isna(row["account_number"]) or str(row["account_number"]).strip() == "":
            reasons.append("MISSING_ACCOUNT_NUMBER")
        if row["currency"] != "ZAR":
            reasons.append(f"INVALID_CURRENCY_{row['currency']}")
        if row["amount"] <= 0:
            reasons.append("NON_POSITIVE_AMOUNT")
        if row["status"] not in ["SUCCESS", "FAILED", "PENDING"]:
            reasons.append(f"INVALID_STATUS_{row['status']}")
        if row["vat_amount"] > row["amount"]:
            reasons.append("VAT_EXCEEDS_AMOUNT")

        if len(reasons) == 0:
            valid_rows.append(row)
        else:
            invalid_record = row.to_dict()
            invalid_record["quarantine_reasons"] = reasons
            quarantined_rows.append(invalid_record)

    # Load Valid Records to SQLite
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    clean_df = pd.DataFrame(valid_rows)
    if not clean_df.empty:
        clean_df.to_sql("transactions", conn, if_exists="append", index=False)
        print(f"Loaded {len(clean_df)} valid records into SQLite ({DB_PATH}).")
    else:
        print("No valid records found to insert.")
    
    conn.close()

    # Quarantined Records to Dead Letter Queue
    os.makedirs(os.path.dirname(DEAD_LETTER_PATH), exist_ok=True)
    with open(DEAD_LETTER_PATH, "w", encoding="utf-8") as f:
        json.dump(quarantined_rows, f, indent=2)
    
    print(f"Quarantined {len(quarantined_rows)} invalid records to {DEAD_LETTER_PATH}.")

if __name__ == "__main__":
    run_pipeline()