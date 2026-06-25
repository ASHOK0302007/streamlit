"""Recompute bank charges and interest against sanctioned terms."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "Account_Number",
    "Bank_Name",
    "Charge_Type",
    "Period_Start",
    "Period_End",
    "Actual_Charge",
    "Sanctioned_Rate_Pct",
    "Average_Balance",
    "Currency",
]


def analyze_bank_charges(df: pd.DataFrame) -> pd.DataFrame:
    """Compare actual bank charges/interest to sanctioned contractual terms."""
    work = df.copy()

    work["Period_Start"] = pd.to_datetime(work["Period_Start"], errors="coerce")
    work["Period_End"] = pd.to_datetime(work["Period_End"], errors="coerce")
    work["Actual_Charge"] = pd.to_numeric(work["Actual_Charge"], errors="coerce")
    work["Sanctioned_Rate_Pct"] = pd.to_numeric(work["Sanctioned_Rate_Pct"], errors="coerce")
    work["Average_Balance"] = pd.to_numeric(work["Average_Balance"], errors="coerce")

    work["Period_Days"] = (work["Period_End"] - work["Period_Start"]).dt.days + 1
    work["Expected_Charge"] = (
        work["Average_Balance"].abs()
        * (work["Sanctioned_Rate_Pct"] / 100)
        * (work["Period_Days"] / 365)
    ).round(2)

    work["Variance"] = (work["Actual_Charge"] - work["Expected_Charge"]).round(2)
    work["Variance_Pct"] = (
        (work["Variance"] / work["Expected_Charge"].replace(0, pd.NA)) * 100
    ).round(2)

    def classify(row: pd.Series) -> str:
        variance_pct = abs(row["Variance_Pct"]) if pd.notna(row["Variance_Pct"]) else 0
        if variance_pct >= 15:
            return "Critical — Reclaim"
        if variance_pct >= 8:
            return "High — Query Bank"
        if variance_pct >= 3:
            return "Medium — Review Terms"
        return "Within Tolerance"

    work["Status"] = work.apply(classify, axis=1)
    work["Recommended_Action"] = work.apply(_recommended_action, axis=1)

    return work.sort_values("Variance_Pct", ascending=False, key=lambda s: s.abs())


def _recommended_action(row: pd.Series) -> str:
    status = row["Status"]
    if status.startswith("Critical"):
        return "Raise debit note / initiate fee reclamation with bank relationship manager"
    if status.startswith("High"):
        return "Send variance query with sanctioned term schedule attached"
    if status.startswith("Medium"):
        return "Validate rate card and update treasury policy if needed"
    return "No action — within agreed tolerance band"


def summary_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    flagged = df[~df["Status"].str.startswith("Within")]
    return {
        "accounts_reviewed": df["Account_Number"].nunique(),
        "flagged_items": len(flagged),
        "total_overcharge": round(flagged[flagged["Variance"] > 0]["Variance"].sum(), 2),
        "total_undercharge": round(flagged[flagged["Variance"] < 0]["Variance"].sum(), 2),
    }
