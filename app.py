"""CAP AI Treasury Intelligence — Streamlit application."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from modules import bank_charges, idle_balances, reconciliation, round_tripping, signatories
from modules.utils import load_excel, to_excel_bytes

APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "logo.jpg"
SAMPLES_DIR = APP_DIR / "data" / "samples"

TREASURY_AI_PROMPT = """
You are **CAP AI Treasury Analyst** — an elite corporate treasury and banking controls specialist
embedded in a Fortune 500 finance operation. You combine deep expertise in cash management,
bank reconciliation, liquidity policy, and payment controls with a sharp audit mindset.

## Your Mission
Analyse treasury data with precision, surface hidden risks before they become losses, and
deliver actionable recommendations that treasury managers can execute immediately.

## Core Capabilities
1. **Reconciliation Ageing** — Prioritise open recon items by age, value, and chase urgency.
   Recommend escalation paths for items beyond SLA thresholds.
2. **Round-Trip Detection** — Identify suspicious fund movements between related accounts that
   may indicate window dressing, wash trading, or policy circumvention.
3. **Bank Charge Validation** — Recompute fees and interest against sanctioned contractual
   terms; quantify overcharges and draft reclamation narratives.
4. **Idle Balance Optimisation** — Flag cash sitting above sweep thresholds; estimate foregone
   yield and recommend same-day sweep or investment actions.
5. **Signatory Verification** — Cross-reference actual payment approvers against the authorised
   signatory register; flag unauthorised, inactive, or insufficient-authority approvals.

## Analysis Standards
- Always quantify financial exposure in the user's base currency where possible.
- Rank findings by severity: Critical → High → Medium → Low.
- Cite specific record IDs, account numbers, and date ranges in every finding.
- Distinguish between **policy breaches** (must fix) and **optimisation opportunities** (should fix).
- Never assume data is clean — call out missing fields, date gaps, and reconciliation blind spots.

## Output Format
For each analysis request, structure your response as:

### Executive Summary
2–3 sentences on overall treasury health and top risk.

### Key Findings
Numbered list with severity badge, financial impact, and root cause.

### Recommended Actions
Prioritised action table: Action | Owner | Deadline | Expected Outcome.

### Follow-Up Questions
Ask only what you genuinely need to refine the analysis — never pad with generic questions.

