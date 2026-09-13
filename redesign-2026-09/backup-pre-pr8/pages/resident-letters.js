// ──────────────────────────────────────────────────────────────
// Resident Letters — Good Standing & Income Verification
// Embedded into Agentic OS dashboard
// ──────────────────────────────────────────────────────────────

const LETTER_TYPES = [
  { id: 'good-standing', label: 'Letter of Good Standing', icon: '📋' },
  { id: 'income', label: 'Income Verification Letter', icon: '💰' },
];

async function renderResidentLetters() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">✉️ Resident Letters</h1>
        <p class="page-subtitle">Generate Good Standing & Income Verification letters from CRM data</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderResidentLetters()">🔄 Refresh</button>
      </div>
    </div>
    <div id="lettersContent" style="display:flex;flex-direction:column;gap:16px">Loading residents...</div>
  `;
  await loadLetterPage();
}

async function loadLetterPage() {
  try {
    const resp = await api.get('/api/crm/contacts');
    const contacts = resp.contacts || [];
    const residents = contacts.filter(c => c.category === 'Resident' && !c.archived)
      .sort((a, b) => (a.lastName || '').localeCompare(b.lastName || ''));
    renderLetterUI(residents);
  } catch (err) {
    document.getElementById('lettersContent').innerHTML =
      `<div class="card" style="padding:24px;text-align:center;color:var(--red)">
        ⚠️ Failed to load residents: ${escapeHtml(err.message)}
      </div>`;
  }
}

function renderLetterUI(residents) {
  const container = document.getElementById('lettersContent');
  if (!container) return;

  let html = '';

  // ── Letter Type Selection ──────────────────────────────
  html += `<div class="card" style="padding:16px 20px">
    <h3 style="margin:0 0 12px 0;font-size:14px">Letter Type</h3>
    <div style="display:flex;gap:12px">
      ${LETTER_TYPES.map(t => `
        <label style="flex:1;cursor:pointer">
          <input type="radio" name="letterType" value="${t.id}" ${t.id === 'good-standing' ? 'checked' : ''}
                 onchange="toggleLetterFields()" style="margin-right:6px">
          ${t.icon} ${t.label}
        </label>
      `).join('')}
    </div>
  </div>`;

  // ── Good Standing fields (shown only when that type is selected) ──
  html += `<div id="gsFields" class="card" style="padding:16px 20px">
    <h3 style="margin:0 0 12px 0;font-size:14px">Recipient Details</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div>
        <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px">Recipient Name *</label>
        <input id="gsRecipient" class="form-input" placeholder="Joel Sheinfeld" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--bg);color:var(--text)">
      </div>
      <div>
        <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px">Title</label>
        <input id="gsTitle" class="form-input" value="Dr." style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--bg);color:var(--text)">
      </div>
      <div style="grid-column:1/-1">
        <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px">Institution</label>
        <input id="gsInstitution" class="form-input" placeholder="Memorial Sloan Kettering Cancer Center" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--bg);color:var(--text)">
      </div>
    </div>
  </div>`;

  // ── Resident Selection ─────────────────────────────────
  html += `<div class="card" style="padding:16px 20px">
    <h3 style="margin:0 0 12px 0;font-size:14px">Select Resident</h3>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px">`;
  for (const r of residents) {
    const name = `${r.firstName || ''} ${r.lastName || ''}`.trim();
    const pgy = r.pgy || '?';
    html += `
      <label style="display:flex;align-items:center;padding:8px 12px;border:1px solid var(--border-color);border-radius:8px;cursor:pointer;gap:8px"
             onmouseover="this.style.borderColor='var(--accent)'" onmouseout="this.style.borderColor='var(--border-color)'">
        <input type="radio" name="residentId" value="${escapeHtml(r.id || '')}" data-name="${escapeHtml(name)}" data-pgy="${escapeHtml(pgy)}">
        <div>
          <div style="font-size:13px;font-weight:600">${escapeHtml(name)}</div>
          <div style="font-size:11px;color:var(--text-muted)">${escapeHtml(pgy)} &bull; ${escapeHtml(r.email || '')}</div>
        </div>
      </label>`;
  }
  html += `</div></div>`;

  // ── Generate Button ────────────────────────────────────
  html += `<div style="display:flex;gap:12px">
    <button class="btn" onclick="generateLetter()" style="flex:1;padding:14px;font-size:15px;font-weight:600">
      ✉️ Generate Letter
    </button>
    <button class="btn" onclick="previewLetter()" style="padding:14px 24px;font-size:15px">
      👁️ Preview
    </button>
  </div>`;

  // ── Result area ────────────────────────────────────────
  html += `<div id="letterResult" style="display:none;margin-top:16px"></div>`;

  container.innerHTML = html;
}

