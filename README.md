```text
TRACK_ID=PS06

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:4F46E5,50:6366F1,100:06B6D4&height=230&section=header&text=SentinelRisk%20AI&fontSize=54&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Autonomous%20Banking%20Risk%20%26%20AML%20Investigation%20Copilot&descAlignY=62&descSize=17" width="100%" alt="SentinelRisk AI Header"/>

<br>

# 🛡️ SENTINELRISK AI

### **Autonomous Banking Fraud & Transaction Risk Investigation Copilot**

<p>
Detect anomalies • Connect evidence • Explain patterns • Assist investigators
</p>

<br>

<img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
<img src="https://img.shields.io/badge/SQLite-Local_Ledger-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
<img src="https://img.shields.io/badge/AI-Evidence_First-10B981?style=for-the-badge" alt="Evidence First AI"/>
<img src="https://img.shields.io/badge/Track-PS06-8B5CF6?style=for-the-badge" alt="PS06"/>

<br><br>

<img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=20&pause=1200&color=4F46E5&center=true&vCenter=true&width=800&lines=Detect+%E2%86%92+Investigate+%E2%86%92+Explain+%E2%86%92+Assist;Deterministic+Evidence+%2B+Generative+Reasoning;Every+Finding+Traces+Back+to+Evidence;Intelligent+Banking+Risk+Investigation" alt="Typing Animation"/>

<br><br>

[🚀 Quick Start](#-quick-start) •
[🧠 Architecture](#-system-architecture) •
[🔬 Detection](#-deterministic-risk-engine) •
[🔐 Guardrails](#-responsible-ai--guardrails) •
[🧪 Scenarios](#-benchmark-scenarios)

</div>

---

# 🛡️ SentinelRisk AI

> **An evidence-first banking risk investigation copilot that combines deterministic transaction intelligence with Gemini-powered investigation synthesis.**

SentinelRisk AI is designed to help fraud operations and AML investigation teams move from raw transaction data to an explainable investigation dossier.

The architecture deliberately separates:

```text
DETECTION → EVIDENCE → REASONING → ASSISTANCE
````

The deterministic engine identifies measurable transaction anomalies.

Gemini transforms those verified signals into a structured, human-readable investigation narrative.

---

<div align="center">

# 🧠 THE CORE IDEA

### **THE AI EXPLAINS THE EVIDENCE.**

### **IT DOES NOT MANUFACTURE THE EVIDENCE.**

</div>

```text
                         TRANSACTIONS
                              │
                              ▼
                    ┌──────────────────┐
                    │ CUSTOMER BASELINE│
                    └────────┬─────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │ DETERMINISTIC ENGINE   │
                 │                        │
                 │ • Velocity             │
                 │ • Off-hours            │
                 │ • Outliers             │
                 │ • Pattern divergence   │
                 └───────────┬────────────┘
                             │
                             ▼
                       VERIFIED SIGNALS
                             │
                             ▼
                  ┌──────────────────────┐
                  │  GEMINI INVESTIGATOR │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ INVESTIGATION DOSSIER│
                  └──────────┬───────────┘
                             │
                             ▼
                       HUMAN REVIEW
```

---

# ✨ WHAT MAKES IT DIFFERENT

| Capability              | SentinelRisk AI              |
| ----------------------- | ---------------------------- |
| 🔬 Anomaly Detection    | Deterministic rules          |
| 📊 Baseline Analysis    | Customer-specific            |
| ⚡ Velocity Detection    | Rapid transaction clustering |
| 🌙 Off-Hours Detection  | Unusual transaction timing   |
| 🧠 AI Reasoning         | Gemini-powered synthesis     |
| 🎯 Evidence Linking     | Transaction-level references |
| 📋 Investigation Report | Structured dossier           |
| 🔐 Safety               | Assistant-first architecture |
| 📦 Auditability         | JSON export                  |
| 💾 Storage              | Local SQLite ledger          |
| 🔄 Resilience           | Deterministic fallback       |

