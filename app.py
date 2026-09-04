import os
import sqlite3
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from data.seed_data import init_db
from src.rules import analyze_customer_transactions
from src.investigator import generate_investigation_report, VALIDATION_KEY
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="SentinelRisk - GCC Banking Investigation Desk")

DB_FILE = "transactions.db"
init_db(DB_FILE)

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

        <!-- Sidebar Navigation Menu Links -->
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
          <a href="#" onclick="navTab('Alerts')" id="nav-Alerts" class="sidebar-item flex items-center justify-between px-3.5 py-2.5 rounded-xl hover:bg-slate-50 hover:text-slate-900 transition">
            <span class="flex items-center gap-3"><i data-lucide="bell" class="w-4 h-4 text-slate-400"></i> Alerts</span>
            <span class="h-2 w-2 rounded-full bg-rose-500"></span>
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
        <div class="w-12 h-12 mx-auto mb-1 relative flex items-center justify-center">
          <i data-lucide="shield-check" class="w-8 h-8 text-indigo-600"></i>
        </div>
        <p class="text-xs font-extrabold text-slate-900">Security. Intelligence.</p>
        <p class="text-[11px] text-indigo-600 font-semibold mt-0.5">Trust.</p>
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
                    <button id="exportMdBtn" onclick="exportReportMd()" disabled class="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed transition" title="Export Markdown Report">
                      <i data-lucide="file-text" class="w-3.5 h-3.5 text-slate-500"></i> Export
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
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex justify-between items-center">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="search" class="w-5 h-5 text-indigo-600"></i> Investigation Workspace
            </h2>
            <p class="text-xs text-slate-500 mt-1">Active case triage queue for fraud investigators.</p>
          </div>
          <button onclick="loadCustomer('CUST_002'); navTab('Dashboard');" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md">
            Open Active Case (CUST_002)
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div onclick="loadCustomer('CUST_001'); navTab('Dashboard');" class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs cursor-pointer hover:border-indigo-400 transition">
            <div class="flex justify-between items-center mb-2">
              <span class="font-bold text-slate-900">CUST_001 - Priya Sharma</span>
              <span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">Routine</span>
            </div>
            <p class="text-xs text-slate-500">Salaried professional, standard monthly utility & grocery spend.</p>
          </div>
          <div onclick="loadCustomer('CUST_002'); navTab('Dashboard');" class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs cursor-pointer hover:border-indigo-400 transition">
            <div class="flex justify-between items-center mb-2">
              <span class="font-bold text-slate-900">CUST_002 - Vikram Rathore</span>
              <span class="px-2 py-0.5 text-[10px] font-bold bg-rose-50 text-rose-700 rounded-full border border-rose-200">High Risk</span>
            </div>
            <p class="text-xs text-slate-500">Account takeover style 3:00 AM velocity burst to new payee.</p>
          </div>
          <div onclick="loadCustomer('CUST_003'); navTab('Dashboard');" class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs cursor-pointer hover:border-indigo-400 transition">
            <div class="flex justify-between items-center mb-2">
              <span class="font-bold text-slate-900">CUST_003 - Ananya Sen</span>
              <span class="px-2 py-0.5 text-[10px] font-bold bg-amber-50 text-amber-700 rounded-full border border-amber-200">Structuring</span>
            </div>
            <p class="text-xs text-slate-500">Multiple transfers in ₹49,900 range right below threshold.</p>
          </div>
        </div>
      </div>

      <!-- VIEW 3: CUSTOMERS DIRECTORY VIEW -->
      <div id="view-Customers" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs">
          <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2 mb-1">
            <i data-lucide="users" class="w-5 h-5 text-indigo-600"></i> Customer Directory
          </h2>
          <p class="text-xs text-slate-500">Manage mounted banking profiles and risk baselines.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-3">
            <div class="h-10 w-10 rounded-full bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold">PS</div>
            <h3 class="font-bold text-slate-900">Priya Sharma</h3>
            <p class="text-xs text-slate-500">Savings Account (CUST_001)</p>
            <button onclick="loadCustomer('CUST_001'); navTab('Dashboard');" class="w-full py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-xl text-xs">Mount & Inspect</button>
          </div>
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-3">
            <div class="h-10 w-10 rounded-full bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold">VR</div>
            <h3 class="font-bold text-slate-900">Vikram Rathore</h3>
            <p class="text-xs text-slate-500">Current Account (CUST_002)</p>
            <button onclick="loadCustomer('CUST_002'); navTab('Dashboard');" class="w-full py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-xl text-xs">Mount & Inspect</button>
          </div>
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-3">
            <div class="h-10 w-10 rounded-full bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold">AS</div>
            <h3 class="font-bold text-slate-900">Ananya Sen</h3>
            <p class="text-xs text-slate-500">Savings Account (CUST_003)</p>
            <button onclick="loadCustomer('CUST_003'); navTab('Dashboard');" class="w-full py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-xl text-xs">Mount & Inspect</button>
          </div>
          <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs space-y-3">
            <div class="h-10 w-10 rounded-full bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold">AM</div>
            <h3 class="font-bold text-slate-900">Arjun Mehta</h3>
            <p class="text-xs text-slate-500">HNI Wealth (CUST_004)</p>
            <button onclick="loadCustomer('CUST_004'); navTab('Dashboard');" class="w-full py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-xl text-xs">Mount & Inspect</button>
          </div>
        </div>
      </div>

      <!-- VIEW 4: FULL TRANSACTIONS VIEW -->
      <div id="view-Transactions" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex justify-between items-center">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="credit-card" class="w-5 h-5 text-indigo-600"></i> Full Transaction Ledger
            </h2>
            <p class="text-xs text-slate-500 mt-1">Audit log across all mounted banking accounts.</p>
          </div>
          <button onclick="openTxnModal()" class="px-4 py-2 bg-slate-900 text-white font-bold rounded-xl text-xs">
            + Inject Sandbox Txn
          </button>
        </div>
      </div>

      <!-- VIEW 5: ALERTS FEED VIEW -->
      <div id="view-Alerts" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs">
          <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2 mb-1">
            <i data-lucide="bell" class="w-5 h-5 text-rose-600"></i> Active Risk Alerts Feed
          </h2>
          <p class="text-xs text-slate-500">Real-time risk rule trigger notifications.</p>
        </div>
      </div>

      <!-- VIEW 6: REPORTS VIEW -->
      <div id="view-Reports" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs">
          <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2 mb-1">
            <i data-lucide="bar-chart-3" class="w-5 h-5 text-indigo-600"></i> Compliance Reports Library
          </h2>
          <p class="text-xs text-slate-500">Generated investigation reports and audit archives.</p>
        </div>
      </div>

      <!-- VIEW 7: AUDIT LOGS VIEW -->
      <div id="view-Audit Logs" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex justify-between items-center">
          <div>
            <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <i data-lucide="file-check-2" class="w-5 h-5 text-indigo-600"></i> System Audit Logs
            </h2>
            <p class="text-xs text-slate-500 mt-1">Immutable audit trail of all deterministic rule scans and GenAI reports.</p>
          </div>
          <button onclick="exportAuditJSON()" class="px-4 py-2 bg-indigo-600 text-white font-bold rounded-xl text-xs">
            Export Audit JSON
          </button>
        </div>
      </div>

      <!-- VIEW 8: SETTINGS VIEW -->
      <div id="view-Settings" class="view-panel hidden flex-1 p-6 max-w-[1850px] w-full mx-auto space-y-6">
        <div class="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs">
          <h2 class="text-lg font-extrabold text-slate-900 flex items-center gap-2 mb-1">
            <i data-lucide="settings" class="w-5 h-5 text-indigo-600"></i> System Settings
          </h2>
          <p class="text-xs text-slate-500">API keys, validation parameters, and model configurations.</p>
          <button onclick="openKeyModal()" class="mt-4 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl text-xs">
            Configure Gemini API Key
          </button>
        </div>
      </div>

      <!-- Footer Bar -->
      <footer class="h-12 border-t border-slate-200/80 bg-white px-6 flex items-center justify-between text-xs text-slate-400 font-medium">
        <div>© 2026 SentinelRisk Copilot</div>
        <div class="hidden sm:block">Built for secure, explainable, and autonomous financial risk intelligence.</div>
        <div class="flex items-center gap-1 text-indigo-600 font-semibold">
          Powered by Gemini 2.0 Flash <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
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

    function exportAuditJSON() {{
      if (!currentAuditData) {{
        showToast("No active data loaded to export.");
        return;
      }}
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentAuditData, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `audit_${{activeCustomerId}}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast("Audit JSON exported successfully.");
    }}

    function exportReportMd() {{
      if (!lastGeneratedReportMd) {{
        showToast("Run investigation assessment first to export report.");
        return;
      }}
      const dataStr = "data:text/markdown;charset=utf-8," + encodeURIComponent(lastGeneratedReportMd);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `investigation_report_${{activeCustomerId}}.md`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast("Report exported as Markdown.");
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

      // Calculate Risk Scores
      let oddScore = 0, velScore = 0, devScore = 0, structScore = 0;
      data.flags.forEach(f => {{
        if (f.rule_name.includes('ODD_HOURS')) oddScore += 20;
        if (f.rule_name.includes('VELOCITY')) velScore += 35;
        if (f.rule_name.includes('BASELINE')) devScore += 25;
        if (f.rule_name.includes('STRUCTURING') || f.rule_name.includes('NEW_PAYEE')) structScore += 30;
      }});

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
      }} catch (err) {{
        reportBox.innerHTML = `<div class="text-rose-700 p-4 border border-rose-200 bg-rose-50 rounded-xl">Error generating report: ${{err.message}}</div>`;
      }} finally {{
        loader.classList.add('hidden');
        btn.disabled = false;
        lucide.createIcons();
      }}
    }}

    // Initial default mount
    loadCustomer('CUST_001');
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(content=LIGHT_UI_HTML)

@app.get("/api/customer/{customer_id}")
async def get_customer(customer_id: str):
    customer, txns, flags = analyze_customer_transactions(DB_FILE, customer_id)
    return JSONResponse({"customer": customer, "transactions": txns, "flags": flags})

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
    customer, txns, flags = analyze_customer_transactions(DB_FILE, customer_id)
    report = generate_investigation_report(customer, txns, flags, custom_api_key=x_gemini_api_key)
    return JSONResponse({"report": report})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
    except OSError as e:
        print(f"[SentinelRisk] Port {port} unavailable ({e}). Falling back to port 8050.")
        uvicorn.run("app:app", host="0.0.0.0", port=8050, reload=False)