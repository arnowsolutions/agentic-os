async function renderGmeTracker() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">💰 GME Reimbursement Tracker</h1>
        <p class="page-subtitle">Track resident education fund usage — $1,250 annual limit per resident</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderGmeTracker()">🔄 Refresh</button>
      </div>
    </div>
    <div id="gmeSummaryCards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px"></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center" id="gmeFilterBar">
      <span style="font-size:12px;color:var(--text-muted);margin-right:4px">Academic Year:</span>
      <select id="gmeAySelector" style="padding:4px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg-card);color:var(--text);font-size:12px" onchange="loadGmeData()">
        <option value="2025-26" selected>2025-26 (Current)</option>
        <option value="2024-25">2024-25</option>
        <option value="2023-24">2023-24</option>
        <option value="all">All-Time</option>
      </select>
      <span style="flex:1"></span>
      <button class="tag gme-filter-btn" style="cursor:pointer;padding:3px 12px;font-size:12px" data-filter="" onclick="filterGmeResidents('')">All</button>
      <button class="tag gme-filter-btn" style="cursor:pointer;padding:3px 12px;font-size:12px" data-filter="has-funds" onclick="filterGmeResidents('has-funds')">Has Funds</button>
      <button class="tag gme-filter-btn" style="cursor:pointer;padding:3px 12px;font-size:12px" data-filter="exhausted" onclick="filterGmeResidents('exhausted')">Exhausted</button>
    </div>
    <div id="gmeResidentCards"></div>
  `;
  document.querySelectorAll('.gme-filter-btn').forEach(el => {
    if (el.dataset.filter === 'has-funds') el.style.borderColor = 'var(--accent)';
    else el.style.borderColor = '';
  });
  loadGmeData();
}

let gmeResidents = [];
let gmeSummary = {};
let expandedResident = null;

async function loadGmeData() {
  try {
    const ay = document.getElementById('gmeAySelector')?.value || '2025-26';
    const [summary, residents] = await Promise.all([
      api.getGmeSummary(ay),
      api.getGmeResidents(ay)
    ]);
    gmeSummary = summary;
    // Also load all-AY data for the breakdown tabs
    const allAyResidents = ay === 'all' ? residents : await api.getGmeResidents('all');
    
    // Store all AYs per resident for tabs
    if (ay !== 'all') {
      const allData = allAyResidents.residents || [];
      const ayMap = {};
      for (const r of allData) {
        const key = r.id || `${r.firstName || ''}_${r.lastName || ''}`;
        ayMap[key] = r;
      }
      for (const r of residents.residents || []) {
        const key = r.id || `${r.firstName || ''}_${r.lastName || ''}`;
        r._allAyData = ayMap[key];
      }
    }
    
    gmeResidents = residents.residents || [];
    renderSummaryCards(summary);
    renderResidentTable(gmeResidents);
  } catch (err) {
    document.getElementById('gmeSummaryCards').innerHTML =
      `<div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Error loading data</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}

function renderSummaryCards(summary) {
  const container = document.getElementById('gmeSummaryCards');
  const cards = [
    { label: 'Total Pool', value: `$${summary.total_pool?.toLocaleString() || '0'}`, icon: '🏦', color: '#6c5ce7' },
    { label: 'Total Used', value: `$${(summary.total_used || 0).toLocaleString()}`, icon: '💳', color: '#e17055' },
    { label: 'Total Remaining', value: `$${(summary.total_remaining || 0).toLocaleString()}`, icon: '💰', color: '#00b894' },
    { label: 'Residents w/ Funds', value: `${summary.residents_with_funds || 0}`, icon: '👤', color: '#0984e3' },
  ];
  container.innerHTML = cards.map(c => `
    <div class="card" style="text-align:center;padding:14px 10px">
      <div style="font-size:22px;margin-bottom:4px">${c.icon}</div>
      <div style="font-size:24px;font-weight:700;color:${c.color}">${c.value}</div>
      <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${c.label}</div>
    </div>
  `).join('');
}

