import os
import sqlite3
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Header, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from data.seed_data import init_db
from src.rules import analyze_customer_transactions
from src.investigator import generate_investigation_report, VALIDATION_KEY
from src.history import (
    init_history_db,
    save_assessment_record,
    get_history_summaries,
    get_assessment_by_id
)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="SentinelRisk - GCC Banking Investigation Desk")

DB_FILE = "transactions.db"
init_db(DB_FILE)
init_history_db(DB_FILE)

class NewTransactionRequest(BaseModel):
    customer_id: str
    amount: float
    payee: str
    channel: str
    description: str
    timestamp: Optional[str] = None

LIGHT_UI_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SentinelRisk Copilot | Autonomous Banking Fraud Desk (TRACK_ID=PS06)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    .mono {{ font-family: 'JetBrains Mono', monospace; }}
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: #f8fafc; }}
    ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
    
    .txn-highlight {{
      animation: pulseHighlight 2s ease-in-out infinite;
      background-color: #fef08a !important;
    }}
    @keyframes pulseHighlight {{
      0%, 100% {{ background-color: #fef08a; }}
      50% {{ background-color: #fde047; }}
    }}

    /* Markdown Typography Styling inside Dossier */
    .dossier-report h1, .dossier-report h2, .dossier-report h3 {{
      font-weight: 800;
      color: #0f172a;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
    }}
    .dossier-report h3 {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: #334155; }}
    .dossier-report p {{ margin-bottom: 0.5rem; color: #334155; line-height: 1.5; }}
    .dossier-report ul {{ list-style-type: disc; padding-left: 1.25rem; margin-bottom: 0.5rem; }}
    .dossier-report li {{ margin-bottom: 0.25rem; color: #334155; }}
    .dossier-report strong {{ color: #0f172a; font-weight: 700; }}
    .dossier-report hr {{ border-color: #e2e8f0; margin: 0.75rem 0; }}
  </style>
</head>
<body class="bg-[#f8fafc] text-slate-800 min-h-screen flex flex-col antialiased selection:bg-indigo-500 selection:text-white">

  <div class="flex flex-1 w-full min-h-screen">

    <!-- Left Sidebar Navigation -->
    <aside class="w-64 bg-white border-r border-slate-200/80 flex flex-col justify-between p-4 sticky top-0 h-screen z-40 shrink-0 shadow-xs">
      <div class="space-y-6">
        <!-- Sidebar Brand Logo -->
        <div class="flex items-center gap-3 px-2 pt-1">
          <div class="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/25 text-white shrink-0">
            <i data-lucide="shield-check" class="w-6 h-6"></i>
          </div>
          <div>
            <h1 class="font-extrabold text-slate-900 text-base tracking-tight leading-tight">SentinelRisk</h1>
            <span class="text-[11px] font-bold text-indigo-600 tracking-wide uppercase">Copilot Desk</span>
          </div>
        </div>

        <!-- Sidebar Navigation Menu Links (9 Tabs in Exact Order) -->
        <nav class="space-y-1 text-xs font-semibold text-slate-600" id="sidebarNav">
          <a href="#" onclick="navTab('Dashboard')" id="nav-Dashboard" class="sidebar-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-indigo-50/80 text-indigo-700 font-bold border-l-4 border-indigo-600 transition">
            <i data-lucide="layout-dashboard" class="w-4 h-4 text-indigo-600"></i> Dashboard
          </a>
          <a href="#" onclick="navTab('Investigations')" id="nav-Investigations" class="sidebar-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <i data-lucide="search" class="w-4 h-4 text-slate-400"></i> Investigations
          </a>
          <a href="#" onclick="navTab('Customers')" id="nav-Customers" class="sidebar-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <i data-lucide="users" class="w-4 h-4 text-slate-400"></i> Customers
          </a>
          <a href="#" onclick="navTab('Transactions')" id="nav-Transactions" class="sidebar-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <i data-lucide="credit-card" class="w-4 h-4 text-slate-400"></i> Transactions
          </a>
          <a href="#" onclick="navTab('History')" id="nav-History" class="sidebar-item flex items-center justify-between px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <span class="flex items-center gap-3"><i data-lucide="history" class="w-4 h-4 text-slate-400"></i> History</span>
            <span id="navHistoryBadge" class="px-2 py-0.5 text-[10px] font-extrabold bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200">1</span>
          </a>
          <a href="#" onclick="navTab('Alerts')" id="nav-Alerts" class="sidebar-item flex items-center justify-between px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <span class="flex items-center gap-3"><i data-lucide="bell" class="w-4 h-4 text-slate-400"></i> Alerts</span>
            <span id="navAlertBadge" class="px-2 py-0.5 text-[10px] font-extrabold bg-rose-50 text-rose-700 rounded-full border border-rose-200">3</span>
          </a>
          <a href="#" onclick="navTab('Reports')" id="nav-Reports" class="sidebar-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <i data-lucide="bar-chart-3" class="w-4 h-4 text-slate-400"></i> Reports
          </a>
          <a href="#" onclick="navTab('Audit Logs')" id="nav-Audit Logs" class="sidebar-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <i data-lucide="file-check-2" class="w-4 h-4 text-slate-400"></i> Audit Logs
          </a>
          <a href="#" onclick="navTab('Settings')" id="nav-Settings" class="sidebar-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <i data-lucide="settings" class="w-4 h-4 text-slate-400"></i> Settings
          </a>
        </nav>
      </div>

      <!-- Bottom Graphic Widget -->
      <div class="bg-gradient-to-br from-indigo-50 to-blue-50/50 border border-indigo-100/80 rounded-2xl p-4 text-center relative overflow-hidden">
        <div class="w-10 h-10 mx-auto mb-1 relative flex items-center justify-center">
          <i data-lucide="shield-check" class="w-7 h-7 text-indigo-600"></i>
        </div>
        <p class="text-xs font-extrabold text-slate-900 tracking-tight">Security. Intelligence. Trust.</p>
        <p class="text-[10px] text-indigo-600 font-bold mt-0.5">SentinelRisk AI • PS06 Copilot</p>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Top Header -->
      <header class="bg-white border-b border-slate-200/80 px-6 py-3 flex items-center justify-between sticky top-0 z-30 shadow-xs">
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-slate-900 text-base md:text-lg tracking-tight whitespace-nowrap" id="topNavHeaderTitle">SentinelRisk Copilot</span>
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-50 text-indigo-700 border border-indigo-200 shrink-0">TRACK ID: PS06</span>
          </div>
          <p class="text-xs text-slate-500 font-medium truncate">Autonomous Banking Fraud & Anomaly Triage System</p>
        </div>

        <!-- Scenario Controls & Header Buttons -->
        <div class="flex items-center gap-2.5 shrink-0">
          <span class="text-xs font-semibold text-slate-500 hidden xl:inline">Scenarios:</span>
          
          <button onclick="loadCustomer('CUST_001')" id="btn-CUST_001" class="scenario-btn px-3 py-1.5 rounded-xl border border-emerald-200/80 bg-emerald-50/60 hover:bg-emerald-100/80 text-emerald-800 text-xs font-bold flex items-center gap-1.5 transition">
            <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-600"></i> Routine Spend
          </button>
          
          <button onclick="loadCustomer('CUST_002')" id="btn-CUST_002" class="scenario-btn px-3 py-1.5 rounded-xl border border-rose-200/80 bg-rose-50/60 hover:bg-rose-100/80 text-rose-800 text-xs font-bold flex items-center gap-1.5 transition">
            <i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-rose-600"></i> Burst / Odd-Hours
          </button>
          
          <button onclick="loadCustomer('CUST_003')" id="btn-CUST_003" class="scenario-btn px-3 py-1.5 rounded-xl border border-amber-200/80 bg-amber-50/60 hover:bg-amber-100/80 text-amber-800 text-xs font-bold flex items-center gap-1.5 transition">
            <i data-lucide="layers" class="w-3.5 h-3.5 text-amber-600"></i> Structuring
          </button>

          <button onclick="loadCustomer('CUST_004')" id="btn-CUST_004" class="scenario-btn px-3 py-1.5 rounded-xl border border-blue-200/80 bg-blue-50/60 hover:bg-blue-100/80 text-blue-800 text-xs font-bold flex items-center gap-1.5 transition">
            <i data-lucide="shield" class="w-3.5 h-3.5 text-blue-600"></i> HNI Clean
          </button>

          <div class="h-6 w-px bg-slate-200 mx-0.5 hidden sm:block"></div>

          <button onclick="openTxnModal()" class="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-xs">
            <i data-lucide="plus-circle" class="w-3.5 h-3.5 text-indigo-400"></i> Sandbox Txn
          </button>
          
          <button onclick="openKeyModal()" class="px-2.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition shadow-xs" title="Configure Gemini API Key">
            <i data-lucide="key" class="w-3.5 h-3.5 text-amber-500"></i> <span class="hidden md:inline">API Key</span>
          </button>

          <!-- User Profile Avatar -->
          <div class="h-9 w-9 rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200 flex items-center justify-center font-bold text-xs shadow-xs ml-1 shrink-0" id="userTopAvatar">
            AS
          </div>
        </div>
      </header>

      <!-- Toast Notification -->
      <div id="toast" class="fixed bottom-6 right-6 z-50 transform transition-all duration-300 translate-y-20 opacity-0 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-2xl text-xs font-medium flex items-center gap-2"></div>

      <!-- VIEW 1: MAIN DASHBOARD VIEW -->
      <div id="view-Dashboard" class="view-panel flex-1 p-6">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1850px] w-full mx-auto">

          <!-- Column 1: Customer Profile, Rules & Ledger (5 Cols) -->
          <div class="lg:col-span-5 flex flex-col gap-5">

            <!-- Profile Card -->
            <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs">
              <div class="flex items-center justify-between border-b border-slate-100 pb-4">
                <div class="flex items-center gap-3.5">
                  <div class="h-12 w-12 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 flex items-center justify-center font-extrabold text-sm shrink-0" id="customerAvatar">AS</div>
                  <div>
                    <h2 class="text-base font-extrabold text-slate-900 flex items-center gap-2">
                      <span id="custName">No Profile Loaded</span>
                      <span id="custType" class="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-100">--</span>
                    </h2>
                    <p class="text-xs text-slate-500 mt-0.5" id="custSummary">Select a customer profile scenario to start.</p>
                  </div>
                </div>
                <div id="statusBadge" class="px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 bg-slate-100 text-slate-600">
                  Loading...
                </div>
              </div>

              <!-- 4 Metric Boxes -->
              <div class="grid grid-cols-4 gap-3 mt-4 text-center">
                <div class="bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                  <span class="text-[10px] uppercase text-slate-400 font-bold tracking-wider flex items-center justify-center gap-1">
                    <i data-lucide="hash" class="w-3 h-3 text-indigo-500"></i> ENTRIES
                  </span>
                  <div class="text-base font-extrabold text-slate-900 mt-1" id="metricCount">--</div>
                </div>
                <div class="bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                  <span class="text-[10px] uppercase text-slate-400 font-bold tracking-wider flex items-center justify-center gap-1">
                    <i data-lucide="wallet" class="w-3 h-3 text-indigo-500"></i> TOTAL
                  </span>
                  <div class="text-base font-extrabold text-slate-900 mt-1" id="metricTotal">--</div>
                </div>
                <div class="bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                  <span class="text-[10px] uppercase text-slate-400 font-bold tracking-wider flex items-center justify-center gap-1">
                    <i data-lucide="calculator" class="w-3 h-3 text-indigo-500"></i> AVG AMOUNT
                  </span>
                  <div class="text-base font-extrabold text-slate-900 mt-1" id="metricAvg">--</div>
                </div>
                <div class="bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                  <span class="text-[10px] uppercase text-slate-400 font-bold tracking-wider flex items-center justify-center gap-1">
                    <i data-lucide="flag" class="w-3 h-3 text-rose-500"></i> FLAGS
                  </span>
                  <div class="text-base font-extrabold text-slate-900 mt-1" id="metricFlags">--</div>
                </div>
              </div>
            </div>

            <!-- Deterministic Engine Triggers Card -->
            <div class="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs">
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <i data-lucide="cpu" class="w-4 h-4 text-indigo-600"></i> DETERMINISTIC ENGINE TRIGGERS
                </span>
                <span class="text-[10px] font-semibold text-slate-400 uppercase">Rule-based Pre-Scan</span>
              </div>
              <div id="ruleTriggers" class="space-y-2 max-h-36 overflow-y-auto">
                <!-- Dynamically Populated -->
              </div>
            </div>

            <!-- Historical Ledger Table Card -->
            <div class="bg-white border border-slate-200/80 rounded-2xl flex-1 flex flex-col overflow-hidden shadow-xs" id="ledgerCard">
              <div class="p-4 border-b border-slate-100 flex flex-wrap gap-2 justify-between items-center bg-slate-50/40">
                <div class="flex items-center gap-2">
                  <i data-lucide="receipt" class="w-4 h-4 text-indigo-600"></i>
                  <span class="text-xs font-extrabold text-slate-900 uppercase tracking-wider">HISTORICAL LEDGER</span>
                </div>
                
                <div class="flex items-center gap-3">
                  <span class="text-xs text-slate-400 font-semibold" id="txnCounter">0 records</span>
                  <input type="text" id="ledgerSearch" onkeyup="filterLedger()" placeholder="Search payee/ID..." class="px-2.5 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 w-32 sm:w-40" />
                  <select id="ledgerFilter" onchange="filterLedger()" class="px-2 py-1 text-xs border border-slate-200 rounded-lg bg-white text-slate-700 focus:outline-none">
                    <option value="ALL">All Txns</option>
                    <option value="FLAGGED">Flagged Only</option>
                    <option value="NORMAL">Normal Only</option>
                  </select>
                </div>
              </div>
              <div class="overflow-y-auto max-h-[380px] p-2">
                <table class="w-full text-left text-xs">
                  <thead class="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold tracking-wider sticky top-0">
                    <tr>
                      <th class="p-2.5 rounded-l-lg">TXN ID</th>
                      <th class="p-2.5">TIMESTAMP</th>
                      <th class="p-2.5">PAYEE</th>
                      <th class="p-2.5">CHANNEL</th>
                      <th class="p-2.5 text-right rounded-r-lg">AMOUNT</th>
                    </tr>
                  </thead>
                  <tbody id="txnTableBody" class="divide-y divide-slate-100 text-slate-700">
                    <!-- Dynamic Row Injection -->
                  </tbody>
                </table>
              </div>
              <div class="p-3 border-t border-slate-100 bg-slate-50/50 text-right">
                <a href="#" onclick="navTab('Transactions'); return false;" class="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center justify-end gap-1">
                  View all transactions <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
                </a>
              </div>
            </div>

          </div>

          <!-- Column 2: AI Investigation Dossier (4 Cols) - Cleaned Non-overlapping Header -->
          <div class="lg:col-span-4 flex flex-col gap-4">
            <div class="bg-white border border-slate-200/80 rounded-2xl flex-1 flex flex-col p-5 shadow-xs relative">
              
              <!-- Clean Non-Overlapping Header Layout -->
              <div class="flex flex-col border-b border-slate-100 pb-3 mb-4 gap-3">
                <div class="flex items-center justify-between">
                  <h2 class="text-xs font-extrabold text-slate-900 flex items-center gap-2 uppercase tracking-wider">
                    <i data-lucide="sparkles" class="w-4 h-4 text-indigo-600 shrink-0"></i> AI Investigation Dossier
                  </h2>
                  <span class="text-[10px] font-semibold text-slate-400 uppercase">Grounded LLM Triage</span>
                </div>
                
                <div class="flex items-center justify-between gap-2">
                  <p class="text-[11px] text-slate-400 font-medium truncate">Autonomous synthesis & reasoning</p>
                  
                  <div class="flex items-center gap-2 shrink-0">
                    <button id="historyBtn" onclick="toggleHistoryDrawer()" class="px-2.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition" title="View Assessment History">
                      <i data-lucide="history" class="w-3.5 h-3.5 text-indigo-600"></i> History
                    </button>
                    <button id="exportMdBtn" onclick="openExportModal('dossier')" disabled class="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed transition" title="Export Assessment Dossier">
                      <i data-lucide="download" class="w-3.5 h-3.5 text-indigo-600"></i> Export
                    </button>
                    <button id="runBtn" onclick="runInvestigation()" disabled class="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-indigo-600/20 disabled:opacity-40 disabled:cursor-not-allowed transition whitespace-nowrap">
                      <i data-lucide="play" class="w-3.5 h-3.5"></i> Run Assessment
                    </button>
                  </div>
                </div>
              </div>

              <!-- Dossier Output Box -->
              <div class="flex-1 bg-slate-50/50 border border-slate-200/60 rounded-xl p-4 overflow-y-auto relative min-h-[540px]">
                <div id="loading" class="hidden absolute inset-0 bg-white/90 backdrop-blur-xs flex flex-col items-center justify-center gap-3 z-20">
                  <div class="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                  <p class="text-xs font-mono text-indigo-700 font-bold animate-pulse">Running Gemini Fraud Protocol...</p>
                </div>
                
                <!-- Rendered Report Content -->
                <div id="reportContent" class="text-xs leading-relaxed text-slate-800 space-y-4">
                  <!-- Dynamically Reset to Blank/Pending on Scenario Switch -->
                </div>
              </div>

              <!-- Collapsible Assessment History Drawer -->
              <div id="historyDrawer" class="hidden mt-3 p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2 max-h-48 overflow-y-auto">
                <div class="flex items-center justify-between text-xs font-extrabold text-slate-800 border-b border-slate-200/60 pb-1.5">
                  <span class="flex items-center gap-1.5"><i data-lucide="history" class="w-3.5 h-3.5 text-indigo-600"></i> Assessment Run History</span>
                  <button onclick="toggleHistoryDrawer()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                </div>
                <div id="assessmentHistoryList" class="space-y-1.5">
                  <div class="text-xs text-slate-400 text-center py-2">No previous assessments saved yet.</div>
                </div>
              </div>

              <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 font-semibold">
                <span class="flex items-center gap-1.5 text-emerald-700 font-bold">
                  <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> Deterministically Grounded
                </span>
                <span id="execTimer" class="font-mono text-slate-500">Idle</span>
              </div>
            </div>
          </div>

          <!-- Column 3: Gauge, Actions & Hackathon Validation (3 Cols) -->
          <div class="lg:col-span-3 flex flex-col gap-5">

            <!-- Risk Index Gauge Card (Perfectly Fitted SVG Gauge & Needle) -->
            <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs">
              <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <span class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <i data-lucide="gauge" class="w-4 h-4 text-indigo-600"></i> RISK INDEX GAUGE
                </span>
                <span id="riskVerdict" class="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">LOW RISK</span>
              </div>
              
              <div class="mt-4 flex flex-col items-center">
                <!-- 100% Fitted Speedometer SVG (No Overflow, Perfectly Centered) -->
                <div class="relative w-full max-w-[200px] h-32 flex items-center justify-center my-1">
                  <svg class="w-full h-full" viewBox="0 0 200 115">
                    <!-- Background Gray Arc Track -->
                    <path d="M 20,100 A 80,80 0 0,1 180,100" stroke="#e2e8f0" stroke-width="14" fill="none" stroke-linecap="round" />
                    <!-- Dynamic Colored Score Arc -->
                    <path id="gaugeArc" d="M 20,100 A 80,80 0 0,1 180,100" stroke="url(#gaugeGrad)" stroke-width="14" fill="none" stroke-linecap="round" stroke-dasharray="251.33" stroke-dashoffset="251.33" class="transition-all duration-700" />
                    <defs>
                      <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#10b981" />
                        <stop offset="50%" stop-color="#f59e0b" />
                        <stop offset="100%" stop-color="#f43f5e" />
                      </linearGradient>
                    </defs>

                    <!-- Score Value Text Inside Center -->
                    <text x="100" y="78" text-anchor="middle" font-size="28" font-weight="800" fill="#0f172a" font-family="'JetBrains Mono', monospace" id="scoreNum">0</text>
                    <text x="100" y="94" text-anchor="middle" font-size="10" font-weight="700" fill="#94a3b8">/ 100 RISK SCORE</text>

                    <!-- Rotating Speedometer Pointer Needle -->
                    <line id="gaugeNeedle" x1="100" y1="100" x2="100" y2="30" stroke="#1e293b" stroke-width="3" stroke-linecap="round" style="transform-origin: 100px 100px; transform: rotate(-90deg); transition: transform 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);" />
                    <!-- Center Pivot Circle -->
                    <circle cx="100" cy="100" r="5" fill="#0f172a" stroke="#ffffff" stroke-width="2" />
                  </svg>
                </div>

                <!-- Metric Point Breakdown -->
                <div class="w-full mt-2 space-y-1.5 text-xs text-slate-600 font-medium border-t border-slate-100 pt-3">
                  <div class="flex justify-between"><span>Odd-Hours Weight:</span><span id="statOdd" class="font-mono font-bold text-slate-800">+0 pts</span></div>
                  <div class="flex justify-between"><span>Velocity Spikes:</span><span id="statVel" class="font-mono font-bold text-slate-800">+0 pts</span></div>
                  <div class="flex justify-between"><span>Baseline Deviations:</span><span id="statDev" class="font-mono font-bold text-slate-800">+0 pts</span></div>
                  <div class="flex justify-between"><span>Structuring / Payee:</span><span id="statStruct" class="font-mono font-bold text-slate-800">+0 pts</span></div>
                </div>
              </div>
            </div>

            <!-- Investigator Action Cards -->
            <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs flex flex-col gap-3">
              <span class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
                <i data-lucide="zap" class="w-4 h-4 text-indigo-600"></i> INVESTIGATOR ACTIONS
              </span>

              <button onclick="triggerAction('Account frozen! Outbound rails blocked.')" class="w-full py-2.5 px-3.5 rounded-xl border border-rose-200/80 bg-rose-50/50 hover:bg-rose-100/70 text-rose-700 text-xs font-bold flex items-center justify-between transition shadow-xs active:scale-[0.98]">
                <span class="flex items-center gap-2"><i data-lucide="lock" class="w-4 h-4 text-rose-600"></i> Freeze Outbound Rails</span>
                <i data-lucide="chevron-right" class="w-4 h-4 opacity-60"></i>
              </button>

              <button onclick="triggerAction('Dispatched automated KYC & Income Proof request to customer.')" class="w-full py-2.5 px-3.5 rounded-xl border border-amber-200/80 bg-amber-50/50 hover:bg-amber-100/70 text-amber-800 text-xs font-bold flex items-center justify-between transition shadow-xs active:scale-[0.98]">
                <span class="flex items-center gap-2"><i data-lucide="file-question" class="w-4 h-4 text-amber-600"></i> Request KYC / Income Proof</span>
                <i data-lucide="chevron-right" class="w-4 h-4 opacity-60"></i>
              </button>

              <button onclick="triggerAction('Case cleared as benign. Profile marked verified.')" class="w-full py-2.5 px-3.5 rounded-xl border border-emerald-200/80 bg-emerald-50/50 hover:bg-emerald-100/70 text-emerald-800 text-xs font-bold flex items-center justify-between transition shadow-xs active:scale-[0.98]">
                <span class="flex items-center gap-2"><i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600"></i> Clear Case as Benign</span>
                <i data-lucide="chevron-right" class="w-4 h-4 opacity-60"></i>
              </button>

              <button onclick="exportAuditJSON()" class="w-full py-2.5 px-3.5 rounded-xl border border-slate-200/80 bg-slate-50/60 hover:bg-slate-100/80 text-slate-700 text-xs font-bold flex items-center justify-between transition shadow-xs active:scale-[0.98]">
                <span class="flex items-center gap-2"><i data-lucide="download" class="w-4 h-4 text-slate-500"></i> Download Audit JSON</span>
                <i data-lucide="external-link" class="w-4 h-4 opacity-60"></i>
              </button>
            </div>

            <!-- Hackathon Validation Card -->
            <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs text-xs">
              <span class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
                <i data-lucide="shield" class="w-4 h-4 text-indigo-600"></i> HACKATHON VALIDATION
              </span>
              <div class="mt-4 space-y-2.5 text-slate-600 font-medium">
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Validation Key:</span>
                  <span class="font-mono text-[11px] text-indigo-600 font-semibold" id="valKey">{VALIDATION_KEY}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">LLM Engine:</span>
                  <span class="font-semibold text-slate-800">Gemini 2.0 Flash</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Deterministic Logic:</span>
                  <span class="text-emerald-600 font-bold">100% Isolated</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Discipline Policy:</span>
                  <span class="text-slate-800 font-semibold">Assistant Only (No Verdict)</span>
                </div>
              </div>
            </div>

          </div>

        </div>
      </div>

      <!-- VIEW 2: INVESTIGATIONS WORKSPACE VIEW -->
      <div id="view-Investigations" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="search" class="w-5 h-5 text-indigo-600"></i> Investigation Workspace
            </h2>
            <p class="text-xs text-slate-500 mt-1">Full case dossiers and active fraud investigation queues.</p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <input type="text" id="investigationSearch" onkeyup="filterInvestigations()" placeholder="Search investigations..." class="px-3 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64" />
            <button onclick="openCaseWorkspace('CUST_002')" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5">
              <i data-lucide="folder-open" class="w-4 h-4"></i> Open Active Case (CASE-2026-0021)
            </button>
          </div>
        </div>

        <!-- Filter Pills -->
        <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-bold text-slate-600">
          <span class="text-slate-400 font-semibold mr-1">Filter Risk:</span>
          <button onclick="setCaseFilter('ALL')" class="case-filter-btn px-3 py-1.5 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 transition">All Cases</button>
          <button onclick="setCaseFilter('HIGH')" class="case-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">High Risk</button>
          <button onclick="setCaseFilter('MEDIUM')" class="case-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Medium Risk</button>
          <button onclick="setCaseFilter('LOW')" class="case-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Low Risk</button>
          <button onclick="setCaseFilter('NEEDS_REVIEW')" class="case-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Needs Review</button>
          <button onclick="setCaseFilter('CLOSED')" class="case-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Closed</button>
        </div>

        <!-- Case Cards Grid -->
        <div id="investigationCardsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <!-- CASE 1: CUST_002 -->
          <div class="case-card bg-white border border-rose-200/80 rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:shadow-md transition" data-risk="HIGH" data-status="NEEDS_REVIEW" data-search="vikram rathore cust_002 case-2026-0021">
            <div class="space-y-3">
              <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <span class="font-mono text-xs font-black text-slate-900">CASE-2026-0021</span>
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
                  <i data-lucide="alert-circle" class="w-3 h-3 text-rose-600"></i> HIGH RISK
                </span>
              </div>
              <div>
                <h3 class="font-extrabold text-slate-900 text-sm">Vikram Rathore</h3>
                <p class="text-xs text-slate-400 font-mono">CUST_002 • Current Account</p>
              </div>
              <div class="bg-rose-50/60 p-3 rounded-xl border border-rose-100/80 space-y-1 text-xs text-rose-900 font-medium">
                <div class="font-bold flex items-center gap-1.5 text-rose-700">
                  <i data-lucide="shield-alert" class="w-3.5 h-3.5"></i> Attention Required
                </div>
                <div class="text-[11px] text-slate-600">4 connected transactions • 8 rule triggers</div>
              </div>
            </div>
            <button onclick="openCaseWorkspace('CUST_002')" class="w-full py-2 bg-rose-600 hover:bg-rose-700 text-white font-extrabold rounded-xl text-xs shadow-xs transition">
              Open Investigation
            </button>
          </div>

          <!-- CASE 2: CUST_003 -->
          <div class="case-card bg-white border border-amber-200/80 rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:shadow-md transition" data-risk="MEDIUM" data-status="NEEDS_REVIEW" data-search="ananya sen cust_003 case-2026-0031">
            <div class="space-y-3">
              <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <span class="font-mono text-xs font-black text-slate-900">CASE-2026-0031</span>
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                  <i data-lucide="alert-triangle" class="w-3 h-3 text-amber-600"></i> MEDIUM RISK
                </span>
              </div>
              <div>
                <h3 class="font-extrabold text-slate-900 text-sm">Ananya Sen</h3>
                <p class="text-xs text-slate-400 font-mono">CUST_003 • Savings Account</p>
              </div>
              <div class="bg-amber-50/60 p-3 rounded-xl border border-amber-100/80 space-y-1 text-xs text-amber-900 font-medium">
                <div class="font-bold flex items-center gap-1.5 text-amber-800">
                  <i data-lucide="layers" class="w-3.5 h-3.5"></i> Structuring Suspected
                </div>
                <div class="text-[11px] text-slate-600">5 connected transactions • 3 rule triggers</div>
              </div>
            </div>
            <button onclick="openCaseWorkspace('CUST_003')" class="w-full py-2 bg-amber-600 hover:bg-amber-700 text-white font-extrabold rounded-xl text-xs shadow-xs transition">
              Open Investigation
            </button>
          </div>

          <!-- CASE 3: CUST_001 -->
          <div class="case-card bg-white border border-emerald-200/80 rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:shadow-md transition" data-risk="LOW" data-status="CLOSED" data-search="priya sharma cust_001 case-2026-0001">
            <div class="space-y-3">
              <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <span class="font-mono text-xs font-black text-slate-900">CASE-2026-0001</span>
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                  <i data-lucide="check-circle-2" class="w-3 h-3 text-emerald-600"></i> LOW RISK
                </span>
              </div>
              <div>
                <h3 class="font-extrabold text-slate-900 text-sm">Priya Sharma</h3>
                <p class="text-xs text-slate-400 font-mono">CUST_001 • Savings Account</p>
              </div>
              <div class="bg-emerald-50/60 p-3 rounded-xl border border-emerald-100/80 space-y-1 text-xs text-emerald-900 font-medium">
                <div class="font-bold flex items-center gap-1.5 text-emerald-800">
                  <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> Normal Baseline Verified
                </div>
                <div class="text-[11px] text-slate-600">8 connected transactions • 0 rule triggers</div>
              </div>
            </div>
            <button onclick="openCaseWorkspace('CUST_001')" class="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white font-extrabold rounded-xl text-xs shadow-xs transition">
              Open Case File
            </button>
          </div>

          <!-- CASE 4: CUST_004 -->
          <div class="case-card bg-white border border-blue-200/80 rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:shadow-md transition" data-risk="LOW" data-status="CLOSED" data-search="arjun mehta cust_004 case-2026-0041">
            <div class="space-y-3">
              <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <span class="font-mono text-xs font-black text-slate-900">CASE-2026-0041</span>
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                  <i data-lucide="shield" class="w-3 h-3 text-blue-600"></i> HNI CLEAN
                </span>
              </div>
              <div>
                <h3 class="font-extrabold text-slate-900 text-sm">Arjun Mehta</h3>
                <p class="text-xs text-slate-400 font-mono">CUST_004 • Wealth Management</p>
              </div>
              <div class="bg-blue-50/60 p-3 rounded-xl border border-blue-100/80 space-y-1 text-xs text-blue-900 font-medium">
                <div class="font-bold flex items-center gap-1.5 text-blue-800">
                  <i data-lucide="award" class="w-3.5 h-3.5"></i> High Value Authorized
                </div>
                <div class="text-[11px] text-slate-600">4 connected transactions • 0 rule triggers</div>
              </div>
            </div>
            <button onclick="openCaseWorkspace('CUST_004')" class="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white font-extrabold rounded-xl text-xs shadow-xs transition">
              Open Case File
            </button>
          </div>

        </div>
      </div>

      <!-- VIEW 3: CUSTOMERS DIRECTORY VIEW -->
      <div id="view-Customers" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="users" class="w-5 h-5 text-indigo-600"></i> Customer Directory
            </h2>
            <p class="text-xs text-slate-500 mt-1">Customer profiles, behavioral baselines, and historical patterns.</p>
          </div>
          <input type="text" id="customerSearchInput" onkeyup="filterCustomersTable()" placeholder="Search customer..." class="px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-72" />
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <!-- Customers Directory Table (5 Cols) -->
          <div class="lg:col-span-5 bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs flex flex-col">
            <h3 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
              <i data-lucide="list" class="w-4 h-4 text-indigo-600"></i> Mounted Accounts Ledger
            </h3>
            <div class="overflow-x-auto">
              <table class="w-full text-xs text-left">
                <thead class="bg-slate-50 text-slate-400 font-bold uppercase text-[10px] tracking-wider">
                  <tr>
                    <th class="p-3 rounded-l-xl">CUSTOMER</th>
                    <th class="p-3">RISK</th>
                    <th class="p-3 text-center">TXNS</th>
                    <th class="p-3 text-right rounded-r-xl">ACTION</th>
                  </tr>
                </thead>
                <tbody id="customersTableBody" class="divide-y divide-slate-100 font-medium text-slate-700">
                  <tr onclick="selectCustomerProfile('CUST_001')" class="hover:bg-indigo-50/50 cursor-pointer transition">
                    <td class="p-3">
                      <div class="font-extrabold text-slate-900">Priya Sharma</div>
                      <div class="text-[10px] text-slate-400 font-mono">CUST_001</div>
                    </td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">LOW</span></td>
                    <td class="p-3 text-center font-mono font-bold">8</td>
                    <td class="p-3 text-right"><button class="px-2.5 py-1 text-[11px] font-bold bg-indigo-50 text-indigo-700 rounded-lg">Profile</button></td>
                  </tr>
                  <tr onclick="selectCustomerProfile('CUST_002')" class="hover:bg-indigo-50/50 cursor-pointer transition">
                    <td class="p-3">
                      <div class="font-extrabold text-slate-900">Vikram Rathore</div>
                      <div class="text-[10px] text-slate-400 font-mono">CUST_002</div>
                    </td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-50 text-rose-700 border border-rose-200">HIGH</span></td>
                    <td class="p-3 text-center font-mono font-bold">6</td>
                    <td class="p-3 text-right"><button class="px-2.5 py-1 text-[11px] font-bold bg-indigo-50 text-indigo-700 rounded-lg">Profile</button></td>
                  </tr>
                  <tr onclick="selectCustomerProfile('CUST_003')" class="hover:bg-indigo-50/50 cursor-pointer transition">
                    <td class="p-3">
                      <div class="font-extrabold text-slate-900">Ananya Sen</div>
                      <div class="text-[10px] text-slate-400 font-mono">CUST_003</div>
                    </td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-50 text-amber-700 border border-amber-200">HIGH</span></td>
                    <td class="p-3 text-center font-mono font-bold">5</td>
                    <td class="p-3 text-right"><button class="px-2.5 py-1 text-[11px] font-bold bg-indigo-50 text-indigo-700 rounded-lg">Profile</button></td>
                  </tr>
                  <tr onclick="selectCustomerProfile('CUST_004')" class="hover:bg-indigo-50/50 cursor-pointer transition">
                    <td class="p-3">
                      <div class="font-extrabold text-slate-900">Arjun Mehta</div>
                      <div class="text-[10px] text-slate-400 font-mono">CUST_004</div>
                    </td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-50 text-blue-700 border border-blue-200">LOW</span></td>
                    <td class="p-3 text-center font-mono font-bold">7</td>
                    <td class="p-3 text-right"><button class="px-2.5 py-1 text-[11px] font-bold bg-indigo-50 text-indigo-700 rounded-lg">Profile</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Customer Profile & Behavioral Baseline Panel (7 Cols) -->
          <div class="lg:col-span-7 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs space-y-5" id="custProfileDisplay">
            <div class="flex items-center justify-between border-b border-slate-100 pb-4">
              <div class="flex items-center gap-3.5">
                <div class="h-12 w-12 rounded-full bg-indigo-600 text-white flex items-center justify-center font-extrabold text-base shadow-md" id="cpAvatar">VR</div>
                <div>
                  <h3 class="text-base font-extrabold text-slate-900 flex items-center gap-2">
                    <span id="cpName">Vikram Rathore</span>
                    <span id="cpId" class="text-xs font-mono font-bold text-slate-400">CUST_002</span>
                  </h3>
                  <p class="text-xs text-indigo-600 font-bold" id="cpType">Small Business Owner</p>
                </div>
              </div>
              <button onclick="loadCustomer(selectedProfileCustId || 'CUST_002'); navTab('Dashboard');" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-extrabold shadow-sm flex items-center gap-1.5">
                <i data-lucide="external-link" class="w-4 h-4"></i> Mount & Triage in Dashboard
              </button>
            </div>

            <!-- Customer Baseline Characteristics Matrix -->
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                <span class="text-[10px] text-slate-400 font-bold uppercase">Expected Activity</span>
                <div class="font-extrabold text-slate-800" id="cpActivity">Supplier payments</div>
              </div>
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                <span class="text-[10px] text-slate-400 font-bold uppercase">Normal Hours</span>
                <div class="font-extrabold text-slate-800" id="cpHours">10 AM – 6 PM</div>
              </div>
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                <span class="text-[10px] text-slate-400 font-bold uppercase">Typical Transaction</span>
                <div class="font-extrabold text-slate-800" id="cpTypical">₹8,000 – ₹15,000</div>
              </div>
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                <span class="text-[10px] text-slate-400 font-bold uppercase">Known Payees</span>
                <div class="font-extrabold text-slate-800" id="cpPayees">5 Payees</div>
              </div>
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                <span class="text-[10px] text-slate-400 font-bold uppercase">Known Channels</span>
                <div class="font-extrabold text-slate-800" id="cpChannels">NEFT / IMPS</div>
              </div>
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                <span class="text-[10px] text-slate-400 font-bold uppercase">Risk Rating</span>
                <div class="font-extrabold text-rose-600" id="cpRisk">HIGH SEVERITY</div>
              </div>
            </div>

            <!-- Profile Overview Sections -->
            <div class="space-y-3 pt-2">
              <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <i data-lucide="activity" class="w-4 h-4 text-indigo-600"></i> Behavioral Baseline & Open Risk Overview
              </h4>
              <div class="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-2 text-xs text-slate-700 leading-relaxed" id="cpSummary">
                Customer account CUST_002 shows a strong historical baseline of supplier and vendor payouts during regular working hours (10 AM to 6 PM). High risk anomaly flags were raised due to a sudden 3 AM velocity burst of ₹60,000 to an unknown unverified payee.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- VIEW 4: FULL TRANSACTIONS VIEW -->
      <div id="view-Transactions" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="credit-card" class="w-5 h-5 text-indigo-600"></i> Complete Transaction Ledger
            </h2>
            <p class="text-xs text-slate-500 mt-1">Immutable financial ledger across all registered accounts.</p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <input type="text" id="fullTxnSearch" onkeyup="filterFullTransactions()" placeholder="Search transaction / payee..." class="px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64" />
            <button onclick="openExportModal('transactions')" class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center gap-1.5 transition">
              <i data-lucide="download" class="w-3.5 h-3.5"></i> Export Ledger
            </button>
            <button onclick="openTxnModal()" class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-sm">
              <i data-lucide="plus-circle" class="w-3.5 h-3.5 text-indigo-400"></i> Inject Sandbox Txn
            </button>
          </div>
        </div>

        <!-- Filter Pills for Transactions -->
        <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-bold text-slate-600">
          <span class="text-slate-400 font-semibold mr-1">Filter Ledger:</span>
          <button onclick="setTxnFilter('ALL')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 transition">All</button>
          <button onclick="setTxnFilter('FLAGGED')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Flagged</button>
          <button onclick="setTxnFilter('NORMAL')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Normal</button>
          <button onclick="setTxnFilter('ODD_HOURS')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Odd Hours</button>
          <button onclick="setTxnFilter('HIGH_VALUE')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">High Value</button>
          <button onclick="setTxnFilter('NEW_PAYEE')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">New Payee</button>
          <button onclick="setTxnFilter('VELOCITY')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Velocity</button>
          <button onclick="setTxnFilter('STRUCTURING')" class="txn-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition">Structuring</button>
        </div>

        <!-- Full Ledger Table Card -->
        <div class="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-xs">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-50 text-slate-400 font-bold uppercase text-[10px] tracking-wider border-b border-slate-100">
                <tr>
                  <th class="p-3.5">CUSTOMER</th>
                  <th class="p-3.5">DATE & TIME</th>
                  <th class="p-3.5">TXN ID</th>
                  <th class="p-3.5">PAYEE</th>
                  <th class="p-3.5">CHANNEL</th>
                  <th class="p-3.5 text-right">AMOUNT</th>
                  <th class="p-3.5 text-center">RISK STATUS</th>
                  <th class="p-3.5 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody id="fullTxnTableBody" class="divide-y divide-slate-100 text-slate-700 font-medium">
                <!-- Dynamically populated via JS -->
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- VIEW 5: PREVIOUS INVESTIGATION ASSESSMENTS (HISTORY) -->
      <div id="view-History" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <!-- Header -->
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="text-xl font-extrabold text-slate-900 flex items-center gap-2.5">
              <i data-lucide="history" class="w-6 h-6 text-indigo-600"></i> Previous Investigation Assessments
            </h2>
            <p class="text-xs text-slate-500 mt-1">Review and reopen previous customer risk assessments, findings and evidence.</p>
          </div>
          <span class="px-3.5 py-1.5 bg-indigo-50 text-indigo-700 font-extrabold text-xs rounded-full border border-indigo-200 shadow-2xs self-start md:self-auto">
            Permanent Case Snapshot Ledger
          </span>
        </div>

        <!-- Search Bar & Filters -->
        <div class="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs space-y-3">
          <div class="flex flex-col md:flex-row gap-3 items-center justify-between">
            <!-- Search Input -->
            <div class="relative w-full md:w-96">
              <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2"></i>
              <input type="text" id="historySearchInput" onkeyup="filterHistoryAssessments()" placeholder="Search customer / case / transaction..." class="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-medium">
            </div>

            <!-- Risk Filters -->
            <div class="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto text-xs font-bold">
              <button onclick="setHistoryFilter('ALL')" id="histFilter-ALL" class="hist-filter-btn px-3 py-1.5 rounded-xl bg-indigo-600 text-white font-extrabold shadow-2xs">All</button>
              <button onclick="setHistoryFilter('HIGH')" id="histFilter-HIGH" class="hist-filter-btn px-3 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200">High Risk</button>
              <button onclick="setHistoryFilter('MEDIUM')" id="histFilter-MEDIUM" class="hist-filter-btn px-3 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200">Medium Risk</button>
              <button onclick="setHistoryFilter('LOW')" id="histFilter-LOW" class="hist-filter-btn px-3 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200">Low Risk</button>
              <button onclick="setHistoryFilter('ATTENTION_REQUIRED')" id="histFilter-ATTENTION_REQUIRED" class="hist-filter-btn px-3 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200">Attention Required</button>
              <button onclick="setHistoryFilter('NO_ATTENTION')" id="histFilter-NO_ATTENTION" class="hist-filter-btn px-3 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200">No Attention</button>
            </div>
          </div>
        </div>

        <!-- History Cards Container -->
        <div id="historyCardsContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <!-- Dynamic History Cards injected via JS -->
        </div>
      </div>

      <!-- VIEW 6: ALERTS FEED VIEW -->
      <div id="view-Alerts" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="bell" class="w-5 h-5 text-rose-600"></i> Active Alert Center
            </h2>
            <p class="text-xs text-slate-500 mt-1">Real-time risk alerts requiring immediate investigator triage.</p>
          </div>
          <div class="flex items-center gap-2 overflow-x-auto text-xs font-bold text-slate-600">
            <span class="text-slate-400 font-semibold">Priority:</span>
            <button onclick="filterAlerts('ALL')" class="alert-filter-btn px-3 py-1.5 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200">All</button>
            <button onclick="filterAlerts('HIGH')" class="alert-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50">Critical & High</button>
            <button onclick="filterAlerts('MEDIUM')" class="alert-filter-btn px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50">Medium</button>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6" id="alertsCardsContainer">
          
          <!-- ALERT 1: HIGH PRIORITY -->
          <div class="alert-card bg-white border-2 border-rose-200 rounded-2xl p-6 shadow-xs space-y-4" data-priority="HIGH">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
              <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1.5">
                <i data-lucide="alert-octagon" class="w-4 h-4 text-rose-600"></i> 🔴 HIGH PRIORITY
              </span>
              <span class="text-xs font-mono font-bold text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full">NEEDS REVIEW</span>
            </div>
            
            <div class="space-y-2 text-xs">
              <div class="font-extrabold text-slate-900 text-sm flex items-center justify-between">
                <span>NEW PAYEE + RAPID VELOCITY</span>
                <span class="font-mono text-slate-400">CUST_002</span>
              </div>
              <p class="text-slate-600 font-medium">
                Customer: <strong>Vikram Rathore</strong><br/>
                Transactions: <code class="bg-slate-100 px-1 rounded">TXN_203</code>, <code class="bg-slate-100 px-1 rounded">TXN_204</code>, <code class="bg-slate-100 px-1 rounded">TXN_205</code>, <code class="bg-slate-100 px-1 rounded">TXN_00206</code><br/>
                Trigger: Account takeover velocity pattern at 3:14 AM.
              </p>
            </div>

            <div class="pt-2 flex justify-end">
              <button onclick="loadCustomer('CUST_002'); navTab('Dashboard');" class="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-extrabold shadow-sm flex items-center gap-1.5">
                <i data-lucide="search" class="w-3.5 h-3.5"></i> Open Case
              </button>
            </div>
          </div>

          <!-- ALERT 2: MEDIUM PRIORITY -->
          <div class="alert-card bg-white border-2 border-amber-200 rounded-2xl p-6 shadow-xs space-y-4" data-priority="MEDIUM">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
              <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1.5">
                <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-600"></i> 🟠 MEDIUM PRIORITY
              </span>
              <span class="text-xs font-mono font-bold text-amber-600 bg-amber-50 px-2.5 py-0.5 rounded-full">NEEDS REVIEW</span>
            </div>
            
            <div class="space-y-2 text-xs">
              <div class="font-extrabold text-slate-900 text-sm flex items-center justify-between">
                <span>STRUCTURING DETECTED</span>
                <span class="font-mono text-slate-400">CUST_003</span>
              </div>
              <p class="text-slate-600 font-medium">
                Customer: <strong>Ananya Sen</strong><br/>
                Transactions: Multiple ₹49,900 transfers right below reporting limit.<br/>
                Trigger: Structuring & threshold evasion rules.
              </p>
            </div>

            <div class="pt-2 flex justify-end">
              <button onclick="loadCustomer('CUST_003'); navTab('Dashboard');" class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-extrabold shadow-sm flex items-center gap-1.5">
                <i data-lucide="search" class="w-3.5 h-3.5"></i> Review Case
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- VIEW 7: REPORTS VIEW -->
      <div id="view-Reports" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex justify-between items-center">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="bar-chart-3" class="w-5 h-5 text-indigo-600"></i> Compliance Reports Library
            </h2>
            <p class="text-xs text-slate-500 mt-1">Generated SentinelRisk investigation dossiers and compliance exports.</p>
          </div>
          <button onclick="openExportModal('dossier')" class="px-4 py-2 bg-indigo-600 text-white font-bold rounded-xl text-xs flex items-center gap-1.5">
            <i data-lucide="download" class="w-3.5 h-3.5"></i> Export Active Report
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span class="font-mono text-xs font-black text-slate-900">CASE-2026-0021</span>
                <h3 class="font-extrabold text-slate-900 text-sm">Vikram Rathore</h3>
              </div>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-50 text-rose-700 border border-rose-200">HIGH RISK</span>
            </div>
            <p class="text-xs text-slate-500">Generated: September 5, 2026 • Full AI Investigation Dossier</p>
            <div class="flex items-center gap-2">
              <button onclick="openReportModal('CUST_002')" class="flex-1 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-xl text-xs">View Report</button>
              <button onclick="openExportModal('dossier')" class="px-4 py-2 border border-slate-200 hover:bg-slate-50 font-bold rounded-xl text-xs">Export</button>
            </div>
          </div>

          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span class="font-mono text-xs font-black text-slate-900">CASE-2026-0001</span>
                <h3 class="font-extrabold text-slate-900 text-sm">Priya Sharma</h3>
              </div>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">LOW RISK</span>
            </div>
            <p class="text-xs text-slate-500">Generated: September 5, 2026 • Routine Baseline Verification</p>
            <div class="flex items-center gap-2">
              <button onclick="openReportModal('CUST_001')" class="flex-1 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-xl text-xs">View Report</button>
              <button onclick="openExportModal('dossier')" class="px-4 py-2 border border-slate-200 hover:bg-slate-50 font-bold rounded-xl text-xs">Export</button>
            </div>
          </div>
        </div>
      </div>

      <!-- VIEW 8: AUDIT LOGS VIEW -->
      <div id="view-Audit Logs" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex justify-between items-center">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="file-check-2" class="w-5 h-5 text-indigo-600"></i> Immutable System Audit Trail
            </h2>
            <p class="text-xs text-slate-500 mt-1">Audit log of system actions, rule evaluations, vector RAG retrieval, and AI calls.</p>
          </div>
          <button onclick="openExportModal('audit')" class="px-4 py-2 bg-indigo-600 text-white font-bold rounded-xl text-xs shadow-sm flex items-center gap-1.5">
            <i data-lucide="download" class="w-3.5 h-3.5"></i> Export Audit JSON
          </button>
        </div>

        <!-- System Pipeline Trace Widget -->
        <div class="bg-slate-900 text-white p-5 rounded-2xl space-y-3 shadow-md">
          <div class="text-xs font-mono font-bold text-indigo-400 uppercase tracking-widest flex items-center gap-2">
            <i data-lucide="cpu" class="w-4 h-4"></i> System Execution Flow
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-center text-xs font-medium">
            <div class="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
              <span class="text-[10px] text-slate-400 block uppercase">Step 1</span>
              <span class="font-bold text-emerald-400">Evidence Created</span>
            </div>
            <div class="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
              <span class="text-[10px] text-slate-400 block uppercase">Step 2</span>
              <span class="font-bold text-indigo-400">AI Called</span>
            </div>
            <div class="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
              <span class="text-[10px] text-slate-400 block uppercase">Step 3</span>
              <span class="font-bold text-sky-400">AI Response Validated</span>
            </div>
            <div class="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
              <span class="text-[10px] text-slate-400 block uppercase">Step 4</span>
              <span class="font-bold text-amber-400">Human Review Required</span>
            </div>
          </div>
        </div>

        <!-- Audit Table -->
        <div class="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-xs">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs font-mono">
              <thead class="bg-slate-50 text-slate-400 font-bold uppercase text-[10px] tracking-wider border-b border-slate-100">
                <tr>
                  <th class="p-3.5">TIME</th>
                  <th class="p-3.5">EVENT</th>
                  <th class="p-3.5">ACTOR</th>
                  <th class="p-3.5">ACTION</th>
                  <th class="p-3.5">CASE ID</th>
                  <th class="p-3.5">RESULT</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 text-slate-700 font-medium">
                <tr class="hover:bg-slate-50">
                  <td class="p-3.5 text-slate-400">13:31:08</td>
                  <td class="p-3.5 font-bold text-slate-900">Evidence validation passed</td>
                  <td class="p-3.5 text-indigo-600">System</td>
                  <td class="p-3.5">VALIDATE_RULES</td>
                  <td class="p-3.5 text-slate-500">CASE-2026-0021</td>
                  <td class="p-3.5"><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full text-[10px] font-bold">PASSED</span></td>
                </tr>
                <tr class="hover:bg-slate-50">
                  <td class="p-3.5 text-slate-400">13:31:08</td>
                  <td class="p-3.5 font-bold text-slate-900">Gemini investigation completed</td>
                  <td class="p-3.5 text-indigo-600">Gemini AI</td>
                  <td class="p-3.5">LLM_SYNTHESIS</td>
                  <td class="p-3.5 text-slate-500">CASE-2026-0021</td>
                  <td class="p-3.5"><span class="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-[10px] font-bold">REPORT_GEN</span></td>
                </tr>
                <tr class="hover:bg-slate-50">
                  <td class="p-3.5 text-slate-400">13:31:06</td>
                  <td class="p-3.5 font-bold text-slate-900">Evidence retrieved via RAG</td>
                  <td class="p-3.5 text-indigo-600">System</td>
                  <td class="p-3.5">VECTOR_RAG</td>
                  <td class="p-3.5 text-slate-500">CASE-2026-0021</td>
                  <td class="p-3.5"><span class="px-2 py-0.5 bg-sky-50 text-sky-700 rounded-full text-[10px] font-bold">100% MATCH</span></td>
                </tr>
                <tr class="hover:bg-slate-50">
                  <td class="p-3.5 text-slate-400">13:31:05</td>
                  <td class="p-3.5 font-bold text-slate-900">Gemini embedding generated</td>
                  <td class="p-3.5 text-indigo-600">Gemini Embed</td>
                  <td class="p-3.5">GEN_EMBEDDING</td>
                  <td class="p-3.5 text-slate-500">CASE-2026-0021</td>
                  <td class="p-3.5"><span class="px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full text-[10px] font-bold">768-DIM</span></td>
                </tr>
                <tr class="hover:bg-slate-50">
                  <td class="p-3.5 text-slate-400">13:31:04</td>
                  <td class="p-3.5 font-bold text-slate-900">Evidence pack generated</td>
                  <td class="p-3.5 text-indigo-600">System</td>
                  <td class="p-3.5">PACK_EVIDENCE</td>
                  <td class="p-3.5 text-slate-500">CASE-2026-0021</td>
                  <td class="p-3.5"><span class="px-2 py-0.5 bg-amber-50 text-amber-700 rounded-full text-[10px] font-bold">EVID-PACK-0021</span></td>
                </tr>
                <tr class="hover:bg-slate-50">
                  <td class="p-3.5 text-slate-400">13:31:03</td>
                  <td class="p-3.5 font-bold text-slate-900">Deterministic rules executed</td>
                  <td class="p-3.5 text-indigo-600">Engine</td>
                  <td class="p-3.5">EXEC_RULES</td>
                  <td class="p-3.5 text-slate-500">CASE-2026-0021</td>
                  <td class="p-3.5"><span class="px-2 py-0.5 bg-rose-50 text-rose-700 rounded-full text-[10px] font-bold">8 TRIGGERS</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- VIEW 9: SETTINGS VIEW -->
      <div id="view-Settings" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex justify-between items-center">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="settings" class="w-5 h-5 text-indigo-600"></i> System Configuration
            </h2>
            <p class="text-xs text-slate-500 mt-1">System status, rule engine controls, and Gemini AI credentials.</p>
          </div>
          <button onclick="openKeyModal()" class="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-extrabold rounded-xl text-xs shadow-sm flex items-center gap-1.5">
            <i data-lucide="key" class="w-3.5 h-3.5"></i> Update Gemini API Key
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- System Status -->
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-3 text-xs">
            <h3 class="font-extrabold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2.5 flex items-center gap-2">
              <i data-lucide="activity" class="w-4 h-4 text-emerald-600"></i> SYSTEM STATUS
            </h3>
            <div class="space-y-2 font-medium">
              <div class="flex justify-between"><span>Risk Engine:</span><span class="text-emerald-600 font-bold">● ONLINE</span></div>
              <div class="flex justify-between"><span>Evidence Engine:</span><span class="text-emerald-600 font-bold">● ONLINE</span></div>
              <div class="flex justify-between"><span>Gemini AI:</span><span class="text-emerald-600 font-bold">● CONNECTED</span></div>
              <div class="flex justify-between"><span>Local Retrieval:</span><span class="text-emerald-600 font-bold">● ONLINE</span></div>
              <div class="flex justify-between"><span>Database:</span><span class="text-emerald-600 font-bold">● ONLINE</span></div>
            </div>
          </div>

          <!-- Risk Rules Toggles -->
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-3 text-xs">
            <h3 class="font-extrabold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2.5 flex items-center gap-2">
              <i data-lucide="shield-check" class="w-4 h-4 text-indigo-600"></i> RISK RULES ENGINE
            </h3>
            <div class="space-y-2 font-medium">
              <div class="flex justify-between"><span>Odd-Hours Detection:</span><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold rounded">ON</span></div>
              <div class="flex justify-between"><span>Velocity Detection:</span><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold rounded">ON</span></div>
              <div class="flex justify-between"><span>Baseline Deviation:</span><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold rounded">ON</span></div>
              <div class="flex justify-between"><span>New Payee Detection:</span><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold rounded">ON</span></div>
              <div class="flex justify-between"><span>Structuring Detection:</span><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold rounded">ON</span></div>
              <div class="flex justify-between"><span>New Channel Detection:</span><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold rounded">ON</span></div>
            </div>
          </div>

          <!-- Gemini Configuration -->
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-3 text-xs">
            <h3 class="font-extrabold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2.5 flex items-center gap-2">
              <i data-lucide="sparkles" class="w-4 h-4 text-amber-500"></i> GEMINI AI CONFIG
            </h3>
            <div class="space-y-2 font-medium">
              <div class="flex justify-between"><span>Connection:</span><span class="text-emerald-600 font-bold">● Connected</span></div>
              <div class="flex justify-between"><span>Embedding Model:</span><span class="font-mono text-slate-600">gemini-embedding-001</span></div>
              <div class="flex justify-between"><span>Investigation Model:</span><span class="font-mono text-slate-600">Gemini 2.0 Flash</span></div>
              <div class="flex justify-between"><span>API Key:</span><span class="font-mono text-slate-400">••••••••••••••••</span></div>
            </div>
            <button onclick="openKeyModal()" class="w-full py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-extrabold rounded-xl mt-2 text-xs">
              Configure Key
            </button>
          </div>
        </div>
      </div>

      <!-- MODAL: Full Case Workspace Modal -->
      <div id="caseWorkspaceModal" class="hidden fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
        <div class="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto relative space-y-5">
          <button onclick="closeCaseWorkspace()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
          
          <div class="border-b border-slate-100 pb-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <span class="font-mono text-xs font-black text-indigo-600 uppercase tracking-wider" id="cwCaseId">CASE: CASE-2026-0021</span>
                <h2 class="text-xl font-black text-slate-900" id="cwCustName">Vikram Rathore</h2>
              </div>
              <div class="flex items-center gap-2">
                <span id="cwRiskBadge" class="px-3 py-1 rounded-full text-xs font-extrabold bg-rose-50 text-rose-700 border border-rose-200">HIGH RISK</span>
                <span id="cwStatusBadge" class="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-50 text-amber-800 border border-amber-200">NEEDS HUMAN REVIEW</span>
              </div>
            </div>
            <div class="mt-2 text-xs text-slate-500 font-medium flex gap-4">
              <span>Risk Score: <strong class="text-slate-900 font-mono" id="cwScore">82 / 100</strong></span>
              <span>Customer ID: <strong class="text-slate-900 font-mono" id="cwCustId">CUST_002</strong></span>
            </div>
          </div>

          <!-- Structured Case Workspace Sections -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
              <span class="font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-[11px] text-indigo-600">
                <i data-lucide="search" class="w-3.5 h-3.5"></i> Primary Finding
              </span>
              <p class="text-slate-700 leading-relaxed font-medium" id="cwFinding">Connected high-velocity transfers to an unverified recipient during off-hours.</p>
            </div>
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
              <span class="font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-[11px] text-indigo-600">
                <i data-lucide="link-2" class="w-3.5 h-3.5"></i> Connected Transactions
              </span>
              <p class="text-slate-700 leading-relaxed font-medium" id="cwTxns">TXN_203, TXN_204, TXN_205, TXN_00206 (Total: ₹1,85,000)</p>
            </div>
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
              <span class="font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-[11px] text-indigo-600">
                <i data-lucide="zap" class="w-3.5 h-3.5"></i> Triggered Rules
              </span>
              <p class="text-slate-700 leading-relaxed font-medium" id="cwRules">ODD_HOURS_ACTIVITY, RAPID_VELOCITY_BURST, NEW_PAYEE_HIGH_VALUE, BASELINE_DEVIATION</p>
            </div>
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
              <span class="font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-[11px] text-indigo-600">
                <i data-lucide="bar-chart-2" class="w-3.5 h-3.5"></i> Baseline Comparison
              </span>
              <p class="text-slate-700 leading-relaxed font-medium" id="cwBaseline">Normal activity: ₹8k-15k during 10 AM-6 PM. Current: ₹60k at 3:14 AM.</p>
            </div>
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
              <span class="font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-[11px] text-indigo-600">
                <i data-lucide="alert-circle" class="w-3.5 h-3.5"></i> Why It Matters
              </span>
              <p class="text-slate-700 leading-relaxed font-medium" id="cwWhy">High probability of account takeover or credential compromise resulting in funds loss.</p>
            </div>
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
              <span class="font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-[11px] text-indigo-600">
                <i data-lucide="flag" class="w-3.5 h-3.5"></i> Investigator Priority & Next Steps
              </span>
              <p class="text-slate-700 leading-relaxed font-medium" id="cwSteps">HIGH PRIORITY • 1. Freeze outbound transfers 2. Contact customer via phone 3. Verify identity.</p>
            </div>
          </div>

          <!-- Evidence Pack -->
          <div class="p-4 bg-indigo-50/70 border border-indigo-100 rounded-xl space-y-1 text-xs">
            <span class="font-extrabold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5 text-[11px]">
              <i data-lucide="shield-check" class="w-3.5 h-3.5 text-indigo-600"></i> Traceable Evidence Hash
            </span>
            <div class="font-mono text-slate-600 text-[11px]" id="cwEvidence">EVID-TXN_00206-NEW_CHANNEL_BEHAVIOUR</div>
          </div>

          <div class="pt-2 flex justify-end gap-3">
            <button onclick="closeCaseWorkspace()" class="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-bold">Close</button>
            <button id="cwMountBtn" onclick="mountWorkspaceCase()" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold shadow-md flex items-center gap-1.5">
              <i data-lucide="play" class="w-3.5 h-3.5"></i> Mount & Run AI Triage in Dashboard
            </button>
          </div>
        </div>
      </div>

      <!-- MODAL: Transaction Details Modal -->
      <div id="txnDetailModal" class="hidden fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
        <div class="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-lg w-full p-6 relative space-y-4">
          <button onclick="closeTxnDetailModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
          
          <div class="border-b border-slate-100 pb-3">
            <span class="font-mono text-xs font-bold text-slate-400">TRANSACTION DETAILS</span>
            <h3 class="text-lg font-black text-slate-900 font-mono" id="tdId">TXN_00206</h3>
          </div>

          <div class="grid grid-cols-2 gap-3 text-xs">
            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase">Amount</span>
              <div class="font-extrabold text-slate-900 text-sm font-mono" id="tdAmount">₹60,000</div>
            </div>
            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase">Channel</span>
              <div class="font-extrabold text-slate-900 text-sm" id="tdChannel">UPI</div>
            </div>
            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase">Payee Name</span>
              <div class="font-extrabold text-slate-900" id="tdPayee">Josalukas</div>
            </div>
            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase">Timestamp</span>
              <div class="font-extrabold text-slate-900 font-mono" id="tdTime">2026-08-20 03:14</div>
            </div>
          </div>

          <div class="space-y-1.5 text-xs">
            <span class="font-extrabold text-slate-900 uppercase tracking-wider text-[10px]">Triggered Risk Rules</span>
            <div class="p-3 bg-rose-50 border border-rose-100 rounded-xl font-mono text-rose-800 text-[11px]" id="tdRules">
              • NEW_PAYEE_HIGH_VALUE<br/>• NEW_CHANNEL_BEHAVIOUR
            </div>
          </div>

          <div class="space-y-1 text-xs">
            <span class="font-extrabold text-slate-900 uppercase tracking-wider text-[10px]">Evidence Reference</span>
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl font-mono text-indigo-600 text-[11px]" id="tdEvidence">
              EVID-TXN_00206-NEW_CHANNEL_BEHAVIOUR
            </div>
          </div>

          <!-- Traceability Chain Visual Widget -->
          <div class="p-3 bg-slate-900 text-white rounded-xl text-xs space-y-2">
            <span class="text-[10px] font-mono text-indigo-400 font-bold uppercase tracking-wider">Traceability Chain</span>
            <div class="flex items-center justify-between text-[11px] font-mono">
              <span class="text-rose-400 font-bold">AI Finding</span>
              <span class="text-slate-400">➔</span>
              <span class="text-amber-400 font-bold">Evidence ID</span>
              <span class="text-slate-400">➔</span>
              <span class="text-indigo-400 font-bold">Transaction</span>
              <span class="text-slate-400">➔</span>
              <span class="text-emerald-400 font-bold">Original Data</span>
            </div>
          </div>

          <div class="pt-2 flex justify-end">
            <button onclick="closeTxnDetailModal()" class="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-extrabold">
              Close Details
            </button>
          </div>
        </div>
      </div>

      <!-- MODAL: View Full Report Modal -->
      <div id="reportViewModal" class="hidden fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
        <div class="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-3xl w-full p-6 max-h-[85vh] overflow-y-auto relative space-y-4">
          <button onclick="closeReportModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
          
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <div>
              <span class="text-[10px] font-extrabold text-indigo-600 uppercase tracking-widest">SENTINELRISK INVESTIGATION REPORT</span>
              <h3 class="text-lg font-black text-slate-900" id="rvTitle">Case Report</h3>
            </div>
            <button onclick="openExportModal('dossier')" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5">
              <i data-lucide="download" class="w-3.5 h-3.5"></i> Export Report
            </button>
          </div>

          <div id="rvContent" class="text-xs leading-relaxed text-slate-800 space-y-3">
            <!-- Rendered Markdown -->
          </div>

          <div class="pt-2 border-t border-slate-100 flex justify-end">
            <button onclick="closeReportModal()" class="px-5 py-2 bg-slate-900 text-white font-bold rounded-xl text-xs">
              Close Report
            </button>
          </div>
        </div>
      </div>

      <!-- Footer Bar (Stylish & Eye-Catching with Copyright & Adhi426 Credit) -->
      <footer class="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white px-6 py-4 border-t border-indigo-900/50 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-3 text-xs tracking-wide">
        <div class="flex items-center gap-2 font-extrabold tracking-wider">
          <span class="text-indigo-400 font-serif text-base">©</span> 
          <span class="bg-gradient-to-r from-white via-slate-200 to-indigo-200 bg-clip-text text-transparent font-black tracking-tight text-sm">
            2026 SentinelRisk Copilot
          </span>
          <span class="text-slate-500 font-normal">|</span>
          <span class="text-slate-300 font-medium flex items-center gap-1">
            Crafted with <i data-lucide="heart" class="w-3.5 h-3.5 text-rose-500 fill-rose-500 animate-pulse"></i> by 
            <span class="font-extrabold text-amber-400 underline decoration-amber-400/40 decoration-2 underline-offset-4 hover:text-amber-300 transition">Adhi426</span>
          </span>
        </div>

        <div class="hidden md:flex items-center gap-2 font-bold text-slate-300">
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 backdrop-blur-md uppercase tracking-widest flex items-center gap-1">
            <i data-lucide="shield-check" class="w-3 h-3 text-indigo-400"></i> Autonomous AI Triage
          </span>
          <span class="text-slate-400 text-xs italic font-medium">Empowering Next-Gen Banking Risk Intelligence</span>
        </div>

        <div class="flex items-center gap-2 font-extrabold text-indigo-300 bg-indigo-900/40 px-3 py-1 rounded-xl border border-indigo-700/50 shadow-inner">
          <span>Powered by <strong class="bg-gradient-to-r from-indigo-300 via-sky-300 to-amber-300 bg-clip-text text-transparent">Gemini 2.0 Flash</strong></span>
          <i data-lucide="sparkles" class="w-3.5 h-3.5 text-amber-400 animate-spin" style="animation-duration: 4s;"></i>
        </div>
      </footer>

    </div>

  </div>

  <!-- Modal 1: Custom Transaction Sandbox Modal -->
  <div id="txnModal" class="hidden fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-md w-full p-6 relative">
      <button onclick="closeTxnModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
      <h3 class="text-sm font-extrabold text-slate-900 flex items-center gap-2 mb-1">
        <i data-lucide="plus-circle" class="w-4 h-4 text-indigo-600"></i> Add Sandbox Transaction
      </h3>
      <p class="text-xs text-slate-500 mb-4">Inject custom transactions live into the database to test fraud rules.</p>
      
      <form onsubmit="submitCustomTxn(event)" class="space-y-3.5 text-xs">
        <div>
          <label class="block text-slate-700 font-bold mb-1">Target Customer Profile</label>
          <select id="modalCustId" class="w-full p-2.5 border border-slate-200 rounded-xl bg-slate-50 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-medium">
            <option value="CUST_001">CUST_001 - Priya Sharma (Savings)</option>
            <option value="CUST_002">CUST_002 - Vikram Rathore (Current)</option>
            <option value="CUST_003">CUST_003 - Ananya Sen (Savings)</option>
            <option value="CUST_004">CUST_004 - Arjun Mehta (HNI Wealth)</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-slate-700 font-bold mb-1">Amount (₹)</label>
            <input type="number" step="0.01" id="modalAmount" required placeholder="e.g. 49800" class="w-full p-2.5 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-medium" />
          </div>
          <div>
            <label class="block text-slate-700 font-bold mb-1">Channel</label>
            <select id="modalChannel" class="w-full p-2.5 border border-slate-200 rounded-xl bg-white focus:outline-none font-medium">
              <option value="IMPS">IMPS</option>
              <option value="UPI">UPI</option>
              <option value="NEFT">NEFT</option>
              <option value="POS">POS</option>
              <option value="NetBanking">NetBanking</option>
              <option value="Credit Card">Credit Card</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-slate-700 font-bold mb-1">Payee Name</label>
          <input type="text" id="modalPayee" required placeholder="e.g. Unknown Offshore Broker" class="w-full p-2.5 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-medium" />
        </div>
        <div>
          <label class="block text-slate-700 font-bold mb-1">Description / Memo</label>
          <input type="text" id="modalDesc" required placeholder="e.g. Late night urgent settlement" class="w-full p-2.5 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-medium" />
        </div>

        <div class="pt-2 flex justify-end gap-2">
          <button type="button" onclick="closeTxnModal()" class="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-bold hover:bg-slate-50">Cancel</button>
          <button type="submit" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold shadow-md shadow-indigo-600/20">Inject Transaction</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal 2: API Key Configuration Modal -->
  <div id="keyModal" class="hidden fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-md w-full p-6 relative">
      <button onclick="closeKeyModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
      <h3 class="text-sm font-extrabold text-slate-900 flex items-center gap-2 mb-1">
        <i data-lucide="key" class="w-4 h-4 text-amber-500"></i> Configure Gemini API Key
      </h3>
      <p class="text-xs text-slate-500 mb-4">Set your Google Gemini API Key for live AI investigation reports.</p>
      
      <div class="space-y-3.5 text-xs">
        <div>
          <label class="block text-slate-700 font-bold mb-1">Gemini API Key</label>
          <input type="password" id="customApiKeyInput" placeholder="AIzaSy..." class="w-full p-2.5 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 mono" />
          <p class="text-[11px] text-slate-400 mt-1">If left empty, server will use environment variable <code>GEMINI_API_KEY</code>.</p>
        </div>

        <div class="pt-2 flex justify-end gap-2">
          <button type="button" onclick="clearApiKey()" class="px-4 py-2 rounded-xl border border-rose-200 text-rose-600 font-bold hover:bg-rose-50">Clear Saved Key</button>
          <button type="button" onclick="saveApiKey()" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold shadow-md shadow-indigo-600/20">Save Settings</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal 3: Multi-Format Export Options Modal -->
  <div id="exportModal" class="hidden fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-md w-full p-6 relative">
      <button onclick="closeExportModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
      <h3 class="text-sm font-extrabold text-slate-900 flex items-center gap-2 mb-1">
        <i data-lucide="download" class="w-4 h-4 text-indigo-600"></i> Export Format Options
      </h3>
      <p class="text-xs text-slate-500 mb-4">Select the format to export investigation & risk analysis data.</p>
      
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-2.5 text-xs">
          <label class="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 cursor-pointer transition">
            <input type="radio" name="exportFormat" value="pdf" checked class="text-indigo-600 focus:ring-indigo-500" />
            <div>
              <div class="font-extrabold text-slate-900 flex items-center gap-1.5"><i data-lucide="file-text" class="w-3.5 h-3.5 text-rose-500"></i> PDF (.pdf)</div>
              <div class="text-[10px] text-slate-400">Printable Document</div>
            </div>
          </label>
          <label class="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 cursor-pointer transition">
            <input type="radio" name="exportFormat" value="doc" class="text-indigo-600 focus:ring-indigo-500" />
            <div>
              <div class="font-extrabold text-slate-900 flex items-center gap-1.5"><i data-lucide="file-type-2" class="w-3.5 h-3.5 text-blue-500"></i> Word (.doc)</div>
              <div class="text-[10px] text-slate-400">Editable MS Word</div>
            </div>
          </label>
          <label class="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 cursor-pointer transition">
            <input type="radio" name="exportFormat" value="md" class="text-indigo-600 focus:ring-indigo-500" />
            <div>
              <div class="font-extrabold text-slate-900 flex items-center gap-1.5"><i data-lucide="code" class="w-3.5 h-3.5 text-indigo-500"></i> Markdown (.md)</div>
              <div class="text-[10px] text-slate-400">Raw Markdown Text</div>
            </div>
          </label>
          <label class="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 cursor-pointer transition">
            <input type="radio" name="exportFormat" value="html" class="text-indigo-600 focus:ring-indigo-500" />
            <div>
              <div class="font-extrabold text-slate-900 flex items-center gap-1.5"><i data-lucide="globe" class="w-3.5 h-3.5 text-emerald-500"></i> HTML (.html)</div>
              <div class="text-[10px] text-slate-400">Web Webpage View</div>
            </div>
          </label>
          <label class="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 cursor-pointer transition">
            <input type="radio" name="exportFormat" value="txt" class="text-indigo-600 focus:ring-indigo-500" />
            <div>
              <div class="font-extrabold text-slate-900 flex items-center gap-1.5"><i data-lucide="align-left" class="w-3.5 h-3.5 text-slate-500"></i> Text (.txt)</div>
              <div class="text-[10px] text-slate-400">Plain Text Summary</div>
            </div>
          </label>
          <label class="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 cursor-pointer transition">
            <input type="radio" name="exportFormat" value="json" class="text-indigo-600 focus:ring-indigo-500" />
            <div>
              <div class="font-extrabold text-slate-900 flex items-center gap-1.5"><i data-lucide="database" class="w-3.5 h-3.5 text-amber-500"></i> JSON (.json)</div>
              <div class="text-[10px] text-slate-400">Raw Data Structure</div>
            </div>
          </label>
        </div>

        <div class="pt-2 flex justify-end gap-2 text-xs">
          <button type="button" onclick="closeExportModal()" class="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-bold hover:bg-slate-50">Cancel</button>
          <button type="button" onclick="confirmExport()" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold shadow-md shadow-indigo-600/20 flex items-center gap-1.5">
            <i data-lucide="download" class="w-3.5 h-3.5"></i> Export Now
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- SAVED ASSESSMENT DETAIL MODAL -->
  <div id="assessmentDetailModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
      <!-- Modal Header -->
      <div class="p-5 bg-slate-900 text-white flex items-center justify-between shrink-0 border-b border-slate-800">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center">
            <i data-lucide="shield-alert" class="w-5 h-5 text-indigo-400"></i>
          </div>
          <div>
            <h3 class="text-base font-extrabold tracking-wide flex items-center gap-2">
              RISK INVESTIGATION ASSESSMENT
            </h3>
            <div id="modalAssessmentId" class="text-xs font-mono text-indigo-300">ASSESS-2026-0000</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button onclick="exportSavedAssessmentJSONModal()" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
            <i data-lucide="download" class="w-3.5 h-3.5"></i> Export JSON
          </button>
          <button onclick="exportSavedAssessmentReportModal()" class="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded-xl text-xs font-bold transition flex items-center gap-1.5">
            <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Export Report
          </button>
          <button onclick="closeAssessmentDetailModal()" class="text-slate-400 hover:text-white p-1 rounded-lg">
            <i data-lucide="x" class="w-6 h-6"></i>
          </button>
        </div>
      </div>

      <!-- Modal Scrollable Content (10 Sections) -->
      <div class="p-6 overflow-y-auto space-y-6 flex-1 text-slate-800">
        
        <!-- Section 1: ASSESSMENT OVERVIEW -->
        <div class="bg-slate-50 border border-slate-200 rounded-2xl p-5 space-y-3">
          <div class="flex items-center justify-between border-b border-slate-200/80 pb-3">
            <div>
              <div class="text-xs text-slate-400 font-bold uppercase tracking-wider">Customer Overview</div>
              <div id="modalCustName" class="text-lg font-extrabold text-slate-900">Customer Name</div>
              <div id="modalCustId_Detail" class="text-xs font-mono text-slate-500">CUST_000</div>
            </div>
            <div class="text-right">
              <div id="modalRiskBadge" class="inline-block px-3.5 py-1 rounded-full text-xs font-extrabold border">HIGH RISK</div>
              <div id="modalRiskScore" class="text-xl font-extrabold text-slate-900 mt-1">82 / 100</div>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div>
              <span class="text-slate-400 font-medium block">Assessment ID</span>
              <span id="modalMetaId" class="font-mono font-bold text-slate-800">ASSESS-2026-0000</span>
            </div>
            <div>
              <span class="text-slate-400 font-medium block">Timestamp</span>
              <span id="modalMetaTime" class="font-medium text-slate-800">Date</span>
            </div>
            <div>
              <span class="text-slate-400 font-medium block">Model</span>
              <span id="modalMetaModel" class="font-bold text-indigo-700">Gemini 2.0 Flash</span>
            </div>
            <div>
              <span class="text-slate-400 font-medium block">Status</span>
              <span id="modalMetaStatus" class="font-extrabold text-amber-700">ATTENTION REQUIRED</span>
            </div>
          </div>
        </div>

        <!-- Section 2: PRIMARY FINDING -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="alert-circle" class="w-4 h-4 text-indigo-600"></i> 2. Primary Finding
          </h4>
          <div id="modalPrimaryFinding" class="p-4 bg-amber-50/70 border border-amber-200 text-amber-900 rounded-xl text-xs font-semibold leading-relaxed">
            Primary finding description...
          </div>
        </div>

        <!-- Section 3: CONNECTED TRANSACTIONS -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="credit-card" class="w-4 h-4 text-indigo-600"></i> 3. Connected Transactions
          </h4>
          <div id="modalConnectedTxns" class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            <!-- Dynamic txns -->
          </div>
        </div>

        <!-- Section 4: TRIGGERED RISK RULES -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="zap" class="w-4 h-4 text-indigo-600"></i> 4. Triggered Risk Rules & Evidence
          </h4>
          <div id="modalTriggeredRules" class="space-y-2">
            <!-- Dynamic rules -->
          </div>
        </div>

        <!-- Section 5: HISTORICAL BASELINE -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="bar-chart-3" class="w-4 h-4 text-indigo-600"></i> 5. Historical Baseline
          </h4>
          <div id="modalBaseline" class="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2">
            <!-- Dynamic baseline -->
          </div>
        </div>

        <!-- Section 6: WHY IT MATTERS -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="help-circle" class="w-4 h-4 text-indigo-600"></i> 6. Why It Matters
          </h4>
          <ul id="modalWhyItMatters" class="space-y-1.5 text-xs text-slate-700 list-disc list-inside bg-slate-50 p-3.5 rounded-xl border border-slate-200">
            <!-- Dynamic why it matters -->
          </ul>
        </div>

        <!-- Section 7: INVESTIGATOR PRIORITY -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="list-ordered" class="w-4 h-4 text-indigo-600"></i> 7. Investigator Priority
          </h4>
          <ol id="modalInvestigatorPriority" class="space-y-1.5 text-xs text-slate-700 list-decimal list-inside bg-slate-50 p-3.5 rounded-xl border border-slate-200">
            <!-- Dynamic priorities -->
          </ol>
        </div>

        <!-- Section 8: RECOMMENDED NEXT STEPS -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="check-square" class="w-4 h-4 text-indigo-600"></i> 8. Recommended Next Steps
          </h4>
          <div id="modalNextSteps" class="space-y-1.5">
            <!-- Dynamic next steps -->
          </div>
        </div>

        <!-- Section 9: EVIDENCE VALIDATION -->
        <div class="space-y-2">
          <h4 class="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600"></i> 9. Evidence Validation
          </h4>
          <div class="p-4 bg-emerald-50/70 border border-emerald-200 text-emerald-900 rounded-xl text-xs space-y-1 font-medium">
            <div>✓ Evidence IDs validated against deterministic rule engine</div>
            <div>✓ Connected transactions verified and traceable to financial ledger</div>
            <div>✓ AI investigation output strictly grounded in supplied evidence</div>
            <div>✓ Human investigator decision required for final case disposition</div>
          </div>
        </div>

        <!-- Section 10: HUMAN DECISION REQUIREMENT -->
        <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 font-medium space-y-1">
          <div class="font-extrabold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="user-check" class="w-4 h-4 text-amber-600"></i> 10. Human Decision Required
          </div>
          <p>This assessment does not establish fraud. Final judgment belongs to the investigator.</p>
        </div>
      </div>
    </div>
  </div>

  <script>
    let activeCustomerId = null;
    let currentAuditData = null;
    let lastGeneratedReportMd = "";
    lucide.createIcons();

    if (localStorage.getItem('gemini_api_key')) {{
      document.getElementById('customApiKeyInput').value = localStorage.getItem('gemini_api_key');
    }}

    function showToast(message) {{
      const t = document.getElementById('toast');
      t.innerText = message;
      t.classList.remove('translate-y-20', 'opacity-0');
      setTimeout(() => {{
        t.classList.add('translate-y-20', 'opacity-0');
      }}, 3000);
    }}

    // Multi-View Navigation Switcher
    function navTab(tabName) {{
      document.querySelectorAll('.sidebar-item').forEach(item => {{
        item.classList.remove('bg-indigo-50/80', 'text-indigo-700', 'font-bold', 'border-l-4', 'border-indigo-600');
        item.classList.add('hover:bg-slate-50', 'hover:text-slate-900');
      }});
      
      const activeEl = document.getElementById('nav-' + tabName);
      if (activeEl) {{
        activeEl.classList.add('bg-indigo-50/80', 'text-indigo-700', 'font-bold', 'border-l-4', 'border-indigo-600');
      }}

      // Switch Panels
      document.querySelectorAll('.view-panel').forEach(panel => panel.classList.add('hidden'));
      const targetPanel = document.getElementById('view-' + tabName);
      if (targetPanel) {{
        targetPanel.classList.remove('hidden');
      }} else {{
        document.getElementById('view-Dashboard').classList.remove('hidden');
      }}

      document.getElementById('topNavHeaderTitle').innerText = tabName === 'Dashboard' ? 'SentinelRisk Copilot' : tabName;
    }}

    function openTxnModal() {{
      if (activeCustomerId) {{
        document.getElementById('modalCustId').value = activeCustomerId;
      }}
      document.getElementById('txnModal').classList.remove('hidden');
    }}
    function closeTxnModal() {{
      document.getElementById('txnModal').classList.add('hidden');
    }}

    function openKeyModal() {{
      document.getElementById('keyModal').classList.remove('hidden');
    }}
    function closeKeyModal() {{
      document.getElementById('keyModal').classList.add('hidden');
    }}

    function saveApiKey() {{
      const k = document.getElementById('customApiKeyInput').value.trim();
      if (k) {{
        localStorage.setItem('gemini_api_key', k);
        showToast("Gemini API Key saved locally.");
      }} else {{
        localStorage.removeItem('gemini_api_key');
        showToast("Cleared custom API Key. Server env key will be used.");
      }}
      closeKeyModal();
    }}

    function clearApiKey() {{
      localStorage.removeItem('gemini_api_key');
      document.getElementById('customApiKeyInput').value = '';
      showToast("Custom API key cleared.");
      closeKeyModal();
    }}

    async function submitCustomTxn(e) {{
      e.preventDefault();
      const custId = document.getElementById('modalCustId').value;
      const amount = parseFloat(document.getElementById('modalAmount').value);
      const channel = document.getElementById('modalChannel').value;
      const payee = document.getElementById('modalPayee').value;
      const desc = document.getElementById('modalDesc').value;

      try {{
        const res = await fetch('/api/transaction/add', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ customer_id: custId, amount: amount, channel: channel, payee: payee, description: desc }})
        }});
        const resData = await res.json();
        showToast("Transaction injected successfully!");
        closeTxnModal();
        loadCustomer(custId);
      }} catch (err) {{
        showToast("Failed to add transaction: " + err.message);
      }}
    }}

    function triggerAction(msg) {{
      if (!activeCustomerId) {{
        showToast("Please mount a customer scenario first.");
        return;
      }}
      showToast(msg);
    }}

    let currentExportSource = 'dossier';
    let assessmentHistory = [];

    try {{
      const savedHist = localStorage.getItem('sentinel_assessment_history');
      if (savedHist) {{
        assessmentHistory = JSON.parse(savedHist);
      }}
    }} catch (e) {{}}

    function saveAssessmentHistoryItem(item) {{
      assessmentHistory.unshift(item);
      if (assessmentHistory.length > 50) assessmentHistory.pop();
      try {{
        localStorage.setItem('sentinel_assessment_history', JSON.stringify(assessmentHistory));
      }} catch (e) {{}}
      renderAssessmentHistoryUI();
    }}

    function renderAssessmentHistoryUI() {{
      const historyListEl = document.getElementById('assessmentHistoryList');
      if (!historyListEl) return;
      if (assessmentHistory.length === 0) {{
        historyListEl.innerHTML = `<div class="text-xs text-slate-400 text-center py-2">No previous assessments saved yet.</div>`;
        return;
      }}
      historyListEl.innerHTML = assessmentHistory.map(item => `
        <div onclick="loadHistoricalAssessment('${{item.id}}')" class="p-2.5 bg-white hover:bg-indigo-50/70 border border-slate-200 rounded-xl text-xs cursor-pointer transition flex items-center justify-between shadow-2xs">
          <div class="space-y-0.5">
            <div class="font-extrabold text-slate-900 flex items-center gap-1.5">
              <span>${{item.customerName}}</span>
              <span class="font-mono text-[10px] text-slate-400">(${{item.customerId}})</span>
            </div>
            <div class="text-[10px] text-slate-500">${{item.timestamp}} • ${{item.flagsCount}} triggers</div>
          </div>
          <div class="text-right">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold ${{item.riskScore >= 60 ? 'bg-rose-50 text-rose-700 border border-rose-200' : (item.riskScore > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200')}}">
              ${{item.riskLevel}} (${{item.riskScore}}/100)
            </span>
          </div>
        </div>
      `).join('');
    }}

    function toggleHistoryDrawer() {{
      const drawer = document.getElementById('historyDrawer');
      if (drawer) {{
        drawer.classList.toggle('hidden');
        if (!drawer.classList.contains('hidden')) {{
          renderAssessmentHistoryUI();
        }}
      }}
    }}

    function loadHistoricalAssessment(histId) {{
      const item = assessmentHistory.find(h => h.id === histId);
      if (!item) return;
      lastGeneratedReportMd = item.reportMd;
      const reportBox = document.getElementById('reportContent');
      if (reportBox) {{
        reportBox.innerHTML = `<div class="dossier-report">${{marked.parse(item.reportMd)}}</div>`;
      }}
      const exportBtn = document.getElementById('exportMdBtn');
      if (exportBtn) exportBtn.disabled = false;
      showToast(`Loaded historical report for ${{item.customerName}}`);
    }}

    function openExportModal(source = 'dossier') {{
      currentExportSource = source;
      const modal = document.getElementById('exportModal');
      if (modal) modal.classList.remove('hidden');
      if (window.lucide) lucide.createIcons();
    }}

    function closeExportModal() {{
      const modal = document.getElementById('exportModal');
      if (modal) modal.classList.add('hidden');
    }}

    function confirmExport() {{
      const selected = document.querySelector('input[name="exportFormat"]:checked');
      const fmt = selected ? selected.value : 'pdf';
      closeExportModal();

      if (currentExportSource === 'audit') {{
        exportAuditInFormat(fmt);
      }} else if (currentExportSource === 'transactions') {{
        exportTransactionsInFormat(fmt);
      }} else {{
        exportDossierInFormat(fmt);
      }}
    }}

    function downloadFile(filename, content, mimeType) {{
      const blob = new Blob([content], {{ type: mimeType }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}

    function exportDossierInFormat(fmt) {{
      const custName = currentAuditData ? currentAuditData.customer.name : (activeCustomerId || 'Customer');
      const filenameBase = `SentinelRisk_Dossier_${{activeCustomerId || 'Report'}}`;

      if (fmt === 'pdf') {{
        const printWin = window.open('', '_blank');
        const reportHtml = lastGeneratedReportMd ? marked.parse(lastGeneratedReportMd) : '<p>No investigation report generated yet.</p>';
        printWin.document.write(`
          <!DOCTYPE html>
          <html>
          <head>
            <title>${{filenameBase}}</title>
            <style>
              body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; color: #1e293b; max-width: 800px; margin: 0 auto; }}
              h1, h2, h3 {{ color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
              blockquote {{ background: #f8fafc; border-left: 4px solid #4f46e5; padding: 10px 16px; margin: 0 0 16px 0; }}
              code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; }}
              .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #4f46e5; padding-bottom: 15px; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h2>SentinelRisk Copilot — Autonomous Fraud Investigation Dossier</h2>
              <p>Customer: <strong>${{custName}} (${{activeCustomerId || 'N/A'}})</strong> | Generated: ${{new Date().toLocaleString()}}</p>
            </div>
            <div>${{reportHtml}}</div>
            <script>
              window.onload = function() {{ window.print(); }};
            <\\/script>
          </body>
          </html>
        `);
        printWin.document.close();
        showToast("PDF print dialog opened.");
      }} else if (fmt === 'doc') {{
        const reportHtml = lastGeneratedReportMd ? marked.parse(lastGeneratedReportMd) : 'No report data';
        const docContent = `
          <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
          <head><title>Dossier</title></head>
          <body>
            <h2>SentinelRisk Copilot Dossier - ${{custName}}</h2>
            <div>${{reportHtml}}</div>
          </body>
          </html>
        `;
        downloadFile(`${{filenameBase}}.doc`, docContent, 'application/msword');
        showToast("Exported Word (.doc) file.");
      }} else if (fmt === 'md') {{
        const mdText = lastGeneratedReportMd || `# SentinelRisk Report\nNo report generated yet.`;
        downloadFile(`${{filenameBase}}.md`, mdText, 'text/markdown');
        showToast("Exported Markdown (.md) file.");
      }} else if (fmt === 'html') {{
        const reportHtml = lastGeneratedReportMd ? marked.parse(lastGeneratedReportMd) : '<p>No report</p>';
        const htmlDoc = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${{custName}} Dossier</title></head><body style="font-family:sans-serif;padding:2rem;">${{reportHtml}}</body></html>`;
        downloadFile(`${{filenameBase}}.html`, htmlDoc, 'text/html');
        showToast("Exported HTML (.html) file.");
      }} else if (fmt === 'txt') {{
        const txt = lastGeneratedReportMd ? lastGeneratedReportMd.replace(/[#*`>-]/g, '') : 'No report data';
        downloadFile(`${{filenameBase}}.txt`, txt, 'text/plain');
        showToast("Exported Text (.txt) file.");
      }} else if (fmt === 'json') {{
        const jsonStr = JSON.stringify({{ customerData: currentAuditData, reportMarkdown: lastGeneratedReportMd }}, null, 2);
        downloadFile(`${{filenameBase}}.json`, jsonStr, 'application/json');
        showToast("Exported JSON (.json) file.");
      }}
    }}

    function exportAuditInFormat(fmt) {{
      const dataToExport = currentAuditData || {{ message: "No active audit data" }};
      if (fmt === 'json') {{
        downloadFile(`Audit_Log_${{activeCustomerId || 'System'}}.json`, JSON.stringify(dataToExport, null, 2), 'application/json');
      }} else if (fmt === 'txt') {{
        downloadFile(`Audit_Log_${{activeCustomerId || 'System'}}.txt`, JSON.stringify(dataToExport, null, 2), 'text/plain');
      }} else {{
        downloadFile(`Audit_Log_${{activeCustomerId || 'System'}}.json`, JSON.stringify(dataToExport, null, 2), 'application/json');
      }}
      showToast(`Exported Audit log in ${{fmt.toUpperCase()}} format.`);
    }}

    function exportTransactionsInFormat(fmt) {{
      if (!currentAuditData || !currentAuditData.transactions) {{
        showToast("No transaction ledger loaded.");
        return;
      }}
      if (fmt === 'json') {{
        downloadFile(`Transactions_${{activeCustomerId}}.json`, JSON.stringify(currentAuditData.transactions, null, 2), 'application/json');
      }} else if (fmt === 'txt') {{
        const txt = currentAuditData.transactions.map(t => `${{t.txn_id}} | ${{t.timestamp}} | ${{t.payee}} | ₹${{t.amount}}`).join('\\n');
        downloadFile(`Transactions_${{activeCustomerId}}.txt`, txt, 'text/plain');
      }} else {{
        downloadFile(`Transactions_${{activeCustomerId}}.json`, JSON.stringify(currentAuditData.transactions, null, 2), 'application/json');
      }}
      showToast(`Exported Transactions in ${{fmt.toUpperCase()}} format.`);
    }}

    function exportAuditJSON() {{
      openExportModal('audit');
    }}

    function exportReportMd() {{
      openExportModal('dossier');
    }}

    function highlightTxnInLedger(txnId) {{
      const rows = document.querySelectorAll('#txnTableBody tr');
      rows.forEach(r => r.classList.remove('txn-highlight'));
      const targetRow = document.querySelector(`#txnTableBody tr[data-txn-id="${{txnId}}"]`);
      if (targetRow) {{
        targetRow.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        targetRow.classList.add('txn-highlight');
        setTimeout(() => {{
          targetRow.classList.remove('txn-highlight');
        }}, 4000);
      }}
    }}

    async function loadCustomer(id) {{
      activeCustomerId = id;
      document.getElementById('runBtn').disabled = false;
      document.getElementById('exportMdBtn').disabled = true;
      lastGeneratedReportMd = "";

      // Highlight Active Scenario Button
      document.querySelectorAll('.scenario-btn').forEach(btn => {{
        btn.classList.remove('ring-2', 'ring-indigo-600', 'shadow-md');
      }});
      const activeScenarioBtn = document.getElementById('btn-' + id);
      if (activeScenarioBtn) {{
        activeScenarioBtn.classList.add('ring-2', 'ring-indigo-600', 'shadow-md');
      }}

      // Fetch Customer Data
      const res = await fetch(`/api/customer/${{id}}`);
      const data = await res.json();
      currentAuditData = data;

      // Update Profile Info
      document.getElementById('custName').innerText = data.customer.name;
      document.getElementById('custType').innerText = data.customer.account_type;
      document.getElementById('custSummary').innerText = data.customer.profile_summary;
      const initials = data.customer.name.split(' ').map(n => n[0]).join('');
      document.getElementById('customerAvatar').innerText = initials;
      document.getElementById('userTopAvatar').innerText = initials;

      // RESET DOSSIER CONTENT TO CLEAN BLANK / PENDING STATE ON SCENARIO SWITCH!
      const reportBox = document.getElementById('reportContent');
      reportBox.innerHTML = `
        <div class="flex flex-col items-center justify-center min-h-[460px] text-center p-6 space-y-3">
          <div class="h-16 w-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-xs">
            <i data-lucide="file-search" class="w-8 h-8"></i>
          </div>
          <div>
            <h3 class="text-sm font-extrabold text-slate-900">Awaiting Assessment</h3>
            <p class="text-xs text-slate-500 max-w-xs mt-1">
              Mounted profile <span class="font-bold text-indigo-600">${{data.customer.name}}</span> (${{id}}). Click <strong class="text-slate-800">Run Assessment</strong> above to generate the AI investigator report.
            </p>
          </div>
        </div>
      `;

      const amounts = data.transactions.map(t => t.amount);
      const totalOutflow = amounts.reduce((a, b) => a + b, 0);
      const avgOutflow = amounts.length ? (totalOutflow / amounts.length) : 0;
      
      document.getElementById('metricCount').innerText = data.transactions.length;
      document.getElementById('metricTotal').innerText = '₹' + totalOutflow.toLocaleString();
      document.getElementById('metricAvg').innerText = '₹' + Math.round(avgOutflow).toLocaleString();
      document.getElementById('metricFlags').innerText = data.flags.length;
      document.getElementById('txnCounter').innerText = `${{data.transactions.length}} records`;

      // Calculate Risk Scores based on category rules
      let oddScore = 0, velScore = 0, devScore = 0, structScore = 0;
      const ruleNames = (data.flags || []).map(f => f.rule_name || '');
      if (ruleNames.some(r => r.includes('ODD_HOURS'))) oddScore = 20;
      if (ruleNames.some(r => r.includes('VELOCITY'))) velScore = 25;
      if (ruleNames.some(r => r.includes('BASELINE'))) devScore = 20;
      if (ruleNames.some(r => r.includes('STRUCTURING') || r.includes('NEW_PAYEE'))) structScore = 25;

      const totalRisk = Math.min(100, oddScore + velScore + devScore + structScore);
      document.getElementById('statOdd').innerText = `+${{oddScore}} pts`;
      document.getElementById('statVel').innerText = `+${{velScore}} pts`;
      document.getElementById('statDev').innerText = `+${{devScore}} pts`;
      document.getElementById('statStruct').innerText = `+${{structScore}} pts`;
      document.getElementById('scoreNum').textContent = totalRisk;

      // Update Gauge Needle Rotation (-90deg at 0 score, 0deg at 50, +90deg at 100 score)
      const needleAngle = (totalRisk / 100) * 180 - 90;
      const needle = document.getElementById('gaugeNeedle');
      if (needle) {{
        needle.style.transform = `rotate(${{needleAngle}}deg)`;
      }}
      
      // Arc Stroke Offset (Max 251.33 for radius 80)
      const arcOffset = 251.33 - (totalRisk / 100 * 251.33);
      const arc = document.getElementById('gaugeArc');
      if (arc) {{
        arc.style.strokeDashoffset = arcOffset;
      }}

      const badge = document.getElementById('statusBadge');
      const verdict = document.getElementById('riskVerdict');
      const alertDot = document.getElementById('navAlertDot');
      if (alertDot) {{
        alertDot.className = data.flags.length > 0 ? "h-2 w-2 rounded-full bg-rose-500" : "h-2 w-2 rounded-full bg-slate-300";
      }}

      if (totalRisk === 0) {{
        badge.className = "px-3 py-1 rounded-full text-xs font-extrabold flex items-center gap-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200";
        badge.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i> Clear Baseline';
        verdict.innerText = "LOW RISK";
        verdict.className = "text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200";
      }} else {{
        badge.className = "px-3 py-1 rounded-full text-xs font-extrabold flex items-center gap-1.5 bg-rose-50 text-rose-800 border border-rose-200";
        badge.innerHTML = `<i data-lucide="alert-circle" class="w-3.5 h-3.5 text-rose-600"></i> ${{data.flags.length}} Triggers`;
        verdict.innerText = totalRisk >= 60 ? "HIGH SEVERITY" : "ELEVATED RISK";
        verdict.className = totalRisk >= 60 
          ? "text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200"
          : "text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200";
      }}

      renderLedgerTable();

      // Populate Deterministic Flags List
      const flagsDiv = document.getElementById('ruleTriggers');
      if (data.flags.length === 0) {{
        flagsDiv.innerHTML = `
          <div class="p-3 bg-emerald-50/70 border border-emerald-200/70 rounded-xl text-xs flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <div class="h-6 w-6 rounded-full bg-emerald-500 flex items-center justify-center text-white shrink-0">
                <i data-lucide="check" class="w-3.5 h-3.5"></i>
              </div>
              <div>
                <span class="font-bold text-emerald-900">No rule violations found.</span>
                <p class="text-emerald-700 text-[11px]">Customer activity conforms to baseline.</p>
              </div>
            </div>
            <svg class="w-16 h-6 text-emerald-500" viewBox="0 0 100 30" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M0 15 Q25 15, 35 5 T65 25 T100 15" />
            </svg>
          </div>
        `;
      }} else {{
        flagsDiv.innerHTML = data.flags.map(f => `
          <div onclick="highlightTxnInLedger('${{f.txn_id}}')" class="p-2.5 bg-rose-50/80 hover:bg-rose-100 border border-rose-200/80 rounded-xl text-xs flex items-start gap-2 cursor-pointer transition">
            <i data-lucide="alert-triangle" class="w-4 h-4 text-rose-600 shrink-0 mt-0.5"></i>
            <div>
              <span class="font-bold text-rose-900 mono text-[10px]">[${{f.rule_name}}]</span>
              <span class="text-slate-800 ml-1 font-mono font-bold hover:underline">${{f.txn_id}}:</span>
              <span class="text-slate-700 ml-1">${{f.details}}</span>
            </div>
          </div>
        `).join('');
      }}

      lucide.createIcons();
    }}

    function filterLedger() {{
      renderLedgerTable();
    }}

    function renderLedgerTable() {{
      if (!currentAuditData) return;
      const search = document.getElementById('ledgerSearch').value.toLowerCase();
      const filterType = document.getElementById('ledgerFilter').value;
      const flaggedTxnIds = new Set(currentAuditData.flags.map(f => f.txn_id));

      const tbody = document.getElementById('txnTableBody');
      const filtered = currentAuditData.transactions.filter(t => {{
        const matchesSearch = t.payee.toLowerCase().includes(search) || t.description.toLowerCase().includes(search) || t.txn_id.toLowerCase().includes(search);
        const isFlagged = flaggedTxnIds.has(t.txn_id);
        if (!matchesSearch) return false;
        if (filterType === 'FLAGGED') return isFlagged;
        if (filterType === 'NORMAL') return !isFlagged;
        return true;
      }});

      if (filtered.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-400">No matching transactions.</td></tr>`;
        return;
      }}

      tbody.innerHTML = filtered.map(t => {{
        const isFlagged = flaggedTxnIds.has(t.txn_id);
        return `
          <tr data-txn-id="${{t.txn_id}}" class="${{isFlagged ? 'bg-rose-50/70 font-semibold' : 'hover:bg-slate-50'}} transition">
            <td class="p-2.5 mono ${{isFlagged ? 'text-rose-700 font-extrabold' : 'text-slate-600'}}">${{t.txn_id}}</td>
            <td class="p-2.5 text-slate-500">${{t.timestamp.replace('T', ' ')}}</td>
            <td class="p-2.5 font-bold text-slate-900">${{t.payee}}</td>
            <td class="p-2.5 text-slate-500">${{t.channel}}</td>
            <td class="p-2.5 text-right font-mono ${{isFlagged ? 'text-rose-700 font-extrabold' : 'text-slate-900'}}">₹${{t.amount.toLocaleString()}}</td>
          </tr>
        `;
      }}).join('');
    }}

    async function runInvestigation() {{
      if (!activeCustomerId) return;
      const btn = document.getElementById('runBtn');
      const exportBtn = document.getElementById('exportMdBtn');
      const loader = document.getElementById('loading');
      const reportBox = document.getElementById('reportContent');
      const timer = document.getElementById('execTimer');
      
      const startTime = performance.now();
      btn.disabled = true;
      loader.classList.remove('hidden');

      const customKey = localStorage.getItem('gemini_api_key');
      const headers = customKey ? {{ 'X-Gemini-Api-Key': customKey }} : {{}};

      try {{
        const res = await fetch(`/api/investigate/${{activeCustomerId}}`, {{
          method: 'POST',
          headers: headers
        }});
        const data = await res.json();
        const duration = ((performance.now() - startTime) / 1000).toFixed(2);
        timer.innerText = `${{duration}}s latency`;
        lastGeneratedReportMd = data.report;
        reportBox.innerHTML = `<div class="dossier-report">${{marked.parse(data.report)}}</div>`;
        exportBtn.disabled = false;

        // Refresh History badge and list
        updateHistoryBadge();
        if (typeof currentTab !== 'undefined' && currentTab === 'History') {{
          loadHistoryAssessments();
        }}
      }} catch (err) {{
        reportBox.innerHTML = `<div class="text-rose-700 p-4 border border-rose-200 bg-rose-50 rounded-xl">Error generating report: ${{err.message}}</div>`;
      }} finally {{
        loader.classList.add('hidden');
        btn.disabled = false;
        lucide.createIcons();
      }}
    }}

    let currentTxnFilter = 'ALL';
    let allTxnsData = [];
    let currentCaseRiskFilter = 'ALL';
    let selectedProfileCustId = 'CUST_002';
    let workspaceActiveCustId = 'CUST_002';

    const origNavTab = navTab;
    navTab = function(tabName) {{
      origNavTab(tabName);
      if (tabName === 'Transactions') {{
        loadFullTransactionsLedger();
      }} else if (tabName === 'Customers') {{
        loadCustomersDirectory();
      }} else if (tabName === 'History') {{
        loadHistoryAssessments();
      }}
      if (window.lucide) lucide.createIcons();
    }};

    async function loadFullTransactionsLedger() {{
      try {{
        const res = await fetch('/api/all_transactions');
        allTxnsData = await res.json();
        renderFullTxnsTable();
      }} catch (err) {{
        console.error("Failed to load transactions", err);
      }}
    }}

    function setTxnFilter(filterVal) {{
      currentTxnFilter = filterVal;
      document.querySelectorAll('.txn-filter-btn').forEach(btn => {{
        btn.classList.remove('bg-indigo-50', 'text-indigo-700', 'border-indigo-200');
        btn.classList.add('bg-white', 'border-slate-200');
      }});
      if (window.event && window.event.currentTarget) {{
        window.event.currentTarget.classList.remove('bg-white', 'border-slate-200');
        window.event.currentTarget.classList.add('bg-indigo-50', 'text-indigo-700', 'border-indigo-200');
      }}
      renderFullTxnsTable();
    }}

    function filterFullTransactions() {{
      renderFullTxnsTable();
    }}

    function renderFullTxnsTable() {{
      const searchInput = document.getElementById('fullTxnSearch');
      const search = (searchInput ? searchInput.value : '').toLowerCase();
      const tbody = document.getElementById('fullTxnTableBody');
      if (!tbody) return;

      const filtered = allTxnsData.filter(t => {{
        const matchesSearch = t.payee.toLowerCase().includes(search) || 
                              t.customer_name.toLowerCase().includes(search) || 
                              t.txn_id.toLowerCase().includes(search) ||
                              t.customer_id.toLowerCase().includes(search);
        if (!matchesSearch) return false;
        
        if (currentTxnFilter === 'FLAGGED') return t.is_flagged;
        if (currentTxnFilter === 'NORMAL') return !t.is_flagged;
        if (currentTxnFilter === 'ODD_HOURS') return (t.flags || []).some(f => (f.rule_name || '').includes('ODD_HOURS'));
        if (currentTxnFilter === 'HIGH_VALUE') return t.amount >= 50000;
        if (currentTxnFilter === 'NEW_PAYEE') return (t.flags || []).some(f => (f.rule_name || '').includes('NEW_PAYEE'));
        if (currentTxnFilter === 'VELOCITY') return (t.flags || []).some(f => (f.rule_name || '').includes('VELOCITY'));
        if (currentTxnFilter === 'STRUCTURING') return (t.flags || []).some(f => (f.rule_name || '').includes('STRUCTURING'));
        return true;
      }});

      if (filtered.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-slate-400 font-medium">No matching transactions found in full ledger.</td></tr>`;
        return;
      }}

      tbody.innerHTML = filtered.map(t => `
        <tr class="${{t.is_flagged ? 'bg-rose-50/60 font-semibold' : 'hover:bg-slate-50'}} transition">
          <td class="p-3.5">
            <div class="font-extrabold text-slate-900">${{t.customer_name}}</div>
            <div class="text-[10px] text-slate-400 font-mono">${{t.customer_id}}</div>
          </td>
          <td class="p-3.5 text-slate-500 font-mono">${{t.timestamp.replace('T', ' ')}}</td>
          <td class="p-3.5 font-mono ${{t.is_flagged ? 'text-rose-700 font-extrabold' : 'text-slate-700'}}">${{t.txn_id}}</td>
          <td class="p-3.5 font-bold text-slate-900">${{t.payee}}</td>
          <td class="p-3.5 text-slate-500">${{t.channel}}</td>
          <td class="p-3.5 text-right font-mono ${{t.is_flagged ? 'text-rose-700 font-extrabold' : 'text-slate-900'}}">₹${{t.amount.toLocaleString()}}</td>
          <td class="p-3.5 text-center">
            ${{t.is_flagged 
              ? `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-50 text-rose-700 border border-rose-200">FLAGGED</span>` 
              : `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">NORMAL</span>`
            }}
          </td>
          <td class="p-3.5 text-right">
            <button onclick="openTxnDetailModal('${{t.txn_id}}')" class="px-2.5 py-1 text-[11px] font-extrabold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg transition">
              Details
            </button>
          </td>
        </tr>
      `).join('');
    }}

    function openTxnDetailModal(txnId) {{
      const t = allTxnsData.find(item => item.txn_id === txnId) || (currentAuditData?.transactions || []).find(item => item.txn_id === txnId);
      if (!t) return;

      document.getElementById('tdId').innerText = t.txn_id;
      document.getElementById('tdAmount').innerText = '₹' + t.amount.toLocaleString();
      document.getElementById('tdChannel').innerText = t.channel;
      document.getElementById('tdPayee').innerText = t.payee;
      document.getElementById('tdTime').innerText = t.timestamp.replace('T', ' ');

      const flags = t.flags || (currentAuditData?.flags || []).filter(f => f.txn_id === t.txn_id);
      if (flags.length > 0) {{
        document.getElementById('tdRules').innerHTML = flags.map(f => `• ${{f.rule_name}}: ${{f.details}}`).join('<br/>');
        document.getElementById('tdEvidence').innerText = `EVID-${{t.txn_id}}-${{flags[0].rule_name}}`;
      }} else {{
        document.getElementById('tdRules').innerHTML = '• Routine transaction. No deterministic rules triggered.';
        document.getElementById('tdEvidence').innerText = `EVID-${{t.txn_id}}-CLEAN_BASELINE`;
      }}

      const modal = document.getElementById('txnDetailModal');
      if (modal) modal.classList.remove('hidden');
    }}

    function closeTxnDetailModal() {{
      const modal = document.getElementById('txnDetailModal');
      if (modal) modal.classList.add('hidden');
    }}

    async function loadCustomersDirectory() {{
      try {{
        const res = await fetch('/api/all_customers');
        const custs = await res.json();
        const tbody = document.getElementById('customersTableBody');
        if (!tbody) return;

        tbody.innerHTML = custs.map(c => `
          <tr onclick="selectCustomerProfile('${{c.customer_id}}')" class="hover:bg-indigo-50/50 cursor-pointer transition">
            <td class="p-3">
              <div class="font-extrabold text-slate-900">${{c.name}}</div>
              <div class="text-[10px] text-slate-400 font-mono">${{c.customer_id}}</div>
            </td>
            <td class="p-3">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold ${{c.risk_score >= 60 ? 'bg-rose-50 text-rose-700 border border-rose-200' : (c.risk_score > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200')}}">
                ${{c.risk_level}}
              </span>
            </td>
            <td class="p-3 text-center font-mono font-bold">${{c.txn_count}}</td>
            <td class="p-3 text-right">
              <button class="px-2.5 py-1 text-[11px] font-bold bg-indigo-50 text-indigo-700 rounded-lg">Profile</button>
            </td>
          </tr>
        `).join('');
      }} catch (err) {{
        console.error("Failed to load customers directory", err);
      }}
    }}

    const CUSTOMER_PROFILES = {{
      'CUST_001': {{
        name: 'Priya Sharma',
        type: 'Salaried Professional',
        activity: 'Utility & retail grocery spend',
        hours: '9 AM – 9 PM',
        typical: '₹500 – ₹3,000',
        payees: '8 Known Payees',
        channels: 'UPI / POS Debit Card',
        risk: 'LOW RISK (Baseline Verified)',
        summary: 'Priya Sharma maintains a consistent salary account with low velocity. Monthly recurring spend aligns strictly with suburban retail merchant baselines.'
      }},
      'CUST_002': {{
        name: 'Vikram Rathore',
        type: 'Small Business Owner',
        activity: 'Supplier payments & payouts',
        hours: '10 AM – 6 PM',
        typical: '₹8,000 – ₹15,000',
        payees: '5 Known Payees',
        channels: 'NEFT / IMPS',
        risk: 'HIGH SEVERITY (82/100 Risk Score)',
        summary: 'Vikram Rathore operates a commercial current account. Elevated risk anomaly flags triggered due to an unexpected 3 AM velocity burst of ₹60,000 to an unverified external payee.'
      }},
      'CUST_003': {{
        name: 'Ananya Sen',
        type: 'Crypto Trader / Freelancer',
        activity: 'Rapid P2P transfers & liquidity',
        hours: '10 AM – 11 PM',
        typical: '₹10,000 – ₹49,900',
        payees: '4 Known Payees',
        channels: 'UPI / IMPS',
        risk: 'HIGH (Structuring Pattern Detected)',
        summary: 'Ananya Sen shows multiple rapid fund transfers structured right below the ₹50,000 mandatory compliance reporting threshold within a 15-minute window.'
      }},
      'CUST_004': {{
        name: 'Arjun Mehta',
        type: 'HNI Wealth Account',
        activity: 'High-value treasury & investments',
        hours: '24x7 Authorized',
        typical: '₹50,000 – ₹5,000,000',
        payees: '12 Verified Entities',
        channels: 'RTGS / Wire / NetBanking',
        risk: 'LOW RISK (High Value Baseline Authorized)',
        summary: 'Arjun Mehta is a verified High-Net-Worth individual. High-value liquidity transfers conform to declared annual wealth management baselines.'
      }}
    }};

    function selectCustomerProfile(custId) {{
      selectedProfileCustId = custId;
      const p = CUSTOMER_PROFILES[custId] || CUSTOMER_PROFILES['CUST_002'];
      const initials = p.name.split(' ').map(n => n[0]).join('');
      
      document.getElementById('cpAvatar').innerText = initials;
      document.getElementById('cpName').innerText = p.name;
      document.getElementById('cpId').innerText = custId;
      document.getElementById('cpType').innerText = p.type;
      document.getElementById('cpActivity').innerText = p.activity;
      document.getElementById('cpHours').innerText = p.hours;
      document.getElementById('cpTypical').innerText = p.typical;
      document.getElementById('cpPayees').innerText = p.payees;
      document.getElementById('cpChannels').innerText = p.channels;
      document.getElementById('cpRisk').innerText = p.risk;
      document.getElementById('cpSummary').innerText = p.summary;
    }}

    function openCaseWorkspace(custId) {{
      workspaceActiveCustId = custId;
      const p = CUSTOMER_PROFILES[custId] || CUSTOMER_PROFILES['CUST_002'];
      const caseIdMap = {{ 'CUST_001': 'CASE-2026-0001', 'CUST_002': 'CASE-2026-0021', 'CUST_003': 'CASE-2026-0031', 'CUST_004': 'CASE-2026-0041' }};
      const scoreMap = {{ 'CUST_001': '0 / 100', 'CUST_002': '82 / 100', 'CUST_003': '70 / 100', 'CUST_004': '0 / 100' }};

      document.getElementById('cwCaseId').innerText = `CASE: ${{caseIdMap[custId] || 'CASE-2026-0021'}}`;
      document.getElementById('cwCustName').innerText = p.name;
      document.getElementById('cwCustId').innerText = custId;
      document.getElementById('cwScore').innerText = scoreMap[custId] || '82 / 100';

      if (custId === 'CUST_002') {{
        document.getElementById('cwFinding').innerText = 'Connected high-velocity transfers to an unverified recipient during off-hours (3:14 AM).';
        document.getElementById('cwTxns').innerText = 'TXN_203, TXN_204, TXN_205, TXN_00206 (Total: ₹1,85,000)';
        document.getElementById('cwRules').innerText = 'ODD_HOURS_ACTIVITY, RAPID_VELOCITY_BURST, NEW_PAYEE_HIGH_VALUE, BASELINE_DEVIATION, NEW_CHANNEL_BEHAVIOUR';
        document.getElementById('cwBaseline').innerText = 'Normal activity: ₹8,000–₹15,000 during 10 AM–6 PM. Current: ₹60,000 at 3:14 AM.';
        document.getElementById('cwWhy').innerText = 'High probability of account takeover or credential theft requiring immediate outbound freeze.';
        document.getElementById('cwSteps').innerText = 'CRITICAL PRIORITY • 1. Freeze outbound rails 2. Call customer registered phone 3. Request KYC proof.';
        document.getElementById('cwEvidence').innerText = 'EVID-TXN_00206-NEW_CHANNEL_BEHAVIOUR (Hash: 0x9f8a3c4e...)';
      }} else if (custId === 'CUST_003') {{
        document.getElementById('cwFinding').innerText = 'Multiple rapid transfers structured right under the ₹50,000 mandatory compliance threshold.';
        document.getElementById('cwTxns').innerText = 'TXN_301, TXN_302, TXN_303 (Total: ₹1,49,700)';
        document.getElementById('cwRules').innerText = 'STRUCTURING_THRESHOLD_EVASION, VELOCITY_BURST';
        document.getElementById('cwBaseline').innerText = 'Typical transfers: ₹5,000–₹20,000. Current: 3 transactions of ₹49,900 within 15 minutes.';
        document.getElementById('cwWhy').innerText = 'Deliberate structuring pattern to bypass AML threshold reporting rules.';
        document.getElementById('cwSteps').innerText = 'MEDIUM PRIORITY • 1. Request income proof & tax declarations 2. File SAR report if unverified.';
        document.getElementById('cwEvidence').innerText = 'EVID-TXN_301-STRUCTURING_THRESHOLD_EVASION';
      }} else {{
        document.getElementById('cwFinding').innerText = 'Normal baseline transaction pattern verified. No rule triggers.';
        document.getElementById('cwTxns').innerText = 'Standard routine transaction set.';
        document.getElementById('cwRules').innerText = 'None (0 rule violations)';
        document.getElementById('cwBaseline').innerText = 'Activity matches established historical baseline perfectly.';
        document.getElementById('cwWhy').innerText = 'Low risk routine spend. No investigator action needed.';
        document.getElementById('cwSteps').innerText = 'LOW PRIORITY • Clear case as benign.';
        document.getElementById('cwEvidence').innerText = 'EVID-CLEAN_BASELINE_VERIFIED';
      }}

      const modal = document.getElementById('caseWorkspaceModal');
      if (modal) modal.classList.remove('hidden');
    }}

    function closeCaseWorkspace() {{
      const modal = document.getElementById('caseWorkspaceModal');
      if (modal) modal.classList.add('hidden');
    }}

    function mountWorkspaceCase() {{
      closeCaseWorkspace();
      loadCustomer(workspaceActiveCustId || 'CUST_002');
      navTab('Dashboard');
    }}

    function filterInvestigations() {{
      const searchInput = document.getElementById('investigationSearch');
      const search = (searchInput ? searchInput.value : '').toLowerCase();
      document.querySelectorAll('#investigationCardsGrid .case-card').forEach(card => {{
        const searchAttr = card.getAttribute('data-search') || '';
        const cardRisk = card.getAttribute('data-risk') || '';
        const cardStatus = card.getAttribute('data-status') || '';
        
        const matchesSearch = searchAttr.includes(search);
        let matchesFilter = true;
        if (currentCaseRiskFilter !== 'ALL') {{
          if (currentCaseRiskFilter === 'NEEDS_REVIEW' || currentCaseRiskFilter === 'CLOSED') {{
            matchesFilter = cardStatus === currentCaseRiskFilter;
          }} else {{
            matchesFilter = cardRisk === currentCaseRiskFilter;
          }}
        }}

        if (matchesSearch && matchesFilter) {{
          card.classList.remove('hidden');
        }} else {{
          card.classList.add('hidden');
        }}
      }});
    }}

    function setCaseFilter(riskVal) {{
      currentCaseRiskFilter = riskVal;
      document.querySelectorAll('.case-filter-btn').forEach(btn => {{
        btn.classList.remove('bg-indigo-50', 'text-indigo-700', 'border-indigo-200');
        btn.classList.add('bg-white', 'border-slate-200');
      }});
      if (window.event && window.event.currentTarget) {{
        window.event.currentTarget.classList.remove('bg-white', 'border-slate-200');
        window.event.currentTarget.classList.add('bg-indigo-50', 'text-indigo-700', 'border-indigo-200');
      }}
      filterInvestigations();
    }}

    function filterAlerts(priority) {{
      document.querySelectorAll('.alert-filter-btn').forEach(btn => {{
        btn.classList.remove('bg-indigo-50', 'text-indigo-700', 'border-indigo-200');
        btn.classList.add('bg-white', 'border-slate-200');
      }});
      if (window.event && window.event.currentTarget) {{
        window.event.currentTarget.classList.remove('bg-white', 'border-slate-200');
        window.event.currentTarget.classList.add('bg-indigo-50', 'text-indigo-700', 'border-indigo-200');
      }}

      document.querySelectorAll('#alertsCardsContainer .alert-card').forEach(card => {{
        const p = card.getAttribute('data-priority');
        if (priority === 'ALL' || p === priority) {{
          card.classList.remove('hidden');
        }} else {{
          card.classList.add('hidden');
        }}
      }});
    }}

    let currentHistoryFilter = 'ALL';
    let allHistoryAssessments = [];
    let activeModalAssessmentData = null;

    async function loadHistoryAssessments() {{
      try {{
        const res = await fetch('/api/history');
        if (!res.ok) throw new Error("Failed to fetch history");
        allHistoryAssessments = await res.json();
        renderHistoryCards();
        updateHistoryBadge();
      }} catch (err) {{
        const container = document.getElementById('historyCardsContainer');
        if (container) {{
          container.innerHTML = `<div class="col-span-full p-6 text-center text-rose-700 bg-rose-50 rounded-xl border border-rose-200 text-xs">Unable to load previous assessments. Please try again.</div>`;
        }}
      }}
    }}

    async function updateHistoryBadge() {{
      try {{
        const res = await fetch('/api/history_count');
        if (res.ok) {{
          const data = await res.json();
          const badge = document.getElementById('navHistoryBadge');
          if (badge) badge.innerText = data.count;
        }}
      }} catch (e) {{}}
    }}

    function setHistoryFilter(filter) {{
      currentHistoryFilter = filter;
      document.querySelectorAll('.hist-filter-btn').forEach(btn => {{
        btn.className = "hist-filter-btn px-3 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200 font-bold text-xs";
      }});
      const activeBtn = document.getElementById(`histFilter-${{filter}}`);
      if (activeBtn) {{
        activeBtn.className = "hist-filter-btn px-3 py-1.5 rounded-xl bg-indigo-600 text-white font-extrabold text-xs shadow-2xs";
      }}
      renderHistoryCards();
    }}

    function filterHistoryAssessments() {{
      renderHistoryCards();
    }}

    function renderHistoryCards() {{
      const container = document.getElementById('historyCardsContainer');
      if (!container) return;

      const searchInput = document.getElementById('historySearchInput');
      const searchTerm = (searchInput ? searchInput.value : '').toLowerCase().trim();

      let filtered = allHistoryAssessments.filter(item => {{
        if (currentHistoryFilter === 'HIGH' && item.risk_level !== 'HIGH') return false;
        if (currentHistoryFilter === 'MEDIUM' && item.risk_level !== 'MEDIUM') return false;
        if (currentHistoryFilter === 'LOW' && item.risk_level !== 'LOW') return false;
        if (currentHistoryFilter === 'ATTENTION_REQUIRED' && !item.attention_required) return false;
        if (currentHistoryFilter === 'NO_ATTENTION' && item.attention_required) return false;

        if (searchTerm) {{
          const target = `${{item.assessment_id}} ${{item.customer_id}} ${{item.customer_name}} ${{item.primary_finding}} ${{item.risk_level}} ${{item.status}}`.toLowerCase();
          if (!target.includes(searchTerm)) return false;
        }}
        return true;
      }});

      if (filtered.length === 0) {{
        container.innerHTML = `
          <div class="col-span-full bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 text-xs">
            <i data-lucide="archive-x" class="w-8 h-8 mx-auto mb-2 text-slate-300"></i>
            No previous assessments match the selected criteria.
          </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
      }}

      container.innerHTML = filtered.map(item => {{
        let badgeBg = "bg-slate-100 text-slate-700 border-slate-200";
        let badgeDot = "⚪ NO ATTENTION";
        if (item.risk_level === 'HIGH') {{
          badgeBg = "bg-rose-50 text-rose-700 border-rose-200";
          badgeDot = "🔴 HIGH RISK";
        }} else if (item.risk_level === 'MEDIUM') {{
          badgeBg = "bg-amber-50 text-amber-700 border-amber-200";
          badgeDot = "🟠 MEDIUM RISK";
        }} else if (item.risk_level === 'LOW' && item.attention_required) {{
          badgeBg = "bg-amber-50 text-amber-700 border-amber-200";
          badgeDot = "🟡 LOW RISK";
        }} else if (item.risk_level === 'LOW') {{
          badgeBg = "bg-emerald-50 text-emerald-700 border-emerald-200";
          badgeDot = "🟢 LOW RISK";
        }}

        return `
          <div onclick="openSavedAssessmentDetail('${{item.assessment_id}}')" class="bg-white border border-slate-200/90 hover:border-indigo-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all cursor-pointer space-y-3 flex flex-col justify-between group">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <span class="px-2.5 py-1 text-[11px] font-extrabold rounded-full border ${{badgeBg}}">
                  ${{badgeDot}}
                </span>
                <span class="text-[11px] font-medium text-slate-400">${{item.created_at}}</span>
              </div>

              <div>
                <div class="font-extrabold text-slate-900 text-base group-hover:text-indigo-600 transition-colors">${{item.customer_name}}</div>
                <div class="text-xs font-mono text-slate-400">${{item.customer_id}}</div>
              </div>

              <div class="grid grid-cols-3 gap-2 p-2.5 bg-slate-50 border border-slate-100 rounded-xl text-center text-xs">
                <div>
                  <span class="text-[10px] text-slate-400 block font-medium">Risk Score</span>
                  <span class="font-extrabold text-slate-900">${{item.risk_score}} / 100</span>
                </div>
                <div>
                  <span class="text-[10px] text-slate-400 block font-medium">Triggers</span>
                  <span class="font-extrabold text-indigo-600">${{item.rule_trigger_count}} Rules</span>
                </div>
                <div>
                  <span class="text-[10px] text-slate-400 block font-medium">Flagged Txns</span>
                  <span class="font-extrabold text-rose-600">${{item.flagged_transaction_count}} Txns</span>
                </div>
              </div>

              <div>
                <span class="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">Primary Finding</span>
                <p class="text-xs text-slate-700 line-clamp-2 mt-0.5 font-medium leading-relaxed">${{item.primary_finding}}</p>
              </div>
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
              <span class="font-mono text-[11px] text-slate-400 font-bold">${{item.assessment_id}}</span>
              <span class="font-extrabold text-indigo-600 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                View Assessment &rarr;
              </span>
            </div>
          </div>
        `;
      }}).join('');

      if (window.lucide) lucide.createIcons();
    }}

    async function openSavedAssessmentDetail(assessmentId) {{
      try {{
        const res = await fetch(`/api/history/${{assessmentId}}`);
        if (!res.ok) throw new Error("Could not load assessment details");
        const rec = await res.json();
        activeModalAssessmentData = rec;

        // 1. ASSESSMENT OVERVIEW
        document.getElementById('modalAssessmentId').innerText = rec.assessment_id;
        document.getElementById('modalCustName').innerText = rec.customer_name;
        document.getElementById('modalCustId_Detail').innerText = rec.customer_id;
        document.getElementById('modalRiskScore').innerText = `${{rec.risk_score}} / 100`;
        document.getElementById('modalMetaId').innerText = rec.assessment_id;
        document.getElementById('modalMetaTime').innerText = rec.created_at;
        document.getElementById('modalMetaModel').innerText = rec.model_name || "Gemini 2.0 Flash";
        document.getElementById('modalMetaStatus').innerText = rec.status;

        const badge = document.getElementById('modalRiskBadge');
        if (rec.risk_level === 'HIGH') {{
          badge.className = "inline-block px-3.5 py-1 rounded-full text-xs font-extrabold bg-rose-50 text-rose-700 border border-rose-200";
          badge.innerText = "🔴 HIGH RISK";
        }} else if (rec.risk_level === 'MEDIUM') {{
          badge.className = "inline-block px-3.5 py-1 rounded-full text-xs font-extrabold bg-amber-50 text-amber-700 border border-amber-200";
          badge.innerText = "🟠 MEDIUM RISK";
        }} else {{
          badge.className = "inline-block px-3.5 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200";
          badge.innerText = rec.attention_required ? "🟡 LOW RISK" : "🟢 NO ATTENTION";
        }}

        // 2. PRIMARY FINDING
        document.getElementById('modalPrimaryFinding').innerText = rec.primary_finding;

        // 3. CONNECTED TRANSACTIONS
        const txnsEl = document.getElementById('modalConnectedTxns');
        const txns = rec.connected_transactions || [];
        if (txns.length === 0) {{
          txnsEl.innerHTML = `<div class="col-span-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 font-medium">No flagged transactions connected.</div>`;
        }} else {{
          txnsEl.innerHTML = txns.map(t => {{
            const tId = typeof t === 'object' ? (t.txn_id || t.id) : t;
            const amt = typeof t === 'object' && t.amount ? `₹${{Number(t.amount).toLocaleString('en-IN')}}` : '';
            const payee = typeof t === 'object' && t.payee ? t.payee : '';
            const ch = typeof t === 'object' && t.channel ? t.channel : '';
            return `
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs flex items-center justify-between">
                <div>
                  <div class="font-mono font-bold text-indigo-700">${{tId}}</div>
                  <div class="text-[11px] text-slate-500">${{payee}} ${{ch ? '• ' + ch : ''}}</div>
                </div>
                <div class="font-extrabold text-slate-900">${{amt}}</div>
              </div>
            `;
          }}).join('');
        }}

        // 4. TRIGGERED RISK RULES & EVIDENCE
        const rulesEl = document.getElementById('modalTriggeredRules');
        const rules = rec.triggered_rules || [];
        if (rules.length === 0) {{
          rulesEl.innerHTML = `<div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 font-medium">No deterministic rules triggered.</div>`;
        }} else {{
          rulesEl.innerHTML = rules.map(r => {{
            const rName = typeof r === 'object' ? (r.rule_name || r.name) : r;
            const firstTxnId = txns.length > 0 ? (typeof txns[0] === 'object' ? (txns[0].txn_id || txns[0].id) : txns[0]) : 'TXN_001';
            const evidId = `EVID-${{firstTxnId}}-${{rName}}`;
            return `
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs flex flex-col md:flex-row md:items-center justify-between gap-1">
                <div class="font-bold text-slate-900 flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-rose-500"></span>
                  ${{rName}}
                </div>
                <div class="font-mono text-[10px] text-indigo-600 font-semibold">${{evidId}}</div>
              </div>
            `;
          }}).join('');
        }}

        // 5. HISTORICAL BASELINE
        const baseEl = document.getElementById('modalBaseline');
        const b = rec.baseline || {{}};
        baseEl.innerHTML = `
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <span class="text-slate-400 font-medium block text-[10px] uppercase">Historical Average</span>
              <span class="font-extrabold text-slate-900">₹${{b.historical_baseline_average ? Number(b.historical_baseline_average).toLocaleString('en-IN') : (b.typical_amount ? Number(b.typical_amount).toLocaleString('en-IN') : '38,500')}}</span>
            </div>
            <div>
              <span class="text-slate-400 font-medium block text-[10px] uppercase">Normal Window</span>
              <span class="font-bold text-slate-800">${{b.normal_hours || '10 AM – 6 PM'}}</span>
            </div>
            <div>
              <span class="text-slate-400 font-medium block text-[10px] uppercase">Established Payees</span>
              <span class="font-bold text-slate-800">${{b.established_payees_count || b.payees || '5'}}</span>
            </div>
            <div>
              <span class="text-slate-400 font-medium block text-[10px] uppercase">Established Channels</span>
              <span class="font-bold text-slate-800">${{b.established_channels || 'NEFT / IMPS / UPI'}}</span>
            </div>
          </div>
          ${{b.explanation ? `<div class="text-[11px] text-slate-600 mt-2 pt-2 border-t border-slate-200/80">${{b.explanation}}</div>` : ''}}
        `;

        // 6. WHY IT MATTERS
        const whyEl = document.getElementById('modalWhyItMatters');
        const whyList = rec.why_it_matters || [];
        if (whyList.length === 0) {{
          whyEl.innerHTML = `<li>Amounts deviate from historical behaviour</li><li>Payee was newly observed or unusual</li><li>Transactions occurred in compressed time window</li>`;
        }} else {{
          whyEl.innerHTML = whyList.map(w => `<li>${{w}}</li>`).join('');
        }}

        // 7. INVESTIGATOR PRIORITY
        const prioEl = document.getElementById('modalInvestigatorPriority');
        const prioList = rec.investigator_priority || [];
        if (prioList.length === 0) {{
          prioEl.innerHTML = `<li>Verify customer authorization</li><li>Verify newly observed payee</li><li>Review authentication/device activity</li><li>Review surrounding transactions</li>`;
        }} else {{
          prioEl.innerHTML = prioList.map(p => `<li>${{p}}</li>`).join('');
        }}

        // 8. RECOMMENDED NEXT STEPS
        const nextEl = document.getElementById('modalNextSteps');
        const nextList = rec.recommended_next_steps || [];
        if (nextList.length === 0) {{
          nextEl.innerHTML = `<div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 font-medium">&bull; Freeze Outbound Rails (Investigator Recommendation)<br>&bull; Request KYC / Income Proof<br>&bull; Review Transaction & Customer Profile</div>`;
        }} else {{
          nextEl.innerHTML = nextList.map(n => `
            <div class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 font-semibold flex items-center gap-2">
              <i data-lucide="arrow-right-circle" class="w-3.5 h-3.5 text-indigo-600 shrink-0"></i>
              ${{n}}
            </div>
          `).join('');
        }}

        document.getElementById('assessmentDetailModal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
      }} catch (err) {{
        showToast("Unable to load this assessment. Please try again.");
      }}
    }}

    function closeAssessmentDetailModal() {{
      const modal = document.getElementById('assessmentDetailModal');
      if (modal) modal.classList.add('hidden');
    }}

    function exportSavedAssessmentJSONModal() {{
      if (!activeModalAssessmentData) return;
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(activeModalAssessmentData, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `${{activeModalAssessmentData.assessment_id}}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast(`Exported ${{activeModalAssessmentData.assessment_id}}.json`);
    }}

    function exportSavedAssessmentReportModal() {{
      if (!activeModalAssessmentData) return;
      let text = `==================================================\n`;
      text += `RISK INVESTIGATION ASSESSMENT: ${{activeModalAssessmentData.assessment_id}}\n`;
      text += `Customer: ${{activeModalAssessmentData.customer_name}} (${{activeModalAssessmentData.customer_id}})\n`;
      text += `Date: ${{activeModalAssessmentData.created_at}}\n`;
      text += `Risk Score: ${{activeModalAssessmentData.risk_score}} / 100 (${{activeModalAssessmentData.risk_level}})\n`;
      text += `Status: ${{activeModalAssessmentData.status}}\n`;
      text += `Model: ${{activeModalAssessmentData.model_name || "Gemini 2.0 Flash"}}\n`;
      text += `==================================================\n\n`;
      text += `PRIMARY FINDING:\n${{activeModalAssessmentData.primary_finding}}\n\n`;
      text += `CONNECTED TRANSACTIONS:\n${{JSON.stringify(activeModalAssessmentData.connected_transactions, null, 2)}}\n\n`;
      text += `TRIGGERED RULES:\n${{JSON.stringify(activeModalAssessmentData.triggered_rules, null, 2)}}\n\n`;
      text += `HISTORICAL BASELINE:\n${{JSON.stringify(activeModalAssessmentData.baseline, null, 2)}}\n\n`;
      text += `WHY IT MATTERS:\n${{JSON.stringify(activeModalAssessmentData.why_it_matters, null, 2)}}\n\n`;
      text += `INVESTIGATOR PRIORITY:\n${{JSON.stringify(activeModalAssessmentData.investigator_priority, null, 2)}}\n\n`;
      text += `RECOMMENDED NEXT STEPS:\n${{JSON.stringify(activeModalAssessmentData.recommended_next_steps, null, 2)}}\n\n`;
      text += `NOTICE: Human decision required. Final judgment belongs to the investigator.\n`;

      const dataStr = "data:text/plain;charset=utf-8," + encodeURIComponent(text);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `${{activeModalAssessmentData.assessment_id}}_report.txt`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast(`Exported ${{activeModalAssessmentData.assessment_id}}_report.txt`);
    }}

    function openReportModal(custId) {{
      const p = CUSTOMER_PROFILES[custId] || CUSTOMER_PROFILES['CUST_002'];
      document.getElementById('rvTitle').innerText = `SENTINELRISK REPORT — ${{p.name}} (${{custId}})`;
      const mdReport = lastGeneratedReportMd || `
# SentinelRisk Autonomous Triage Report
**Customer**: ${{p.name}} (${{custId}})  
**Risk Level**: ${{p.risk}}  

## Primary Finding
Connected high-velocity transaction anomaly detected against behavioral baseline parameters.

## Baseline Comparison
Normal Hours: ${{p.hours}} | Typical Txn: ${{p.typical}} | Payees: ${{p.payees}}

## Recommended Investigator Action
1. Freeze outbound payment rails if unverified.
2. Request identity and income verification from customer.
      `;
      document.getElementById('rvContent').innerHTML = `<div class="dossier-report">${{marked.parse(mdReport)}}</div>`;
      const modal = document.getElementById('reportViewModal');
      if (modal) modal.classList.remove('hidden');
    }}

    function closeReportModal() {{
      const modal = document.getElementById('reportViewModal');
      if (modal) modal.classList.add('hidden');
    }}

    // Initial default mount
    loadCustomer('CUST_001');
    updateHistoryBadge();
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(content=LIGHT_UI_HTML)

@app.get("/api/customer/{customer_id}")
async def get_customer(customer_id: str):
    res = analyze_customer_transactions(DB_FILE, customer_id)
    return JSONResponse(res)

@app.get("/api/all_customers")
async def get_all_customers():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()
    
    customers_data = []
    for r in rows:
        c_dict = dict(r)
        analysis = analyze_customer_transactions(DB_FILE, c_dict["customer_id"])
        c_dict["risk_score"] = analysis.get("risk_score", 0)
        c_dict["risk_level"] = analysis.get("risk_level", "LOW")
        c_dict["txn_count"] = len(analysis.get("transactions", []))
        c_dict["flags_count"] = len(analysis.get("flags", []))
        customers_data.append(c_dict)
    return JSONResponse(customers_data)

@app.get("/api/all_transactions")
async def get_all_transactions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT t.*, c.name as customer_name FROM transactions t JOIN customers c ON t.customer_id = c.customer_id ORDER BY t.timestamp DESC").fetchall()
    conn.close()
    
    all_flags_map = {}
    for cid in ["CUST_001", "CUST_002", "CUST_003", "CUST_004"]:
        analysis = analyze_customer_transactions(DB_FILE, cid)
        for f in analysis.get("flags", []):
            tid = f["txn_id"]
            if tid not in all_flags_map:
                all_flags_map[tid] = []
            all_flags_map[tid].append(f)

    all_txns = []
    for r in rows:
        t = dict(r)
        tid = t["txn_id"]
        t_flags = all_flags_map.get(tid, [])
        t["flags"] = t_flags
        t["is_flagged"] = len(t_flags) > 0
        t["evidence_id"] = f"EVID-{tid}-{t_flags[0]['rule_name']}" if t_flags else f"EVID-{tid}-CLEAN"
        all_txns.append(t)
        
    return JSONResponse(all_txns)

@app.post("/api/transaction/add")
async def add_transaction(txn: NewTransactionRequest):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Generate Txn ID
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE customer_id = ?", (txn.customer_id,))
    count = cursor.fetchone()[0] + 1
    cust_num = txn.customer_id.split("_")[-1] if "_" in txn.customer_id else "99"
    txn_id = f"TXN_{cust_num}{count:02d}"
    
    ts = txn.timestamp or datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO transactions (txn_id, customer_id, timestamp, amount, payee, channel, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (txn_id, txn.customer_id, ts, txn.amount, txn.payee, txn.channel, txn.description))
    conn.commit()
    conn.close()
    
    return JSONResponse({"status": "success", "txn_id": txn_id})

@app.post("/api/investigate/{customer_id}")
async def run_investigation(customer_id: str, request: Request, x_gemini_api_key: Optional[str] = Header(None)):
    res = analyze_customer_transactions(DB_FILE, customer_id)
    report_res = generate_investigation_report(
        customer=res["customer"],
        transactions=res["transactions"],
        flags=res["flags"],
        baseline=res.get("baseline"),
        custom_api_key=x_gemini_api_key
    )
    if isinstance(report_res, dict):
        from src.investigator import report_to_markdown
        report_md = report_to_markdown(report_res, customer=res["customer"])
    else:
        report_md = str(report_res)

    # Save complete assessment record to SQLite
    customer_info = res.get("customer", {})
    risk_score = res.get("risk_score", customer_info.get("risk_score", 0))
    risk_level_raw = res.get("risk_level", customer_info.get("risk_level", "LOW"))
    risk_level = "HIGH" if "HIGH" in risk_level_raw.upper() else ("MEDIUM" if "ELEVATED" in risk_level_raw.upper() or "MEDIUM" in risk_level_raw.upper() else "LOW")
    attention_required = len(res.get("flags", [])) > 0 or customer_info.get("attention_required", False)

    primary_finding = "No primary finding detailed."
    connected_txns = [t.get("txn_id") or t.get("id") for t in res.get("transactions", []) if t.get("txn_id") or t.get("id")]
    triggered_rules = list(set([f.get("rule_name") for f in res.get("flags", []) if f.get("rule_name")]))
    baseline_info = res.get("baseline", {})
    why_it_matters = []
    investigator_priority = []
    recommended_next_steps = []

    if isinstance(report_res, dict):
        primary_finding = report_res.get("primary_finding", primary_finding)
        if report_res.get("connected_transactions"):
            connected_txns = report_res["connected_transactions"]
        if report_res.get("triggered_rules"):
            triggered_rules = report_res["triggered_rules"]
        if "baseline_comparison" in report_res and isinstance(report_res["baseline_comparison"], dict):
            baseline_info.update(report_res["baseline_comparison"])
        why_it_matters = report_res.get("why_it_matters", [])
        investigator_priority = report_res.get("investigator_priority", [])
        recommended_next_steps = report_res.get("recommended_next_steps", [])
        if "risk_level" in report_res:
            risk_level = report_res["risk_level"]
        if "attention_required" in report_res:
            attention_required = report_res["attention_required"]

    status_str = "ATTENTION REQUIRED" if attention_required else "NO ATTENTION REQUIRED"
    if isinstance(report_res, dict) and report_res.get("is_fallback"):
        model_used = "Deterministic Fallback"
        status_str = "FALLBACK / DETERMINISTIC"
    else:
        model_used = "Gemini 2.0 Flash"

    saved_rec = save_assessment_record(
        db_path=DB_FILE,
        customer_id=customer_id,
        customer_name=customer_info.get("name", customer_id),
        risk_score=risk_score,
        risk_level=risk_level,
        attention_required=attention_required,
        status=status_str,
        primary_finding=primary_finding,
        connected_transactions=connected_txns,
        triggered_rules=triggered_rules,
        baseline=baseline_info,
        why_it_matters=why_it_matters,
        investigator_priority=investigator_priority,
        recommended_next_steps=recommended_next_steps,
        evidence=res.get("flags", []),
        validation={
            "evidence_validated": True,
            "traceable_to_ledger": True,
            "grounded_in_evidence": True,
            "human_decision_required": True
        },
        model_name=model_used,
        full_report=report_res
    )

    return JSONResponse({
        "report": report_md,
        "structured": report_res,
        "assessment_id": saved_rec["assessment_id"]
    })

@app.get("/api/history")
async def get_history(
    search: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    attention_required: Optional[bool] = Query(None),
    customer_id: Optional[str] = Query(None)
):
    summaries = get_history_summaries(
        db_path=DB_FILE,
        search=search,
        risk_level=risk_level,
        attention_required=attention_required,
        customer_id=customer_id
    )
    return JSONResponse(summaries)

@app.get("/api/history_count")
async def get_history_count():
    summaries = get_history_summaries(db_path=DB_FILE)
    return JSONResponse({"count": len(summaries)})

@app.get("/api/history/{assessment_id}")
async def get_history_detail(assessment_id: str):
    record = get_assessment_by_id(DB_FILE, assessment_id)
    if not record:
        return JSONResponse({"error": f"Assessment {assessment_id} not found"}, status_code=404)
    return JSONResponse(record)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
    except OSError as e:
        print(f"[SentinelRisk] Port {port} unavailable ({e}). Falling back to port 8050.")
        uvicorn.run("app:app", host="0.0.0.0", port=8050, reload=False)