TRACK_ID=PS06

# Banking - Transaction Risk Investigation Assistant (SentinelRisk Copilot)

Validation Key: `<BROADCAST_VALIDATION_KEY>`

## Overview
An autonomous transaction risk investigation assistant for banking fraud desks. The system performs deterministic pre-screening (detecting velocity bursts, odd-hours activity, baseline statistical deviations, structuring/smurfing, and unverified new payee bursts), followed by grounded GenAI synthesis using Google Gemini. It produces actionable investigation dossiers while maintaining zero-hallucination guardrails and explicitly clearing benign profiles.

## Key Features & Architecture
- **Deterministic Rule Engine (`src/rules.py`)**: 100% isolated rule-based pre-scan for rapid anomaly detection.
- **Grounded GenAI Investigator (`src/investigator.py`)**: Structured LLM reasoning with model fallback (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`).
- **Zero-Hallucination & Discipline**: Line 1 explicitly states whether attention is required. Never accuses of fraud; flags, explains, and hands judgment to human compliance investigators.
- **Interactive Citation Tracing**: Click/hover any transaction ID (`TXN_xxx`) to highlight the corresponding row in the historical ledger.
- **Sandbox Mode**: Inject live custom transactions to test custom fraud scenarios in real time.
- **One-Click Export**: Export complete investigation dossiers as Markdown (`.md`) or audit JSON.

## Setup & Execution

### One Command to Run
```bash
pip install -r requirements.txt
python app.py
```
The application starts and serves on **http://localhost:8000** (with automatic port fallback if port 8000 is occupied).

### Environment Configuration
Copy `.env.example` to `.env` or set the API key in your environment:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```
*(Alternatively, enter your API key directly in the web UI header modal).*

## Generated Test Data & Scenarios
The SQLite database (`transactions.db`) is automatically seeded at startup with four representative profiles:
1. **CUST_001 (Priya Sharma)**: Clean routine spend (salaried, utilities, groceries) -> **NO ATTENTION REQUIRED**.
2. **CUST_002 (Vikram Rathore)**: Account Takeover pattern (3:00 AM velocity burst to unverified new payee) -> **ATTENTION REQUIRED**.
3. **CUST_003 (Ananya Sen)**: Structuring / Smurfing pattern (multiple ₹49,900 transfers right below ₹50,000 threshold) -> **ATTENTION REQUIRED**.
4. **CUST_004 (Arjun Mehta)**: HNI Clean Baseline (high-value legitimate investments/travel) -> **NO ATTENTION REQUIRED** (Zero false positives).

## Demo Video Link
- Demo Video: `https://youtube.com/watch?v=demo-video-link-placeholder`