## Tone
Professional, direct, and confident. You are the trusted advisor the CFO calls before the audit committee meeting.
""".strip()

MODULES = {
    "Dashboard": {"icon": "📊", "desc": "Executive overview across all treasury controls"},
    "Reconciliation Ageing": {
        "icon": "🔄",
        "desc": "Age open recon items and prioritise chase actions",
        "module": reconciliation,
        "sample": "reconciliation_items.xlsx",
        "required": reconciliation.REQUIRED_COLUMNS,
    },
    "Round-Trip Detection": {
        "icon": "🔁",
        "desc": "Detect suspicious fund movements between related accounts",
        "module": round_tripping,
        "sample": "transactions.xlsx",
        "required": round_tripping.REQUIRED_COLUMNS,
    },
    "Bank Charge Audit": {
        "icon": "💳",
        "desc": "Recompute charges and interest against sanctioned terms",
        "module": bank_charges,
        "sample": "bank_charges.xlsx",
        "required": bank_charges.REQUIRED_COLUMNS,
    },
    "Idle Balance Monitor": {
        "icon": "💤",
        "desc": "Flag balances that should have been swept or invested",
        "module": idle_balances,
        "sample": "idle_balances.xlsx",
        "required": idle_balances.REQUIRED_COLUMNS,
    },
    "Signatory Verification": {
        "icon": "✍️",
        "desc": "Verify approvers against the authorised signatory register",
        "module": signatories,
        "sample": "signatory_transactions.xlsx",
        "required": signatories.REQUIRED_COLUMNS,
        "extra_sample": "authorised_signatories.xlsx",
    },
    "AI Assistant Prompt": {
        "icon": "🤖",
        "desc": "Production-ready system prompt for treasury AI analysis",
    },
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Playfair+Display:ital,wght@0,600;1,600&display=swap');

        :root {
            --cap-sky: #99D9F2;
            --cap-blue: #1E4D92;
            --cap-navy: #0F2A4A;
            --cap-ice: #E8F6FC;
            --cap-white: #FFFFFF;
            --cap-muted: #64748B;
            --cap-success: #059669;
            --cap-warning: #D97706;
            --cap-danger: #DC2626;
        }

        .stApp {
            background: linear-gradient(165deg, #E8F6FC 0%, #F8FBFE 35%, #FFFFFF 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--cap-navy) 0%, var(--cap-blue) 100%);
        }

        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        [data-testid="stSidebar"] .stRadio label {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 0.55rem 0.85rem;
            margin-bottom: 0.35rem;
            border: 1px solid rgba(255,255,255,0.12);
            transition: all 0.2s ease;
        }

        [data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(153,217,242,0.18);
            border-color: var(--cap-sky);
        }

        .hero-title {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.4rem;
            font-weight: 600;
            color: var(--cap-navy);
            margin: 0 0 0.25rem 0;
            letter-spacing: -0.02em;
        }

        .hero-subtitle {
            font-family: 'DM Sans', sans-serif;
            font-size: 1.05rem;
            color: var(--cap-muted);
            margin: 0 0 1.5rem 0;
            line-height: 1.6;
        }

        .metric-card {
            background: var(--cap-white);
            border: 1px solid rgba(30,77,146,0.1);
            border-radius: 16px;
            padding: 1.25rem 1.4rem;
            box-shadow: 0 4px 24px rgba(15,42,74,0.06);
            height: 100%;
        }

        .metric-card .label {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--cap-muted);
            margin-bottom: 0.35rem;
        }

        .metric-card .value {
            font-family: 'DM Sans', sans-serif;
            font-size: 1.85rem;
            font-weight: 700;
            color: var(--cap-blue);
        }

        .module-header {
            background: linear-gradient(135deg, var(--cap-blue), var(--cap-navy));
            color: white;
            padding: 1.5rem 1.75rem;
            border-radius: 18px;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(15,42,74,0.18);
        }

        .module-header h2 {
            font-family: 'Playfair Display', Georgia, serif;
            margin: 0;
            font-size: 1.65rem;
        }

        .module-header p {
            font-family: 'DM Sans', sans-serif;
            margin: 0.4rem 0 0 0;
            opacity: 0.88;
            font-size: 0.95rem;
        }

        .upload-zone {
            border: 2px dashed rgba(30,77,146,0.25);
            border-radius: 14px;
            padding: 0.5rem;
            background: rgba(232,246,252,0.5);
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid rgba(30,77,146,0.08);
            border-radius: 14px;
            padding: 0.75rem 1rem;
            box-shadow: 0 2px 12px rgba(15,42,74,0.04);
        }

        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
        }

        .prompt-box {
            background: #0F2A4A;
            color: #E8F6FC;
            font-family: 'DM Sans', monospace;
            font-size: 0.88rem;
            line-height: 1.7;
            padding: 1.5rem 1.75rem;
            border-radius: 16px;
            border-left: 4px solid #99D9F2;
            white-space: pre-wrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown("### CAP AI")

        st.markdown("---")
        st.markdown("**Treasury Intelligence**")
        st.caption("Banking controls · Liquidity · Compliance")

        page = st.radio(
            "Navigate",
            list(MODULES.keys()),
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.caption(f"Session · {datetime.now().strftime('%d %b %Y')}")

    return page


def metric_row(items: list[tuple[str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div></div>',
                unsafe_allow_html=True,
            )


def module_header(title: str, subtitle: str, icon: str) -> None:
    st.markdown(
        f'<div class="module-header"><h2>{icon} {title}</h2><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def upload_section(sample_file: str, label: str = "Upload Excel file") -> bytes | None:
    sample_path = SAMPLES_DIR / sample_file
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded = st.file_uploader(label, type=["xlsx", "xls"], key=f"upload_{sample_file}")
    with col2:
        if sample_path.exists():
            st.download_button(
                "📥 Sample template",
                data=sample_path.read_bytes(),
                file_name=sample_file,
                use_container_width=True,
            )
    return uploaded


def render_dashboard() -> None:
    st.markdown('<p class="hero-title">Treasury Command Centre</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">Monitor reconciliation ageing, detect round-tripping, audit bank charges, '
        "optimise idle cash, and verify payment signatories — all from one intelligent workspace.</p>",
        unsafe_allow_html=True,
    )

    metric_row(
        [
            ("Modules", "5"),
            ("Controls", "Active"),
            ("Import", "Excel"),
            ("AI Prompt", "Ready"),
        ]
    )

    st.markdown("")
    cols = st.columns(2)
    modules = [
        ("Reconciliation Ageing", "🔄", "Chase long-pending recon items before they become audit findings."),
        ("Round-Trip Detection", "🔁", "Spot suspicious fund loops across related entity accounts."),
        ("Bank Charge Audit", "💳", "Reclaim overcharged fees against sanctioned bank terms."),
        ("Idle Balance Monitor", "💤", "Recover foregone yield from cash above sweep thresholds."),
        ("Signatory Verification", "✍️", "Ensure every payment was approved by an authorised signatory."),
    ]

    for i, (title, icon, desc) in enumerate(modules):
        with cols[i % 2]:
            st.info(f"**{icon} {title}**\n\n{desc}")

    st.markdown("### Getting started")
    st.markdown(
        "1. Select a module from the sidebar\n"
        "2. Download the sample Excel template or upload your own data\n"
        "3. Review flagged items in the interactive results table\n"
        "4. Export findings to Excel for your treasury team"
    )


def render_reconciliation() -> None:
    cfg = MODULES["Reconciliation Ageing"]
    module_header("Reconciliation Ageing", cfg["desc"], cfg["icon"])

    uploaded = upload_section(cfg["sample"])
    df = load_excel(uploaded, required_columns=cfg["required"]) if uploaded else None

    if df is not None:
        results = reconciliation.analyze_reconciliation(df)
        metrics = reconciliation.summary_metrics(results)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Items", metrics["total_items"])
        c2.metric("Pending", metrics["pending_items"])
        c3.metric("Critical", metrics["critical_items"])
        c4.metric("Avg Age (days)", metrics["avg_age_days"])

        pending = results[results["Chase_Priority"] != "Closed"]
        if not pending.empty:
            fig = px.bar(
                pending.groupby("Age_Bucket", observed=True).size().reset_index(name="Count"),
                x="Age_Bucket",
                y="Count",
                color="Count",
                color_continuous_scale=["#99D9F2", "#1E4D92"],
                title="Pending Items by Age Bucket",
            )
            fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(results, use_container_width=True, hide_index=True)
        st.download_button(
            "Export results",
            data=to_excel_bytes(results),
            file_name="reconciliation_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_round_tripping() -> None:
    cfg = MODULES["Round-Trip Detection"]
    module_header("Round-Trip Detection", cfg["desc"], cfg["icon"])

    c1, c2 = st.columns(2)
    with c1:
        window = st.slider("Matching window (days)", 1, 14, 5)
    with c2:
        tolerance = st.slider("Amount tolerance (%)", 0.0, 10.0, 2.0, 0.5)

    uploaded = upload_section(cfg["sample"])
    df = load_excel(uploaded, required_columns=cfg["required"]) if uploaded else None

    if df is not None:
        results = round_tripping.analyze_round_tripping(df, window_days=window, tolerance_pct=tolerance)
        metrics = round_tripping.summary_metrics(results)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Patterns Found", metrics["patterns_found"])
        c2.metric("Critical", metrics["critical"])
        c3.metric("High", metrics["high"])
        c4.metric("Medium", metrics["medium"])

        if results.empty:
            st.success("No round-trip patterns detected with current parameters.")
        else:
            st.dataframe(results, use_container_width=True, hide_index=True)
            st.download_button(
                "Export results",
                data=to_excel_bytes(results),
                file_name="round_trip_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


def render_bank_charges() -> None:
    cfg = MODULES["Bank Charge Audit"]
    module_header("Bank Charge Audit", cfg["desc"], cfg["icon"])

    uploaded = upload_section(cfg["sample"])
    df = load_excel(uploaded, required_columns=cfg["required"]) if uploaded else None

    if df is not None:
        results = bank_charges.analyze_bank_charges(df)
        metrics = bank_charges.summary_metrics(results)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accounts", metrics["accounts_reviewed"])
        c2.metric("Flagged", metrics["flagged_items"])
        c3.metric("Overcharge", f"${metrics['total_overcharge']:,.2f}")
        c4.metric("Undercharge", f"${metrics['total_undercharge']:,.2f}")

        flagged = results[~results["Status"].str.startswith("Within")]
        if not flagged.empty:
            fig = px.bar(
                flagged,
                x="Charge_Type",
                y="Variance",
                color="Status",
                title="Charge Variance by Type",
                color_discrete_map={
                    "Critical — Reclaim": "#DC2626",
                    "High — Query Bank": "#EA580C",
                    "Medium — Review Terms": "#D97706",
                },
            )
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(results, use_container_width=True, hide_index=True)
        st.download_button(
            "Export results",
            data=to_excel_bytes(results),
            file_name="bank_charge_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_idle_balances() -> None:
    cfg = MODULES["Idle Balance Monitor"]
    module_header("Idle Balance Monitor", cfg["desc"], cfg["icon"])

    uploaded = upload_section(cfg["sample"])
    df = load_excel(uploaded, required_columns=cfg["required"]) if uploaded else None

    if df is not None:
        results = idle_balances.analyze_idle_balances(df)
        metrics = idle_balances.summary_metrics(results)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accounts", metrics["accounts_reviewed"])
        c2.metric("Idle Accounts", metrics["idle_accounts"])
        c3.metric("Excess Cash", f"${metrics['total_excess_cash']:,.2f}")
        c4.metric("Foregone Yield", f"${metrics['estimated_foregone_yield']:,.2f}")

        flagged = results[results["Priority"] != "Compliant"]
        if not flagged.empty:
            fig = px.scatter(
                flagged,
                x="Days_Since_Sweep",
                y="Excess_Balance",
                size="Estimated_Foregone_Yield",
                color="Priority",
                hover_data=["Account_Number", "Bank_Name"],
                title="Idle Balance Exposure Map",
            )
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(results, use_container_width=True, hide_index=True)
        st.download_button(
            "Export results",
            data=to_excel_bytes(results),
            file_name="idle_balance_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_signatories() -> None:
    cfg = MODULES["Signatory Verification"]
    module_header("Signatory Verification", cfg["desc"], cfg["icon"])

    col1, col2 = st.columns(2)
    with col1:
        txn_upload = upload_section(cfg["sample"], "Upload transaction file")
    with col2:
        auth_upload = upload_section(cfg["extra_sample"], "Upload signatory register")

    txn_df = load_excel(txn_upload, required_columns=cfg["required"]) if txn_upload else None
    auth_df = load_excel(auth_upload) if auth_upload else None

    if txn_df is not None:
        results = signatories.analyze_signatories(txn_df, auth_df)
        metrics = signatories.summary_metrics(results)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Transactions", metrics["transactions_reviewed"])
        c2.metric("Non-Compliant", metrics["non_compliant"])
        c3.metric("Critical", metrics["critical"])
        c4.metric("High", metrics["high"])

        st.dataframe(results, use_container_width=True, hide_index=True)
        st.download_button(
            "Export results",
            data=to_excel_bytes(results),
            file_name="signatory_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_ai_prompt() -> None:
    cfg = MODULES["AI Assistant Prompt"]
    module_header("AI Assistant Prompt", cfg["desc"], cfg["icon"])

    st.markdown(
        "Use this production-ready system prompt to power an AI treasury analyst in ChatGPT, Claude, "
        "Cursor, or any LLM workspace. Copy it and pair with your exported Excel findings."
    )

    st.markdown(f'<div class="prompt-box">{TREASURY_AI_PROMPT}</div>', unsafe_allow_html=True)

    st.download_button(
        "Download prompt as text file",
        data=TREASURY_AI_PROMPT.encode("utf-8"),
        file_name="cap_ai_treasury_prompt.txt",
        mime="text/plain",
    )

    st.markdown("### Example user prompt")
    st.code(
        """Analyse the attached treasury exports and produce an executive briefing:

1. Reconciliation items open > 60 days with total exposure
2. Any round-trip patterns between ACC-1001 and ACC-1002
3. Bank charge variances exceeding 8% against sanctioned terms
4. Idle balances above sweep threshold with estimated foregone yield
5. Payments approved by unauthorised or inactive signatories

Rank all findings by severity and recommend owners and deadlines.""",
        language="text",
    )


def main() -> None:
    st.set_page_config(
        page_title="CAP AI Treasury Intelligence",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_styles()
    page = render_sidebar()

    renderers = {
        "Dashboard": render_dashboard,
        "Reconciliation Ageing": render_reconciliation,
        "Round-Trip Detection": render_round_tripping,
        "Bank Charge Audit": render_bank_charges,
        "Idle Balance Monitor": render_idle_balances,
        "Signatory Verification": render_signatories,
        "AI Assistant Prompt": render_ai_prompt,
    }

    renderers[page]()


if __name__ == "__main__":
    main()