---

# 🔬 DETERMINISTIC RISK ENGINE

SentinelRisk never relies on an LLM alone to discover transaction anomalies.

The deterministic layer evaluates:

```text
┌─────────────────────────────────────────────┐
│              TRANSACTION ANALYSIS           │
├─────────────────────────────────────────────┤
│                                             │
│  💰 Amount Deviations                       │
│  ⚡ Transaction Velocity                    │
│  🌙 Off-Hours Activity                      │
│  📊 Customer Baseline                       │
│  🔗 Connected Transactions                  │
│  📈 Behavioral Divergence                   │
│                                             │
└─────────────────────────────────────────────┘
```

These signals become the evidence layer supplied to the investigator.

---

# 🧠 GEMINI INVESTIGATION LAYER

Once deterministic analysis identifies meaningful signals, Gemini receives structured evidence and produces an investigation-oriented explanation.

```text
EVIDENCE
   │
   ├── Customer Profile
   ├── Transaction IDs
   ├── Timestamps
   ├── Amounts
   ├── Channels
   ├── Baseline Statistics
   └── Detected Signals
            │
            ▼
     STRUCTURED PROMPT
            │
            ▼
        GEMINI MODEL
            │
            ▼
    INVESTIGATION DOSSIER
```

The result can include:

* 🎯 Primary finding
* 🔗 Connected transactions
* 📊 Baseline divergence
* 🧠 Pattern explanation
* 📋 Investigation context
* 🚀 Suggested next-step assistance

---

# 🏗️ SYSTEM ARCHITECTURE

```text
                         ┌─────────────────────┐
                         │    WEB DASHBOARD    │
                         │      PORT 8000      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FASTAPI       │
                         │     ORCHESTRATOR    │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌─────────────────────┐       ┌─────────────────────┐
          │ DETERMINISTIC       │       │ GEMINI INVESTIGATOR │
          │ RISK ENGINE         │       │                     │
          │                     │       │ Structured Prompt   │
          │ src/rules.py        │       │ Evidence Synthesis  │
          │                     │       │ Investigation Report │
          └──────────┬──────────┘       └──────────┬──────────┘
                     │                             │
                     └──────────────┬──────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │    SQLITE LEDGER    │
                         │   transactions.db   │
                         └─────────────────────┘
```

---

# 🔄 END-TO-END INVESTIGATION FLOW

```text
┌─────────────────┐
│   TRANSACTION   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DETECTION    │
│                 │
│ Amount          │
│ Velocity        │
│ Timing          │
│ Behavior        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    EVIDENCE     │
│                 │
│ TXN IDs         │
│ Amounts         │
│ Timestamps      │
│ Channels        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GEMINI REASONING│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   INVESTIGATION │
│     DOSSIER     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HUMAN REVIEW   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AUDIT JSON    │
└─────────────────┘
```

---

# 🧪 BENCHMARK SCENARIOS

SentinelRisk includes three representative banking investigation scenarios.

## 🟢 CUST_001 — ROUTINE SPEND

```text
Regular grocery
       +
Broadband utilities
       +
Expected amounts
       +
Expected timing
       +
Expected frequency
       ↓
Baseline aligned
       ↓
🟢 NO ATTENTION REQUIRED
```

The system demonstrates that normal behavior should remain normal instead of creating unnecessary alerts.

---

## 🔴 CUST_002 — ACCOUNT TAKEOVER

```text
Normal historical behavior
          │
          ▼
Unexpected activity
          │
     ┌────┼────┐
     ▼    ▼    ▼
  Rapid  3AM  IMPS
 Transfers Activity Burst
     │    │    │
     └────┼────┘
          ▼
    Velocity anomaly
          ▼
🔴 ATTENTION REQUIRED
```

The investigation connects suspicious transactions and highlights the deviation from the customer's established behavior.

---

## 🟡 CUST_003 — STRUCTURING

