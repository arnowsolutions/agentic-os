// ──────────────────────────────────────────────────────────────
// Resident Letters — Good Standing, Income Verification
//                  + ABU Chief Resident Confirmation (annual)
// Embedded into Agentic OS dashboard
//
// The first two letters are rendered from HTML templates. The ABU chief letter
// is NOT: it fills the department's own Word letterhead file (letterhead banner
// and Dr. Sankin's signature already in it) via letterhead_letters.py, so the
// letterhead is never reproduced by hand. Required from every chief each year
// the ABU opens the Qualifying (Part 1) Examination cycle.
// ──────────────────────────────────────────────────────────────

const LETTER_TYPES = [
  { id: 'good-standing', label: 'Letter of Good Standing', icon: '▸' },
  { id: 'income', label: 'Income Verification Letter', icon: '▸' },
  { id: 'abu-chief', label: 'ABU Chief Resident Confirmation (annual)', icon: '▸' },
];

async function renderResidentLetters() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Resident Letters</h1>
        <p class="page-subtitle">Good Standing &amp; Income Verification letters, plus the annual ABU chief-resident confirmation on department letterhead</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderResidentLetters()">↻ Refresh</button>
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
    loadChiefCohort();
  } catch (err) {
    document.getElementById('lettersContent').innerHTML =
      `<div class="card" style="padding:24px;text-align:center;color:var(--red)">
        ! Failed to load residents: ${escapeHtml(err.message)}
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
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      ${LETTER_TYPES.map(t => `
        <label style="flex:1;min-width:220px;cursor:pointer">
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

  // ── ABU chief-resident panel (hidden until that type is selected) ──
  html += `<div id="chiefFields" class="card" style="padding:16px 20px;display:none">
    <h3 style="margin:0 0 4px 0;font-size:14px">ABU Chief Resident Confirmation &mdash; annual batch</h3>
    <p style="font-size:12px;color:var(--text-muted);margin:0 0 12px 0">
      One letter per chief resident, on department letterhead with Dr. Sankin's signature already in place.
      The Board needs it in its office by January 1 of the exam year; the Program Director's Evaluation
      Form is due March 1.
    </p>
    <div style="display:grid;grid-template-columns:180px 1fr;gap:12px;align-items:start">
      <div>
        <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px">Exam year</label>
        <select id="chiefYear" class="form-input" onchange="loadChiefCohort()"
                style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--bg);color:var(--text)"></select>
      </div>
      <div>
        <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px">Chiefs in this cohort (from the roster)</label>
        <div id="chiefRoster" style="font-size:13px;color:var(--text-muted)">Loading...</div>
      </div>
    </div>
  </div>`;

  // ── Resident Selection ─────────────────────────────────
  html += `<div id="residentPicker" class="card" style="padding:16px 20px">
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
      Generate Letter
    </button>
    <button class="btn" onclick="previewLetter()" style="padding:14px 24px;font-size:15px">
      Preview
    </button>
  </div>`;

  // ── Result area ────────────────────────────────────────
  html += `<div id="letterResult" style="display:none;margin-top:16px"></div>`;

  container.innerHTML = html;
}

function currentLetterType() {
  return document.querySelector('input[name="letterType"]:checked')?.value;
}

function toggleLetterFields() {
  const type = currentLetterType();
  const gsFields = document.getElementById('gsFields');
  const chiefFields = document.getElementById('chiefFields');
  const picker = document.getElementById('residentPicker');
  if (gsFields) gsFields.style.display = type === 'good-standing' ? '' : 'none';
  if (chiefFields) chiefFields.style.display = type === 'abu-chief' ? '' : 'none';
  // the ABU letter goes to the whole chief cohort, so per-resident picking is moot
  if (picker) picker.style.display = type === 'abu-chief' ? 'none' : '';
  const previewBtn = document.querySelector('button[onclick="previewLetter()"]');
  if (previewBtn) previewBtn.style.display = type === 'abu-chief' ? 'none' : '';
  if (type === 'abu-chief') loadChiefCohort();
}

