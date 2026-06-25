"""Detect round-tripping of funds across related accounts."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "Transaction_ID",
    "Transaction_Date",
    "From_Account",
    "To_Account",
    "Amount",
    "Currency",
    "Reference",
]


def analyze_round_tripping(
    df: pd.DataFrame,
    window_days: int = 5,
    tolerance_pct: float = 2.0,
) -> pd.DataFrame:
    """Identify suspicious round-trip fund movements between related accounts."""
    work = df.copy()
    work["Transaction_Date"] = pd.to_datetime(work["Transaction_Date"], errors="coerce")
    work["Amount"] = pd.to_numeric(work["Amount"], errors="coerce").abs()
    work["Currency"] = work["Currency"].astype(str).str.upper().str.strip()

    flags: list[dict] = []

    for currency, group in work.groupby("Currency"):
        records = group.sort_values("Transaction_Date").reset_index(drop=True)
        for i, outbound in records.iterrows():
            reverse = records[
                (records.index > i)
                & (records["From_Account"] == outbound["To_Account"])
                & (records["To_Account"] == outbound["From_Account"])
            ]
            if reverse.empty:
                continue

            for _, inbound in reverse.iterrows():
                day_gap = (inbound["Transaction_Date"] - outbound["Transaction_Date"]).days
                if day_gap < 0 or day_gap > window_days:
                    continue

                variance = abs(inbound["Amount"] - outbound["Amount"]) / max(outbound["Amount"], 1) * 100
                if variance > tolerance_pct:
                    continue

                risk = "Critical" if day_gap <= 1 and variance <= 0.5 else "High" if day_gap <= 2 else "Medium"

                flags.append(
                    {
                        "Outbound_ID": outbound["Transaction_ID"],
                        "Inbound_ID": inbound["Transaction_ID"],
                        "From_Account": outbound["From_Account"],
                        "To_Account": outbound["To_Account"],
                        "Outbound_Date": outbound["Transaction_Date"],
                        "Inbound_Date": inbound["Transaction_Date"],
                        "Days_Between": day_gap,
                        "Outbound_Amount": outbound["Amount"],
                        "Inbound_Amount": inbound["Amount"],
                        "Variance_Pct": round(variance, 2),
                        "Currency": currency,
                        "Risk_Level": risk,
                        "Pattern": "Round-trip detected",
                        "Recommendation": _recommendation(risk, day_gap),
                    }
                )

    if not flags:
        return pd.DataFrame(
            columns=[
                "Outbound_ID",
                "Inbound_ID",
                "From_Account",
                "To_Account",
                "Outbound_Date",
                "Inbound_Date",
                "Days_Between",
                "Outbound_Amount",
                "Inbound_Amount",
                "Variance_Pct",
                "Currency",
                "Risk_Level",
                "Pattern",
                "Recommendation",
            ]
        )

    return pd.DataFrame(flags).drop_duplicates(
        subset=["Outbound_ID", "Inbound_ID"]
    ).sort_values(["Risk_Level", "Days_Between"])


def _recommendation(risk: str, day_gap: int) -> str:
    if risk == "Critical":
        return "Immediate compliance review — possible wash trading or liquidity window dressing"
    if risk == "High":
        return "Investigate purpose and supporting approvals within 24 hours"
    return f"Validate business rationale for same-day or {day_gap}-day reversal"


def summary_metrics(df: pd.DataFrame) -> dict[str, int]:
    if df.empty:
        return {"patterns_found": 0, "critical": 0, "high": 0, "medium": 0}
    return {
        "patterns_found": len(df),
        "critical": int((df["Risk_Level"] == "Critical").sum()),
        "high": int((df["Risk_Level"] == "High").sum()),
        "medium": int((df["Risk_Level"] == "Medium").sum()),
    }