function renderResidentTable(residents) {
  const container = document.getElementById('gmeResidentCards');
  if (!residents || !residents.length) {
    container.innerHTML = '<div class="empty-state" style="padding:40px"><div class="empty-state-title">No residents found</div></div>';
    return;
  }

  const limit = 1250;

  container.innerHTML = `
    <div style="border:1px solid var(--border);border-radius:8px;overflow:hidden">
      <div style="display:grid;grid-template-columns:1.8fr 0.6fr 1.6fr 0.7fr 0.9fr 0.3fr;gap:0;background:var(--bg-secondary);font-size:11px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;padding:8px 12px;border-bottom:1px solid var(--border)">
        <div>Resident</div>
        <div>PGY</div>
        <div>Used / $1,250</div>
        <div>Status</div>
        <div>Last Reimb</div>
        <div></div>
      </div>
      ${residents.map(r => {
        const id = r.id || `${r.firstName || ''}_${r.lastName || ''}`.replace(/\s+/g, '_');
        const used = r.total_used || 0;
        const remaining = limit - used;
        const pct = Math.min((used / limit) * 100, 100);
        const exhausted = used >= limit;
        const barColor = exhausted ? '#d63031' : remaining < 500 ? '#e17055' : '#00b894';
        const reimbursements = r.reimbursements || [];
        const lastDate = reimbursements.length ? reimbursements[reimbursements.length - 1].date : '—';
        const ay = document.getElementById('gmeAySelector')?.value || '2025-26';
        const isExpanded = expandedResident === id;
        const allReimb = ay === 'all' ? reimbursements : (r._allAyData?.reimbursements || reimbursements);

        return `
          <div class="gme-row" style="display:grid;grid-template-columns:1.8fr 0.6fr 1.6fr 0.7fr 0.9fr 0.3fr;gap:0;padding:6px 12px;border-bottom:1px solid var(--border);align-items:center;font-size:13px;transition:background 0.15s;cursor:pointer" onclick="toggleResidentDetail('${escapeHtml(id)}')" onmouseover="this.style.background='var(--bg-secondary)'" onmouseout="this.style.background=''">
            <div style="display:flex;align-items:center;gap:6px">
              <span style="font-size:10px;color:var(--text-muted);transition:transform 0.2s;${isExpanded ? 'transform:rotate(90deg)' : ''}">▶</span>
              <span style="font-weight:500">${escapeHtml(r.firstName || '')} ${escapeHtml(r.lastName || '')}</span>
            </div>
            <div><span class="tag" style="font-size:10px;padding:1px 8px;background:${exhausted?'#d6303115':'#6c5ce715'};color:${exhausted?'#d63031':'#6c5ce7'};border:1px solid ${exhausted?'#d6303130':'#6c5ce730'}">${escapeHtml(r.pgy || 'N/A')}</span></div>
            <div>
              <div style="display:flex;align-items:center;gap:8px">
                <span style="font-weight:600;font-size:12px;min-width:70px;white-space:nowrap">$${used.toLocaleString()} / $1,250</span>
                <div style="flex:1;max-width:100px;height:6px;background:var(--border);border-radius:3px;overflow:hidden">
                  <div style="height:100%;width:${pct}%;background:${barColor};border-radius:3px;transition:width 0.4s ease"></div>
                </div>
              </div>
            </div>
            <div>
              ${exhausted
                ? '<span class="tag" style="font-size:10px;padding:1px 8px;background:#d6303120;color:#d63031;border:1px solid #d6303140">Exhausted</span>'
                : `<span style="font-size:11px;color:#00b894">$${remaining.toLocaleString()} left</span>`
              }
            </div>
            <div style="font-size:11px;color:var(--text-muted)">${lastDate}</div>
            <div style="text-align:right;font-size:10px;color:var(--text-muted)">${reimbursements.length} txns</div>
          </div>
          ${isExpanded ? renderResidentDetail(id, r, allReimb, ay, remaining, exhausted) : ''}
        `;
      }).join('')}
    </div>
    <div style="font-size:11px;color:var(--text-muted);margin-top:8px;text-align:right">${residents.length} residents · $1,250 annual limit</div>
  `;
}

