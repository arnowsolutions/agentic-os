async function renderCallSchedulePdf() {
  const content = document.getElementById('pageContent');
  
  const presetEmails = [
    'sfrasier@montefiore.org',
    'urologyresidencyprogram@gmail.com',
    'kelliaibel@gmail.com',
  ];

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">📄 Call Schedule PDF Generator</div>
        <div class="page-subtitle">Generate, preview, and email the call schedule PDF</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderCallSchedulePdf()">🔄 Reset</button>
      </div>
    </div>
    <div class="csp-grid">
      <div class="csp-card">
        <div class="csp-card-header">
          <span class="csp-card-icon">📋</span>
          <span class="csp-card-title">Generate PDF</span>
        </div>
        <div class="csp-card-body">
          <div style="margin-bottom:12px">
            <label style="font-size:12px;font-weight:500;display:block;margin-bottom:4px;color:var(--text-muted)">Period</label>
            <select id="cspPeriod" class="csp-select">
              <option value="Q3-Q4 2026">Q3-Q4 2026</option>
              <option value="Q1-Q2 2026">Q1-Q2 2026</option>
              <option value="Custom">Custom Range</option>
            </select>
          </div>
          <div style="margin-bottom:12px">
            <label style="font-size:12px;font-weight:500;display:block;margin-bottom:4px;color:var(--text-muted)">Include</label>
            <label class="csp-check"><input type="checkbox" id="cspNavyHeader" checked> Navy header branding</label>
            <label class="csp-check"><input type="checkbox" id="cspChiefCall" checked> Chief / 1st / 2nd Call columns</label>
            <label class="csp-check"><input type="checkbox" id="cspPGYLabels" checked> PGY level labels</label>
          </div>
          <button class="btn btn-primary" onclick="generateCspPdf()" style="width:100%">
            ⚡ Generate PDF
          </button>
        </div>
      </div>

      <div class="csp-card">
        <div class="csp-card-header">
          <span class="csp-card-icon">📧</span>
          <span class="csp-card-title">Email PDF</span>
        </div>
        <div class="csp-card-body">
          <div style="margin-bottom:12px">
            <label style="font-size:12px;font-weight:500;display:block;margin-bottom:4px;color:var(--text-muted)">Recipient</label>
            <select id="cspEmailSelect" class="csp-select" onchange="toggleCspCustomEmail()">
              ${presetEmails.map(e => `<option value="${e}">${e}</option>`).join('')}
              <option value="custom">Custom email...</option>
            </select>
          </div>
          <div id="cspCustomEmailRow" style="display:none;margin-bottom:12px">
            <input type="email" id="cspCustomEmail" class="csp-select" placeholder="Enter email address...">
          </div>
          <div style="margin-bottom:12px">
            <label style="font-size:12px;font-weight:500;display:block;margin-bottom:4px;color:var(--text-muted)">Subject</label>
            <input type="text" id="cspSubject" class="csp-select" value="Urology Call Schedule — Q3-Q4 2026">
          </div>
          <button class="btn btn-primary" onclick="emailCspPdf()" style="width:100%" id="cspEmailBtn">
            📤 Generate & Email
          </button>
        </div>
      </div>
    </div>

    <div id="cspResult" style="display:none;margin-top:16px;background:var(--bg-card);border-radius:var(--radius-md);border:1px solid var(--border);padding:16px">
      <div style="display:flex;justify-content:space-between;align-items:start">
        <div>
          <div id="cspResultIcon" style="font-size:20px;margin-bottom:4px">✅</div>
          <div id="cspResultTitle" style="font-size:14px;font-weight:600">PDF Generated</div>
          <div id="cspResultBody" style="font-size:12px;color:var(--text-muted);margin-top:4px;white-space:pre-wrap"></div>
        </div>
        <button class="btn btn-ghost btn-sm" onclick="document.getElementById('cspResult').style.display='none'">✕</button>
      </div>
      <pre id="cspResultOutput" style="margin-top:8px;padding:8px;background:rgba(0,0,0,0.2);border-radius:4px;font-size:11px;max-height:200px;overflow-y:auto;white-space:pre-wrap"></pre>
    </div>
    <style>
      .csp-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:12px; margin-top:16px; }
      .csp-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:0; overflow:hidden; }
      .csp-card-header { padding:14px 16px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:8px; }
      .csp-card-icon { font-size:18px; }
      .csp-card-title { font-size:14px; font-weight:600; }
      .csp-card-body { padding:16px; }
      .csp-select { width:100%; padding:8px 10px; border:1px solid var(--border); border-radius:6px; background:var(--bg); color:var(--text); font-size:13px; }
      .csp-check { display:flex; align-items:center; gap:6px; font-size:12px; padding:4px 0; cursor:pointer; }
      .csp-check input { accent-color:#6c5ce7; }
    </style>
  `;
}

function toggleCspCustomEmail() {
  const val = document.getElementById('cspEmailSelect').value;
  document.getElementById('cspCustomEmailRow').style.display = val === 'custom' ? 'block' : 'none';
}

async function generateCspPdf() {
  await runCspAction('generate');
}

async function emailCspPdf() {
  await runCspAction('email');
}

async function runCspAction(mode) {
  const resultDiv = document.getElementById('cspResult');
  const resultIcon = document.getElementById('cspResultIcon');
  const resultTitle = document.getElementById('cspResultTitle');
  const resultBody = document.getElementById('cspResultBody');
  const resultOutput = document.getElementById('cspResultOutput');
  
  resultDiv.style.display = 'block';
  resultIcon.textContent = '⏳';
  resultTitle.textContent = mode === 'generate' ? 'Generating PDF...' : 'Generating & emailing...';
  resultBody.textContent = 'Running call schedule script...';
  resultOutput.textContent = '';

  const emailSelect = document.getElementById('cspEmailSelect');
  const email = emailSelect.value === 'custom' 
    ? document.getElementById('cspCustomEmail').value 
    : emailSelect.value;
  const period = document.getElementById('cspPeriod').value;
  const subject = document.getElementById('cspSubject').value;
  const options = {
    navy_header: document.getElementById('cspNavyHeader').checked,
    chief_call: document.getElementById('cspChiefCall').checked,
    pgy_labels: document.getElementById('cspPGYLabels').checked,
  };

  try {
    const res = await fetch('/api/call-schedule/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, email, period, subject, options })
    });
    const data = await res.json();
    
    if (data.success) {
      resultIcon.textContent = '✅';
      resultTitle.textContent = mode === 'generate' ? 'PDF Generated' : 'PDF Generated & Emailed';
      resultBody.textContent = data.message || 'Completed successfully';
      resultOutput.textContent = data.output || '';
      showToast('Call schedule ' + (mode === 'generate' ? 'PDF generated' : 'sent'), 'success');
    } else {
      resultIcon.textContent = '❌';
      resultTitle.textContent = 'Failed';
      resultBody.textContent = data.error || 'Unknown error';
      resultOutput.textContent = data.output || '';
    }
  } catch (err) {
    resultIcon.textContent = '❌';
    resultTitle.textContent = 'Error';
    resultBody.textContent = err.message;
    resultOutput.textContent = '';
  }
}
