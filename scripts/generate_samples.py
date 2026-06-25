"""Generate sample Excel templates for CAP Treasury app."""

from pathlib import Path

import pandas as pd

SAMPLES_DIR = Path(__file__).parent.parent / "data" / "samples"


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    reconciliation = pd.DataFrame(
        [
            ["REC-001", "ACC-1001", "Barclays", "2026-01-15", 45230.00, "Unmatched bank fee", "Open"],
            ["REC-002", "ACC-1002", "HSBC", "2025-11-20", 128500.00, "Timing difference — outgoing wire", "Pending"],
            ["REC-003", "ACC-1003", "Citi", "2025-09-05", 8750.50, "Deposit in transit", "Outstanding"],
            ["REC-004", "ACC-1001", "Barclays", "2026-03-01", 2100.00, "Interest accrual mismatch", "Open"],
            ["REC-005", "ACC-1004", "Deutsche Bank", "2025-06-18", 250000.00, "FX settlement variance", "Unmatched"],
            ["REC-006", "ACC-1002", "HSBC", "2026-04-10", 980.00, "Bank charge discrepancy", "Matched"],
        ],
        columns=[
            "Reconciliation_ID",
            "Account_Number",
            "Bank_Name",
            "Item_Date",
            "Amount",
            "Description",
            "Status",
        ],
    )

    transactions = pd.DataFrame(
        [
            ["TXN-101", "2026-04-01", "ACC-1001", "ACC-1002", 500000, "USD", "Interco funding"],
            ["TXN-102", "2026-04-02", "ACC-1002", "ACC-1001", 498500, "USD", "Interco return"],
            ["TXN-103", "2026-03-15", "ACC-1003", "ACC-1004", 120000, "EUR", "Liquidity transfer"],
            ["TXN-104", "2026-03-16", "ACC-1004", "ACC-1003", 119400, "EUR", "Liquidity return"],
            ["TXN-105", "2026-05-01", "ACC-1001", "ACC-1005", 75000, "USD", "Vendor prepayment"],
            ["TXN-106", "2026-05-10", "ACC-1005", "ACC-1001", 30000, "USD", "Partial refund"],
        ],
        columns=[
            "Transaction_ID",
            "Transaction_Date",
            "From_Account",
            "To_Account",
            "Amount",
            "Currency",
            "Reference",
        ],
    )

    charges = pd.DataFrame(
        [
            ["ACC-1001", "Barclays", "Account Maintenance", "2026-01-01", "2026-03-31", 1250.00, 0.15, 2500000, "USD"],
            ["ACC-1002", "HSBC", "Wire Fee", "2026-01-01", "2026-03-31", 890.00, 0.08, 1800000, "USD"],
            ["ACC-1003", "Citi", "Interest Charge", "2026-01-01", "2026-03-31", 4200.00, 0.35, 3200000, "USD"],
            ["ACC-1004", "Deutsche Bank", "FX Spread", "2026-01-01", "2026-03-31", 3100.00, 0.22, 950000, "EUR"],
        ],
        columns=[
            "Account_Number",
            "Bank_Name",
            "Charge_Type",
            "Period_Start",
            "Period_End",
            "Actual_Charge",
            "Sanctioned_Rate_Pct",
            "Average_Balance",
            "Currency",
        ],
    )

    idle = pd.DataFrame(
        [
            ["ACC-1001", "Barclays", "USD", 850000, 100000, "2026-04-01", "2026-03-15", "Global Sweep Policy"],
            ["ACC-1002", "HSBC", "USD", 125000, 50000, "2026-05-20", "2026-05-01", "Regional Sweep Policy"],
            ["ACC-1003", "Citi", "USD", 45000, 75000, "2026-05-18", "2026-05-10", "Global Sweep Policy"],
            ["ACC-1004", "Deutsche Bank", "EUR", 620000, 150000, "2026-02-10", "2026-01-20", "EU Investment Policy"],
        ],
        columns=[
            "Account_Number",
            "Bank_Name",
            "Currency",
            "Current_Balance",
            "Sweep_Threshold",
            "Last_Sweep_Date",
            "Last_Investment_Date",
            "Policy_Name",
        ],
    )

    signatories_txn = pd.DataFrame(
        [
            ["PAY-001", "ACC-1001", "2026-05-01", 450000, "USD", "Jane Smith", "A", "Yes"],
            ["PAY-002", "ACC-1002", "2026-05-03", 85000, "USD", "Tom Harris", "B", "No"],
            ["PAY-003", "ACC-1003", "2026-05-05", 1200000, "USD", "Unknown User", "A", "Yes"],
            ["PAY-004", "ACC-1001", "2026-05-08", 25000, "USD", "Jane Smith", "B", "No"],
            ["PAY-005", "ACC-1004", "2026-05-10", 300000, "EUR", "Robert Lee", "A", "Yes"],
        ],
        columns=[
            "Transaction_ID",
            "Account_Number",
            "Transaction_Date",
            "Amount",
            "Currency",
            "Actual_Approver",
            "Required_Signatory_Level",
            "Dual_Approval_Required",
        ],
    )

    signatories_register = pd.DataFrame(
        [
            ["ACC-1001", "Jane Smith", "A", 500000, "Active"],
            ["ACC-1001", "Michael Brown", "B", 100000, "Active"],
            ["ACC-1002", "Tom Harris", "B", 150000, "Active"],
            ["ACC-1003", "Sarah Chen", "A", 2000000, "Active"],
            ["ACC-1004", "Robert Lee", "A", 750000, "Inactive"],
        ],
        columns=[
            "Account_Number",
            "Signatory_Name",
            "Authorisation_Level",
            "Transaction_Limit",
            "Status",
        ],
    )

    reconciliation.to_excel(SAMPLES_DIR / "reconciliation_items.xlsx", index=False)
    transactions.to_excel(SAMPLES_DIR / "transactions.xlsx", index=False)
    charges.to_excel(SAMPLES_DIR / "bank_charges.xlsx", index=False)
    idle.to_excel(SAMPLES_DIR / "idle_balances.xlsx", index=False)
    signatories_txn.to_excel(SAMPLES_DIR / "signatory_transactions.xlsx", index=False)
    signatories_register.to_excel(SAMPLES_DIR / "authorised_signatories.xlsx", index=False)

    print(f"Sample files written to {SAMPLES_DIR}")


if __name__ == "__main__":
    main()