```text
₹49,900
   │
   ▼
₹49,500
   │
   ▼
₹49,800
   │
   ▼
₹49,900
   │
   ▼
Repeated near-threshold transfers
   │
   ▼
Behavioral divergence
   │
   ▼
🟡 ATTENTION REQUIRED
```

Rather than evaluating each transaction independently, SentinelRisk identifies the repeated behavioral pattern.

---

# 📊 RISK INDEX

The dashboard provides an interpretable risk overview instead of presenting an unexplained score.

```text
              ┌────────────────────┐
              │     RISK INDEX      │
              │                    │
              │        72          │
              │       /100         │
              │                    │
              └────────────────────┘

     Odd-Hours Activity       +12
     Velocity Spikes          +20
     Baseline Deviations      +40
```

Risk indicators can be traced back to measurable transaction behavior.

---

# 🔎 INVESTIGATION DOSSIER

The central investigation report organizes the evidence into one readable workflow.

```text
┌────────────────────────────────────────────┐
│          🔎 INVESTIGATION DOSSIER          │
├────────────────────────────────────────────┤
│                                            │
│ CUSTOMER DETAILS                           │
│ ─────────────────                          │
│ Customer ID                                │
│ Name                                       │
│ Account Type                               │
│ Profile Summary                            │
│                                            │
│ PRIMARY FINDING                            │
│ ─────────────────                          │
│ Investigation summary                      │
│                                            │
│ CONNECTED TRANSACTIONS                     │
│ ─────────────────────                      │
│ TXN ID                                     │
│ Timestamp                                  │
│ Amount                                     │
│ Payee                                      │
│ Channel                                    │
│                                            │
│ PATTERN DIVERGENCE                         │
│ ─────────────────                          │
│ Current activity vs baseline               │
│                                            │
│ NEXT-STEP ASSISTANCE                       │
│ ─────────────────────                      │
│ Investigation actions                      │
│                                            │
└────────────────────────────────────────────┘
```

---

# 🎯 EVIDENCE-ANCHORED REASONING

Instead of producing a vague statement such as:

```text
❌ "This customer appears fraudulent."
```

SentinelRisk structures investigation evidence around:

```text
✓ Transaction ID
✓ Timestamp
✓ Amount
✓ Payee
✓ Channel
✓ Customer baseline
✓ Detected anomaly
✓ Pattern relationship
✓ Investigation context
```

The goal is simple:

<div align="center">

### **EVIDENCE FIRST → INTERPRETATION SECOND → ASSISTANCE THIRD**

</div>

---

# 🔐 RESPONSIBLE AI & GUARDRAILS

SentinelRisk is designed as an **investigation assistant**, not an autonomous fraud adjudicator.

```text
                  VERIFIED DATA
                       │
                       ▼
              DETERMINISTIC RULES
                       │
                       ▼
                 RISK SIGNALS
                       │
                       ▼
              GEMINI EXPLANATION
                       │
                       ▼
              INVESTIGATION DOSSIER
                       │
                       ▼
                 HUMAN REVIEW
```

### The system can:

* 🔬 Detect measurable anomalies
* 🔗 Connect transaction evidence
* 🧠 Explain behavioral divergence
* 📋 Generate investigation summaries
* 🚀 Prepare investigation actions
* 📦 Export audit information

### The system does not claim to:

* ❌ Replace compliance investigators
* ❌ Make legal determinations
* ❌ Automatically accuse customers of fraud
* ❌ Treat an LLM response as ground truth

---

# 🛡️ ASSISTED INVESTIGATOR ACTIONS

The interface can prepare actions such as:

```text
🔒 Freeze Outbound Rails

📄 Request KYC / Income Proof

🟢 Clear Case as Benign

📦 Download Audit JSON
```

These actions are presented as **assistance workflows** for human investigators.

---

# 📦 AUDITABLE OUTPUT

Investigation context can be exported as JSON.

Example:

```json
{
  "customer_id": "CUST_003",
  "risk_index": 72,
  "deterministic_flags": [
    "velocity_spike",
    "baseline_deviation"
  ],
  "connected_transactions": [
    "TXN_302",
    "TXN_303",
    "TXN_304"
  ],
  "assistant_policy": "NO_AUTONOMOUS_VERDICT"
}
```

This creates a portable record of the investigation context.

---

# 🔄 GRACEFUL DEGRADATION

SentinelRisk maintains useful deterministic functionality even when the external AI layer is unavailable.

```text
                    REQUEST
                       │
                       ▼
             ┌─────────────────┐
             │ DETERMINISTIC   │
             │ ANALYSIS        │
             └────────┬────────┘
                      │
                      ▼
               GEMINI AVAILABLE?
                 /           \
               YES            NO
                │              │
                ▼              ▼
             GEMINI       FALLBACK LOGIC
                │              │
                └──────┬───────┘
                       ▼
                 FINAL REPORT
```

---

# 💾 DATA LAYER

SQLite provides a lightweight local transaction ledger.

```text
Customer
   │
   ├── Profile
   ├── Account Type
   ├── Baseline
   └── Transactions
          │
          ├── TXN ID
          ├── Timestamp
          ├── Amount
          ├── Payee
          └── Channel
```

The seeded benchmark data provides reproducible scenarios for evaluation.

---

# 📂 PROJECT STRUCTURE

```text
banking-risk-assistant/
│
├── app.py
│   └── FastAPI application, routes, database initialization & UI
│
├── requirements.txt
│   └── Python dependencies
│
├── README.md
│   └── Project documentation
│
├── .gitignore
│   └── Environment & virtual-environment exclusions
│
├── src/
│   ├── rules.py
│   │   └── Deterministic anomaly detection engine
│   │
│   └── investigator.py
│       └── Gemini orchestration & structured prompts
│
└── data/
    └── seed_data.py
        └── Benchmark customer & transaction scenarios
```

---

# ⚡ QUICK START

## 1️⃣ Clone

```bash
git clone https://github.com/Adhi426/<YOUR-REPO-NAME>.git
cd <YOUR-REPO-NAME>
```

## 2️⃣ Create Virtual Environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

## 4️⃣ Configure Gemini

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

### Windows CMD

```cmd
set GEMINI_API_KEY=YOUR_API_KEY
```

### Linux / macOS

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

## 5️⃣ Launch

```bash
python app.py
```

Open:

```text
http://localhost:8000
```

---

# 🌐 TECHNOLOGY STACK

<div align="center">

| Layer        | Technology                       |
| ------------ | -------------------------------- |
| 🐍 Backend   | Python 3.11                      |
| ⚡ API        | FastAPI                          |
| 🧠 AI        | Google Gemini                    |
| 💾 Database  | SQLite                           |
| 🔬 Detection | Deterministic Statistical Rules  |
| 📋 Reporting | Structured Investigation Dossier |
| 🌐 Interface | HTML / CSS / JavaScript          |
| 📦 Audit     | JSON Export                      |

</div>

---

# 🎥 DEMO

<div align="center">

## 🎬 SentinelRisk AI — 2 Minute Walkthrough

### `INSERT_YOUR_YOUTUBE_OR_LOOM_LINK_HERE`

```text
00:00  →  Problem
00:20  →  Dashboard
00:40  →  Routine Spend
01:00  →  Account Takeover
01:20  →  Structuring
01:40  →  AI Investigation
02:00  →  Audit & Guardrails
```

</div>

---

# 🧭 DESIGN PHILOSOPHY

```text
╔═══════════════════════════════════════════════╗
║                                               ║
║             EVIDENCE → REASONING              ║
║                                               ║
║                    NOT                         ║
║                                               ║
║             REASONING → EVIDENCE              ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

The system is designed so that AI reasoning is grounded in transaction signals rather than being the source of those signals.

---

# 📈 INVESTIGATION PIPELINE

```text
      💳 TRANSACTION
             │
             ▼
      🔬 DETECTION
             │
             ▼
       📊 BASELINE
             │
             ▼
        ⚠️ SIGNAL
             │
             ▼
       🔗 EVIDENCE
             │
             ▼
        🧠 GEMINI
             │
             ▼
       📋 DOSSIER
             │
             ▼
       👤 REVIEW
             │
             ▼
       📦 AUDIT