function renderResidentDetail(id, resident, reimbursements, currentAy) {
  // Group reimbursements by AY
  const ayGroups = {};
  for (const r of reimbursements || []) {
    const ay = r.ay || 'unknown';
    if (!ayGroups[ay]) ayGroups[ay] = [];
    ayGroups[ay].push(r);
  }
  
  // Sort AYs descending
  const ayList = Object.keys(ayGroups).sort().reverse();
  const validAys = ayList.filter(a => a !== 'unknown');
  const unknown = ayList.filter(a => a === 'unknown');
  const orderedAys = [...validAys, ...unknown];
  
  // Determine which AY tab is active
  const activeAy = window[`_gmeAyTab_${id}`] || currentAy || '2025-26';
  const activeTxns = ayGroups[activeAy] || [];
  
  const totalAllAy = reimbursements.reduce((s, r) => s + (r.amount || 0), 0);
  const totalFiltered = activeTxns.reduce((s, r) => s + (r.amount || 0), 0);
  
  return `
    <div style="background:var(--bg-card-alt);border-bottom:1px solid var(--border);padding:12px 12px 12px 30px;animation:fadeIn 0.2s ease">
      <style>@keyframes fadeIn{from{opacity:0;max-height:0}to{opacity:1;max-height:1000px}}</style>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;border-bottom:1px solid var(--border);padding-bottom:8px">
        ${orderedAys.map(ay => {
          const ayTotal = ayGroups[ay].reduce((s, r) => s + (r.amount || 0), 0);
          const ayCapped = Math.min(ayTotal, 1250);
          const isActive = ay === activeAy;
          return `
            <div style="cursor:pointer;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:500;
                        ${isActive ? 'background:var(--accent);color:#fff' : 'background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border)'}
                        transition:all 0.15s"
                 onclick="switchGmeAyTab('${escapeHtml(id)}', '${escapeHtml(ay)}')">
              ${ay === 'unknown' ? 'Unspecified' : ay}
              <span style="opacity:0.7;margin-left:4px">$${ayCapped.toLocaleString()}</span>
            </div>
          `;
        }).join('')}
        ${orderedAys.length > 1 ? `
          <div style="margin-left:auto;font-size:11px;color:var(--text-muted);padding:4px 8px">
            All AYs: $${Math.min(totalAllAy, 1250).toLocaleString()}
          </div>
        ` : ''}
      </div>
      
      ${activeTxns.length === 0 ? `
        <div style="text-align:center;padding:16px;color:var(--text-muted);font-size:13px">
          📭 No transactions for ${activeAy === 'unknown' ? 'this period' : activeAy}
        </div>
      ` : `
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;display:flex;justify-content:space-between">
          <span>${activeAy} transactions · ${activeTxns.length} items · $${totalFiltered.toLocaleString()} total</span>
          <span style="font-weight:600;color:${totalFiltered >= 1250 ? '#d63031' : '#00b894'}">
            Cap: $1,250 · ${totalFiltered >= 1250 ? 'Exhausted' : `$${(1250 - totalFiltered).toLocaleString()} remaining`}
          </span>
        </div>
        <div style="border:1px solid var(--border);border-radius:6px;overflow:hidden">
          <div style="display:grid;grid-template-columns:1fr 0.7fr 2fr 0.5fr 0.6fr;gap:0;background:var(--bg-secondary);font-size:10px;font-weight:600;color:var(--text-muted);text-transform:uppercase;padding:5px 8px;border-bottom:1px solid var(--border)">
            <div>Date</div>
            <div>Amount</div>
            <div>Description</div>
            <div>Account</div>
            <div>Status</div>
          </div>
          ${activeTxns.map(t => {
            const acct = t.account || t.account_type || '';
            const acctShort = acct.length > 20 ? acct.substring(0, 18) + '…' : acct;
            const isGme = acct.toLowerCase().includes('gme');
            return `
            <div style="display:grid;grid-template-columns:1fr 0.7fr 2fr 0.5fr 0.6fr;gap:0;padding:5px 8px;border-bottom:1px solid var(--border);font-size:12px;align-items:center">
              <div style="color:var(--text-muted)">${t.date || '—'}</div>
              <div style="font-weight:600;color:${(t.amount || 0) >= 500 ? '#e17055' : 'var(--text)'}">$${(t.amount || 0).toLocaleString()}</div>
              <div style="color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${escapeHtml(t.description || '')}">${escapeHtml(t.description || '—')}</div>
              <div><span class="tag" style="font-size:9px;padding:1px 5px;background:${isGme ? '#6c5ce715' : '#0984e315'};color:${isGme ? '#6c5ce7' : '#0984e3'};border:1px solid ${isGme ? '#6c5ce730' : '#0984e330'}" title="${escapeHtml(acct)}">${escapeHtml(acctShort)}</span></div>
              <div><span class="tag" style="font-size:9px;padding:1px 6px;background:#00b89415;color:#00b894;border:1px solid #00b89430">${t.status || 'approved'}</span></div>
            </div>`;
          }).join('')}
        </div>
      `}
      
      ${resident.total_used < 1250 && activeAy !== 'all' ? `
        <div style="margin-top:8px;text-align:right">
          <button class="btn" style="padding:4px 12px;font-size:11px" onclick="openAddReimbursement('${escapeHtml(resident.id)}', '${escapeHtml((resident.firstName||'') + ' ' + (resident.lastName||''))}', ${1250 - resident.total_used})">
            ➕ Add Reimbursement
          </button>
        </div>
      ` : ''}
    </div>
  `;
}

