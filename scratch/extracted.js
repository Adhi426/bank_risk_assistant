
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
        const txt = currentAuditData.transactions.map(t => `${{t.txn_id}} | ${{t.timestamp}} | ${{t.payee}} | ₹${{t.amount}}`).join('\n');
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

        // Save to Assessment History
        const scoreVal = parseInt(document.getElementById('scoreNum').innerText || '0', 10);
        const verdictVal = document.getElementById('riskVerdict').innerText || 'LOW RISK';
        saveAssessmentHistoryItem({{
          id: 'HIST_' + Date.now(),
          timestamp: new Date().toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }}) + ', ' + new Date().toLocaleDateString(),
          customerId: activeCustomerId,
          customerName: currentAuditData ? currentAuditData.customer.name : activeCustomerId,
          riskScore: scoreVal,
          riskLevel: verdictVal,
          reportMd: data.report,
          flagsCount: currentAuditData ? currentAuditData.flags.length : 0
        }});
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
  