```

---

# 🔒 VALIDATION

```text
┌───────────────────────────────────────────┐
│              VALIDATION LAYER             │
├───────────────────────────────────────────┤
│                                           │
│ Track ID              PS06                │
│                                           │
│ AI Engine             Gemini              │
│                                           │
│ Detection             Deterministic       │
│                                           │
│ Database              SQLite              │
│                                           │
│ Audit                 JSON                │
│                                           │
│ Policy                Assistant Only      │
│                                           │
└───────────────────────────────────────────┘
```

---

# 🌟 SENTINELRISK IN ONE VIEW

<div align="center">

### 🔬 **DETECT**

Find measurable anomalies.

### 🔗 **CONNECT**

Link the transactions that matter.

### 🧠 **EXPLAIN**

Turn evidence into understandable reasoning.

### 👤 **ASSIST**

Prepare the investigator for the next step.

### 📦 **AUDIT**

Preserve the investigation context.

</div>

---

# 🚀 THE VISION

Financial risk investigation should not feel like searching through thousands of disconnected records.

It should feel like having an intelligent investigation desk beside you.

```text
                  TRANSACTIONS
                       │
                       ▼
                ┌─────────────┐
                │ SENTINELRISK│
                └──────┬──────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       DETECT        CONNECT      EXPLAIN
          │            │            │
          └────────────┼────────────┘
                       ▼
                  INVESTIGATOR
                       │
                       ▼
                  HUMAN REVIEW
```

<div align="center">

### **LESS NOISE.**

### **MORE EVIDENCE.**

### **FASTER INVESTIGATION.**

</div>

---

# 📚 REFERENCES

* Google Gemini / Google Generative AI
* FastAPI
* SQLite
* Transaction Monitoring & AML Investigation Concepts
* Explainable AI
* Human-in-the-Loop Systems

---

<div align="center">

<br>

<img src="https://capsule-render.vercel.app/api?type=rect&color=0:4F46E5,50:6366F1,100:06B6D4&height=4&section=header" width="100%" alt="Divider"/>

<br><br>

<img src="https://readme-typing-svg.demolab.com?font=Inter&weight=700&size=25&pause=1400&color=4F46E5&center=true&vCenter=true&width=800&lines=Detect+the+Signal.;Understand+the+Pattern.;Assist+the+Investigator.;Build+Smarter+Financial+Intelligence" alt="SentinelRisk Footer Animation"/>

<br><br>
# 🛡️ **SENTINELRISK AI**

### *Detect the signal. Understand the pattern. Assist the investigator.*

<br>

<img src="https://img.shields.io/badge/EVIDENCE--FIRST-4F46E5?style=for-the-badge" alt="Evidence First"/>
<img src="https://img.shields.io/badge/AI--ASSISTED-7C3AED?style=for-the-badge" alt="AI Assisted"/>
<img src="https://img.shields.io/badge/SAFETY--FIRST-059669?style=for-the-badge" alt="Safety First"/>
<img src="https://img.shields.io/badge/AUDITABLE-0891B2?style=for-the-badge" alt="Auditable"/>

<br><br>

**INTELLIGENT • EXPLAINABLE • EVIDENCE-FIRST • HUMAN-ASSISTED**

<br>

`SENTINELRISK AI • PS06 • 2026`

<br><br>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:06B6D4,50:6366F1,100:4F46E5&height=130&section=footer&animation=fadeIn" width="100%" alt="SentinelRisk Footer"/>

</div>
```

This version specifically fixes the **first animation** by using the direct Capsule Render image URL instead of the broken nested Markdown/HTML format. It also keeps `TRACK_ID=PS06` as the **absolute first line**, which is important for your submission format.