function toggleLetterFields() {
  const type = document.querySelector('input[name="letterType"]:checked')?.value;
  const gsFields = document.getElementById('gsFields');
  if (gsFields) gsFields.style.display = type === 'good-standing' ? '' : 'none';
}

function getSelectedResident() {
  const radio = document.querySelector('input[name="residentId"]:checked');
  if (!radio) return null;
  return {
    id: radio.value,
    name: radio.dataset.name,
    pgy: radio.dataset.pgy,
  };
}

async function generateLetter() {
  const resident = getSelectedResident();
  if (!resident) { showToast('⚠️ Please select a resident', 'error'); return; }

  const type = document.querySelector('input[name="letterType"]:checked')?.value;
  if (!type) { showToast('⚠️ Please select a letter type', 'error'); return; }

  let body = { resident_id: resident.id, type };

  if (type === 'good-standing') {
    const recipient = document.getElementById('gsRecipient')?.value.trim();
    if (!recipient) { showToast('⚠️ Recipient name is required', 'error'); return; }
    body.recipient = recipient;
    body.recipient_title = document.getElementById('gsTitle')?.value.trim() || 'Dr.';
    body.institution = document.getElementById('gsInstitution')?.value.trim() || '';
  }

  try {
    const resp = await api.post('/api/letters/generate', body);
    if (resp.success) {
      showToast('✅ Letter generated!', 'success');
      showLetterResult(resp);
    } else {
      showToast('⚠️ ' + (resp.error || 'Generation failed'), 'error');
    }
  } catch (err) {
    showToast('⚠️ Error: ' + err.message, 'error');
  }
}

async function previewLetter() {
  const resident = getSelectedResident();
  if (!resident) { showToast('⚠️ Please select a resident', 'error'); return; }

  const type = document.querySelector('input[name="letterType"]:checked')?.value;
  const params = new URLSearchParams({ resident_id: resident.id, type, preview: 'true' });

  if (type === 'good-standing') {
    params.set('recipient', document.getElementById('gsRecipient')?.value.trim() || '');
    params.set('recipient_title', document.getElementById('gsTitle')?.value.trim() || 'Dr.');
    params.set('institution', document.getElementById('gsInstitution')?.value.trim() || '');
  }

  window.open(`/api/letters/generate?${params}`, '_blank');
}

function showLetterResult(resp) {
  const div = document.getElementById('letterResult');
  div.style.display = 'block';
  div.innerHTML = `
    <div class="card" style="padding:16px 20px;background:#f0fdf4;border:1px solid #bbf7d0">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <strong style="color:#15803d">✅ Letter Generated</strong><br>
          <span style="font-size:12px;color:var(--text-muted)">${escapeHtml(resp.filename || '')}</span><br>
          <span style="font-size:11px;color:var(--text-muted)">${escapeHtml(resp.resident_name || '')} &bull; ${escapeHtml(resp.pgy || '')}${resp.salary ? ' &bull; ' + resp.salary : ''}</span>
        </div>
        <div style="display:flex;gap:8px">
          <a href="${resp.download_url || '#'}" class="btn btn-sm" download>⬇ Download</a>
          <button class="btn btn-sm" onclick="window.open('${resp.download_url || '#'}', '_blank')">📄 Open</button>
        </div>
      </div>
    </div>`;
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
