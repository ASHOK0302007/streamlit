"""Bank reconciliation ageing and chase analysis."""

from __future__ import annotations

from datetime import datetime

import pandas as pd


REQUIRED_COLUMNS = [
    "Reconciliation_ID",
    "Account_Number",
    "Bank_Name",
    "Item_Date",
    "Amount",
    "Description",
    "Status",
]

STATUS_PENDING = {"open", "pending", "unmatched", "outstanding", "in progress"}


def analyze_reconciliation(df: pd.DataFrame, as_of: datetime | None = None) -> pd.DataFrame:
    """Age reconciliation items and flag long-pending entries for chase."""
    as_of = as_of or datetime.now()
    work = df.copy()

    work["Item_Date"] = pd.to_datetime(work["Item_Date"], errors="coerce")
    work["Amount"] = pd.to_numeric(work["Amount"], errors="coerce")
    work["Status"] = work["Status"].astype(str).str.strip().str.lower()

    work["Age_Days"] = (pd.Timestamp(as_of) - work["Item_Date"]).dt.days
    work["Age_Bucket"] = pd.cut(
        work["Age_Days"],
        bins=[-1, 7, 15, 30, 60, 90, float("inf")],
        labels=["0-7 days", "8-15 days", "16-30 days", "31-60 days", "61-90 days", "90+ days"],
    )

    def chase_priority(row: pd.Series) -> str:
        if row["Status"] not in STATUS_PENDING:
            return "Closed"
        age = row["Age_Days"] if pd.notna(row["Age_Days"]) else 0
        amount = abs(row["Amount"]) if pd.notna(row["Amount"]) else 0
        if age >= 90 or amount >= 100_000:
            return "Critical — Escalate"
        if age >= 60:
            return "High — Chase Today"
        if age >= 30:
            return "Medium — Follow Up"
        if age >= 15:
            return "Low — Monitor"
        return "Routine"

    work["Chase_Priority"] = work.apply(chase_priority, axis=1)
    work["Recommended_Action"] = work.apply(_recommended_action, axis=1)

    return work.sort_values(["Chase_Priority", "Age_Days"], ascending=[True, False])


def _recommended_action(row: pd.Series) -> str:
    if row["Chase_Priority"] == "Closed":
        return "No action required"
    if row["Chase_Priority"].startswith("Critical"):
        return "Escalate to CFO / send formal bank query"
    if row["Chase_Priority"].startswith("High"):
        return "Assign owner and send chase email to bank"
    if row["Chase_Priority"].startswith("Medium"):
        return "Request supporting documents and update tracker"
    if row["Chase_Priority"].startswith("Low"):
        return "Review in weekly recon meeting"
    return "Continue standard monitoring"


def summary_metrics(df: pd.DataFrame) -> dict[str, int | float]:
    """Compute dashboard metrics for reconciliation ageing."""
    pending = df[df["Chase_Priority"] != "Closed"]
    return {
        "total_items": len(df),
        "pending_items": len(pending),
        "critical_items": int(pending["Chase_Priority"].str.startswith("Critical").sum()),
        "avg_age_days": round(pending["Age_Days"].mean(), 1) if len(pending) else 0,
        "pending_value": round(pending["Amount"].abs().sum(), 2),
    }
