# CAP AI Treasury Intelligence

A Streamlit application for corporate treasury and banking controls — built with CAP AI branding.

## Features

| Module | Capability |
|--------|------------|
| **Reconciliation Ageing** | Age open recon items, bucket by days outstanding, prioritise chase actions |
| **Round-Trip Detection** | Detect suspicious fund movements between related accounts |
| **Bank Charge Audit** | Recompute fees/interest against sanctioned contractual terms |
| **Idle Balance Monitor** | Flag cash above sweep thresholds with foregone yield estimates |
| **Signatory Verification** | Match payment approvers to the authorised signatory register |

- Excel import and export on every module
- Sample templates included
- Interactive charts (Plotly)
- Production-ready AI system prompt

## Quick start

```bash
cd cap-treasury-app
pip install -r requirements.txt
python scripts/generate_samples.py
streamlit run app.py
```

## Excel templates

Run `python scripts/generate_samples.py` to create sample files in `data/samples/`.

## AI Treasury Prompt

The full system prompt is available in the app under **AI Assistant Prompt**, or in `prompts/treasury_analyst_prompt.txt`.

---

**CAP AI** — Treasury Intelligence Platform
