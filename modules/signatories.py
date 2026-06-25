"""Verify authorised signatories against actual transaction approvers."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "Transaction_ID",
    "Account_Number",
    "Transaction_Date",
    "Amount",
    "Currency",
    "Actual_Approver",
    "Required_Signatory_Level",
    "Dual_Approval_Required",
]


def analyze_signatories(
    df: pd.DataFrame,
    authorised_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Match transaction approvers to authorised signatory register."""
    work = df.copy()
    work["Transaction_Date"] = pd.to_datetime(work["Transaction_Date"], errors="coerce")
    work["Amount"] = pd.to_numeric(work["Amount"], errors="coerce")
    work["Dual_Approval_Required"] = work["Dual_Approval_Required"].astype(str).str.lower().isin(
        ["yes", "true", "1", "y"]
    )

    auth_lookup: dict[tuple[str, str], dict] = {}
    if authorised_df is not None and not authorised_df.empty:
        auth = authorised_df.copy()
        auth.columns = [str(c).strip() for c in auth.columns]
        for _, row in auth.iterrows():
            key = (str(row.get("Account_Number", "")), str(row.get("Signatory_Name", "")).strip().lower())
            auth_lookup[key] = {
                "level": str(row.get("Authorisation_Level", "")).strip().lower(),
                "active": str(row.get("Status", "active")).strip().lower() == "active",
                "limit": pd.to_numeric(row.get("Transaction_Limit", float("inf")), errors="coerce"),
            }

    results = []
    for _, row in work.iterrows():
        approver = str(row["Actual_Approver"]).strip()
        approver_key = approver.lower()
        account = str(row["Account_Number"])
        lookup = auth_lookup.get((account, approver_key), {})
        authorised = bool(lookup)
        active = lookup.get("active", False)
        approver_level = lookup.get("level", "unknown")
        required_level = str(row["Required_Signatory_Level"]).strip().lower()
        limit = lookup.get("limit", float("inf"))
        amount = row["Amount"]

        level_rank = {"a": 3, "b": 2, "c": 1, "director": 4, "manager": 2, "officer": 1}
        approver_rank = level_rank.get(approver_level[:1] if len(approver_level) == 1 else approver_level, 0)
        required_rank = level_rank.get(required_level[:1] if len(required_level) == 1 else required_level, 0)

        if not authorised:
            status = "Critical — Unauthorised Approver"
        elif not active:
            status = "Critical — Inactive Signatory"
        elif pd.notna(amount) and amount > limit:
            status = "High — Exceeds Limit"
        elif approver_rank < required_rank:
            status = "High — Insufficient Authority"
        elif row["Dual_Approval_Required"]:
            status = "Medium — Verify Dual Approval"
        else:
            status = "Compliant"

        results.append(
            {
                **row.to_dict(),
                "Approver_Authorised": authorised,
                "Approver_Active": active,
                "Approver_Level": approver_level or "—",
                "Status": status,
                "Recommended_Action": _recommended_action(status),
            }
        )

    result_df = pd.DataFrame(results)
    priority_order = {
        "Critical — Unauthorised Approver": 0,
        "Critical — Inactive Signatory": 1,
        "High — Exceeds Limit": 2,
        "High — Insufficient Authority": 3,
        "Medium — Verify Dual Approval": 4,
        "Compliant": 5,
    }
    result_df["_sort"] = result_df["Status"].map(priority_order).fillna(99)
    return result_df.sort_values(["_sort", "Amount"], ascending=[True, False]).drop(columns="_sort")


def _recommended_action(status: str) -> str:
    if "Unauthorised" in status:
        return "Block future payments and escalate to compliance immediately"
    if "Inactive" in status:
        return "Remove signatory from bank mandate and investigate payment"
    if "Exceeds Limit" in status:
        return "Obtain retrospective board approval or recall transaction"
    if "Insufficient Authority" in status:
        return "Validate signatory matrix and re-train operations team"
    if "Dual Approval" in status:
        return "Confirm second approver on payment instruction"
    return "No action required"


def summary_metrics(df: pd.DataFrame) -> dict[str, int]:
    return {
        "transactions_reviewed": len(df),
        "non_compliant": int((df["Status"] != "Compliant").sum()),
        "critical": int(df["Status"].str.startswith("Critical").sum()),
        "high": int(df["Status"].str.startswith("High").sum()),
    }
