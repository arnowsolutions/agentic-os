async function renderReports() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Report Center</h1>
        <p class="page-subtitle">Generate & deliver reports</p>
      </div>
    </div>
    <div class="card mb-3">
      <div class="card-header"><span class="card-title">Generate a Report</span></div>
      <div style="padding:20px">
        <div class="form-group">
          <label class="form-label">Report Type</label>
          <select id="reportType" class="form-select">
            <option value="">Loading...</option>
          </select>
        </div>
        <div class="form-group" id="inputGroup" style="display:none">
          <label class="form-label">Input / Topic (optional)</label>
          <textarea id="reportInput" class="form-input" rows="3" placeholder="Optional input for the skill report"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Delivery Channel</label>
          <select id="reportChannel" class="form-select">
            <option value="download">Download</option>
            <option value="email">Email</option>
          </select>
        </div>
        <div class="form-group" id="recipientGroup" style="display:none">
          <label class="form-label">Recipient Email</label>
          <input id="reportRecipient" class="form-input" type="email" placeholder="recipient@example.com">
        </div>
        <button class="btn btn-primary" onclick="generateReport()">Generate Report</button>
      </div>
    </div>
    <div class="card" id="reportResultCard" style="display:none">
      <div class="card-header"><span class="card-title">Report Result</span></div>
      <div id="reportResult" style="padding:20px"><div class="loading"><div class="loading-spinner"></div></div></div>
    </div>
  `;

  // Load report types
  try {
    const types = await api.getReportTypes();
    const select = document.getElementById('reportType');
    select.innerHTML = '<option value="">Select a report type...</option>'
      + types.map(t => `<option value="${t.id}" data-kind="${t.kind}" data-supports-pdf="${t.supports_pdf}">${escapeHtml(t.label)}</option>`).join('');
  } catch (err) {
    document.getElementById('reportType').innerHTML = `<option value="">Error loading: ${escapeHtml(err.message)}</option>`;
  }

  // Show/hide recipient field based on channel
  document.getElementById('reportChannel').addEventListener('change', toggleRecipientField);
  document.getElementById('reportType').addEventListener('change', toggleInputField);
}

function toggleRecipientField() {
  const channel = document.getElementById('reportChannel').value;
  document.getElementById('recipientGroup').style.display = channel === 'email' ? 'block' : 'none';
}

function toggleInputField() {
  const select = document.getElementById('reportType');
  const option = select.options[select.selectedIndex];
  const kind = option ? option.dataset.kind : '';
  document.getElementById('inputGroup').style.display = kind === 'skill' ? 'block' : 'none';
}

async function generateReport() {
  const type = document.getElementById('reportType').value;
  if (!type) { showToast('Please select a report type', 'warning'); return; }

  const channel = document.getElementById('reportChannel').value;
  const input = document.getElementById('reportInput')?.value || '';
  const recipient = document.getElementById('reportRecipient')?.value || '';

  if (channel === 'email' && !recipient) { showToast('Please enter a recipient email', 'warning'); return; }

  const resultCard = document.getElementById('reportResultCard');
  const resultDiv = document.getElementById('reportResult');
  resultCard.style.display = 'block';
  resultDiv.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

  try {
    const data = await api.generateReport({ type, input, channel, recipient });

    if (data.content) {
      // Text/HTML content response (download)
      resultDiv.innerHTML = `
        <div style="margin-bottom:12px">
          <span class="badge badge-success">${escapeHtml(data.message || 'Generated')}</span>
        </div>
        <pre style="white-space:pre-wrap;font-size:13px;line-height:1.6;background:var(--bg-input);padding:16px;border-radius:6px;max-height:500px;overflow:auto">${escapeHtml(data.content)}</pre>
      `;
    } else {
      // Email / status response
      resultDiv.innerHTML = `
        <div style="padding:20px;text-align:center">
          <div style="font-size:40px;margin-bottom:12px">${data.status === 'success' ? '✅' : '⚠️'}</div>
          <div style="font-size:15px;font-weight:600;margin-bottom:4px">${escapeHtml(data.message || 'Done')}</div>
        </div>
      `;
    }
    showToast(data.message || 'Report generated', data.status === 'success' ? 'success' : 'info');
  } catch (err) {
    resultDiv.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠</div>
        <div class="empty-state-title">${escapeHtml(err.message)}</div>
      </div>
    `;
    showToast(`Error: ${err.message}`, 'error');
  }
}
