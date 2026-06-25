"""Shared utilities for Excel import and data handling."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st


def load_excel(
    uploaded_file: Any,
    sheet_name: str | int = 0,
    required_columns: list[str] | None = None,
) -> pd.DataFrame | None:
    if uploaded_file is None:
        return None
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine="openpyxl")
    except Exception as exc:
        st.error(f"Could not read Excel file: {exc}")
        return None
    if df.empty:
        st.warning("The uploaded file contains no rows.")
        return None
    df.columns = [str(col).strip() for col in df.columns]
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing required columns: {', '.join(missing)}")
            return None
    return df


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Results") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()