async function loadChiefCohort() {
  const rosterEl = document.getElementById('chiefRoster');
  const yearEl = document.getElementById('chiefYear');
  if (!rosterEl || !yearEl) return;
  try {
    const resp = await api.get('/api/letters/chief/roster');
    const years = resp.years || [];
    if (!years.length) {
      rosterEl.innerHTML = '<em>No chief-resident records found.</em>';
      return;
    }
    if (!yearEl.options.length) {
      yearEl.innerHTML = years.map(y =>
        `<option value="${y}" ${y === resp.exam_year ? 'selected' : ''}>${y}</option>`).join('');
    }
    const year = yearEl.value || resp.exam_year;
    const r2 = await api.get(`/api/letters/chief/roster?exam_year=${encodeURIComponent(year)}`);
    const chiefs = r2.chiefs || [];
    rosterEl.innerHTML = chiefs.length
      ? chiefs.map(c => `<div style="padding:3px 0">
            <strong style="color:var(--text)">${escapeHtml(c.name)}, MD</strong>
            <span style="color:var(--text-muted)">&bull; ${escapeHtml(c.pgy || '')} &bull; completes June 30, ${escapeHtml(String(c.exam_year || ''))}</span>
          </div>`).join('')
      : '<em>No chiefs found for this year.</em>';
  } catch (err) {
    rosterEl.innerHTML = `<em>Could not load roster: ${escapeHtml(err.message)}</em>`;
  }
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
  const type = currentLetterType();
  if (!type) { showToast('! Please select a letter type', 'error'); return; }

  // ── ABU chief letter: annual batch, one per chief ──
  if (type === 'abu-chief') {
    const exam_year = document.getElementById('chiefYear')?.value;
    try {
      const resp = await api.post('/api/letters/chief/generate', { exam_year });
      if (resp.success) {
        showToast(`✓ ${resp.count} letter(s) generated`, 'success');
        showChiefResults(resp);
      } else {
        showToast('! ' + (resp.error || 'Generation failed'), 'error');
      }
    } catch (err) {
      showToast('! Error: ' + err.message, 'error');
    }
    return;
  }

  const resident = getSelectedResident();
  if (!resident) { showToast('! Please select a resident', 'error'); return; }

  let body = { resident_id: resident.id, type };

  if (type === 'good-standing') {
    const recipient = document.getElementById('gsRecipient')?.value.trim();
    if (!recipient) { showToast('! Recipient name is required', 'error'); return; }
    body.recipient = recipient;
    body.recipient_title = document.getElementById('gsTitle')?.value.trim() || 'Dr.';
    body.institution = document.getElementById('gsInstitution')?.value.trim() || '';
  }

  try {
    const resp = await api.post('/api/letters/generate', body);
    if (resp.success) {
      showToast('✓ Letter generated!', 'success');
      showLetterResult(resp);
    } else {
      showToast('! ' + (resp.error || 'Generation failed'), 'error');
    }
  } catch (err) {
    showToast('! Error: ' + err.message, 'error');
  }
}

function showChiefResults(resp) {
  const div = document.getElementById('letterResult');
  div.style.display = 'block';
  const rows = (resp.letters || []).map(l => `
    <tr>
      <td style="padding:8px 10px;border-bottom:1px solid var(--border-color)">
        <strong>${escapeHtml(l.name)}, MD</strong>
        <div style="font-size:11px;color:var(--text-muted)">${escapeHtml(l.pgy || '')} &bull; completes June 30, ${escapeHtml(String(l.exam_year || ''))}</div>
      </td>
      <td style="padding:8px 10px;border-bottom:1px solid var(--border-color);font-size:11px;color:var(--text-muted)">${escapeHtml(l.file || '')}</td>
      <td style="padding:8px 10px;border-bottom:1px solid var(--border-color);white-space:nowrap">
        <a href="${l.download_url}" class="btn btn-sm" download>↓ Download</a>
      </td>
    </tr>`).join('');
  div.innerHTML = `
    <div class="card" style="padding:16px 20px;background:#f0fdf4;border:1px solid #bbf7d0">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div>
          <strong style="color:#15803d">✓ ${resp.count} ABU chief-resident letter(s) generated</strong><br>
          <span style="font-size:12px;color:var(--text-muted)">
            Exam year ${escapeHtml(String(resp.exam_year || ''))} &bull; department letterhead + signature already in place
          </span>
        </div>
      </div>
      <table style="width:100%;border-collapse:collapse;margin-top:12px">${rows}</table>
      <div style="font-size:11px;color:var(--text-muted);margin-top:10px">
        Sent to the Board office by January 1, ${escapeHtml(String(resp.exam_year || ''))};
        Program Director's Evaluation Form due March 1, ${escapeHtml(String(resp.exam_year || ''))}.
      </div>
    </div>`;
}

async function previewLetter() {
  const resident = getSelectedResident();
  if (!resident) { showToast('! Please select a resident', 'error'); return; }

  const type = currentLetterType();
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
          <strong style="color:#15803d">✓ Letter Generated</strong><br>
          <span style="font-size:12px;color:var(--text-muted)">${escapeHtml(resp.filename || '')}</span><br>
          <span style="font-size:11px;color:var(--text-muted)">${escapeHtml(resp.resident_name || '')} &bull; ${escapeHtml(resp.pgy || '')}${resp.salary ? ' &bull; ' + resp.salary : ''}</span>
        </div>
        <div style="display:flex;gap:8px">
          <a href="${resp.download_url || '#'}" class="btn btn-sm" download>↓ Download</a>
          <button class="btn btn-sm" onclick="window.open('${resp.download_url || '#'}', '_blank')">Open</button>
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