function toggleResidentDetail(id) {
  if (expandedResident === id) {
    expandedResident = null;
  } else {
    expandedResident = id;
    window[`_gmeAyTab_${id}`] = document.getElementById('gmeAySelector')?.value || '2025-26';
  }
  renderResidentTable(gmeResidents);
}

function switchGmeAyTab(id, ay) {
  window[`_gmeAyTab_${id}`] = ay;
  renderResidentTable(gmeResidents);
}

function filterGmeResidents(filter) {
  document.querySelectorAll('.gme-filter-btn').forEach(el => {
    el.style.borderColor = el.dataset.filter === filter ? 'var(--accent)' : '';
  });
  let filtered = gmeResidents;
  if (filter === 'has-funds') {
    filtered = gmeResidents.filter(r => (r.total_used || 0) < 1250);
  } else if (filter === 'exhausted') {
    filtered = gmeResidents.filter(r => (r.total_used || 0) >= 1250);
  }
  renderResidentTable(filtered);
}

function openAddReimbursement(residentId, residentName, maxAmount) {
  const body = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div style="grid-column:1/-1;font-size:13px;color:var(--text-muted);margin-bottom:4px">
        Adding reimbursement for <strong>${escapeHtml(residentName)}</strong> — $${maxAmount.toLocaleString()} remaining
      </div>
      <div style="grid-column:1/-1">
        <label style="font-size:11px;color:var(--text-muted)">Date</label>
        <input id="gmeDate" type="date" value="${new Date().toISOString().split('T')[0]}" style="width:100%">
      </div>
      <div>
        <label style="font-size:11px;color:var(--text-muted)">Amount ($)</label>
        <input id="gmeAmount" type="number" min="1" max="${maxAmount}" value="" style="width:100%" placeholder="e.g. 250">
      </div>
      <div>
        <label style="font-size:11px;color:var(--text-muted)">Category</label>
        <select id="gmeCategory" style="width:100%">
          <option value="Conference">Conference</option>
          <option value="Books">Books</option>
          <option value="Travel">Travel</option>
          <option value="Equipment">Equipment</option>
          <option value="Other">Other</option>
        </select>
      </div>
      <div>
        <label style="font-size:11px;color:var(--text-muted)">Status</label>
        <select id="gmeStatus" style="width:100%">
          <option value="paid">Paid</option>
          <option value="pending">Pending</option>
          <option value="denied">Denied</option>
        </select>
      </div>
    </div>
  `;
  const footer = `
    <button class="btn" onclick="saveReimbursement('${escapeHtml(residentId)}', ${maxAmount})">💾 Save</button>
    <button class="btn" onclick="closeModal()">Cancel</button>
  `;
  showModal('➕ Add Reimbursement', body, footer);
}

async function saveReimbursement(residentId, maxAmount) {
  const date = document.getElementById('gmeDate').value;
  const amount = parseInt(document.getElementById('gmeAmount').value);
  const category = document.getElementById('gmeCategory').value;
  const status = document.getElementById('gmeStatus').value;

  if (!date) { showToast('Please select a date', 'warning'); return; }
  if (!amount || amount < 1) { showToast('Please enter a valid amount', 'warning'); return; }
  if (amount > maxAmount) { showToast(`Amount exceeds remaining funds ($${maxAmount})`, 'warning'); return; }

  try {
    await api.addReimbursement({
      resident_id: residentId,
      date: date,
      amount: amount,
      category: category,
      status: status
    });
    showToast('Reimbursement added!', 'success');
    closeModal();
    await loadGmeData();
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  }
}
