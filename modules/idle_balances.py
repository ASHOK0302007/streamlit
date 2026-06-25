"""Flag idle balances that should have been swept or invested."""

from __future__ import annotations

from datetime import datetime

import pandas as pd


REQUIRED_COLUMNS = [
    "Account_Number",
    "Bank_Name",
    "Currency",
    "Current_Balance",
    "Sweep_Threshold",
    "Last_Sweep_Date",
    "Last_Investment_Date",
    "Policy_Name",
]


def analyze_idle_balances(df: pd.DataFrame, as_of: datetime | None = None) -> pd.DataFrame:
    """Identify accounts with idle cash above policy thresholds."""
    as_of = as_of or datetime.now()
    work = df.copy()

    work["Current_Balance"] = pd.to_numeric(work["Current_Balance"], errors="coerce")
    work["Sweep_Threshold"] = pd.to_numeric(work["Sweep_Threshold"], errors="coerce")
    work["Last_Sweep_Date"] = pd.to_datetime(work["Last_Sweep_Date"], errors="coerce")
    work["Last_Investment_Date"] = pd.to_datetime(work["Last_Investment_Date"], errors="coerce")

    work["Excess_Balance"] = (work["Current_Balance"] - work["Sweep_Threshold"]).clip(lower=0).round(2)
    work["Days_Since_Sweep"] = (pd.Timestamp(as_of) - work["Last_Sweep_Date"]).dt.days
    work["Days_Since_Investment"] = (pd.Timestamp(as_of) - work["Last_Investment_Date"]).dt.days

    def classify(row: pd.Series) -> str:
        if row["Excess_Balance"] <= 0:
            return "Compliant"
        excess_ratio = row["Excess_Balance"] / max(row["Sweep_Threshold"], 1)
        if excess_ratio >= 2 or row["Days_Since_Sweep"] >= 30:
            return "Critical — Sweep Now"
        if excess_ratio >= 1 or row["Days_Since_Sweep"] >= 14:
            return "High — Schedule Sweep"
        if row["Days_Since_Sweep"] >= 7:
            return "Medium — Review Policy"
        return "Low — Monitor"

    work["Priority"] = work.apply(classify, axis=1)
    work["Estimated_Foregone_Yield"] = (work["Excess_Balance"] * 0.045 / 365 * work["Days_Since_Sweep"]).round(2)
    work["Recommended_Action"] = work.apply(_recommended_action, axis=1)

    return work.sort_values(["Priority", "Excess_Balance"], ascending=[True, False])


def _recommended_action(row: pd.Series) -> str:
    if row["Priority"] == "Compliant":
        return "Balance within sweep threshold"
    if row["Priority"].startswith("Critical"):
        return "Execute same-day sweep to master account or money market fund"
    if row["Priority"].startswith("High"):
        return "Initiate sweep workflow and notify cash manager"
    if row["Priority"].startswith("Medium"):
        return "Review sweep automation rules and bank connectivity"
    return "Track in daily liquidity dashboard"


def summary_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    flagged = df[df["Priority"] != "Compliant"]
    return {
        "accounts_reviewed": len(df),
        "idle_accounts": len(flagged),
        "total_excess_cash": round(flagged["Excess_Balance"].sum(), 2),
        "estimated_foregone_yield": round(flagged["Estimated_Foregone_Yield"].sum(), 2),
    }
