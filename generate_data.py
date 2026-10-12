import csv
import random
from datetime import datetime, timedelta
import os

MERCHANTS = [
    "Checkers Rosebank", "Shoprite Soweto", "Woolworths Sandton",
    "Vodacom Direct TopUp", "MTN Airtime", "Eskom Prepaid",
    "Takealot Online", "Dis-Chem Pharmacy", "Gautrain TapToPay",
    "Engen QuickShop", "Shell Select", "Capitec Instant Pay"
]

CHANNELS = ["POS", "EFT", "Capitec_Pay", "CARD_ONLINE", "ATM", "RTC_EFT"]
STATUSES = ["SUCCESS", "SUCCESS", "SUCCESS", "FAILED", "PENDING"]

def generate_sa_dataset(file_path="data/raw/sa_financial_transactions.csv", num_rows=100):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    start_time = datetime(2026, 10, 1, 8, 0, 0)
    
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "transaction_id", "timestamp", "account_number", 
            "merchant_name", "channel", "amount", 
            "currency", "vat_amount", "status", "flagged_anomaly"
        ])
        
        for i in range(1, num_rows + 1):
            txn_id = f"TXN-ZA-{10000 + i}"
            txn_time = (start_time + timedelta(minutes=i * 2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            account_no = str(random.randint(1000000000, 9999999999))
            merchant = random.choice(MERCHANTS)
            channel = random.choice(CHANNELS)
            amount = round(random.uniform(20.00, 5500.00), 2)
            currency = "ZAR"
            vat_amount = round(amount * 0.130435, 2)  # 15% VAT inclusive calculation
            status = random.choice(STATUSES)
            anomaly = ""

            # Inject intentional data quality faults in ~10% of records for testing
            fault_type = random.random()
            if fault_type < 0.02:
                account_no = ""
                anomaly = "MISSING_ACCOUNT_NO"
            elif fault_type < 0.04:
                amount = -1 * amount
                anomaly = "NEGATIVE_AMOUNT"
            elif fault_type < 0.06:
                currency = "USD"
                anomaly = "INVALID_CURRENCY"
            elif fault_type < 0.08:
                status = "UNKNOWN_CODE"
                anomaly = "INVALID_STATUS_ENUM"
            elif fault_type < 0.10:
                vat_amount = round(amount * 1.5, 2)
                anomaly = "VAT_EXCEEDS_AMOUNT"

            writer.writerow([
                txn_id, txn_time, account_no, merchant, 
                channel, amount, currency, vat_amount, status, anomaly
            ])

    print(f"Generated {num_rows} records at {file_path}")

if __name__ == "__main__":
    generate_sa_dataset()