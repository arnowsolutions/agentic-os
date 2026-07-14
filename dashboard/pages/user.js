/**
 * User Dashboard — EZ ID self-service portal for residents.
 * URL: #user
 * Data source: /api/user/{ez_id}
 */
async function renderUser() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">👤 Resident Portal</div>
        <div class="page-subtitle">Enter your EZ ID to see your schedule, benefits, and more</div>
      </div>
    </div>
    <div id="userLoginSection">
      <div style="max-width:480px;margin:40px auto;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:32px;text-align:center;">
        <div style="font-size:48px;margin-bottom:16px;">🆔</div>
        <h2 style="font-size:18px;font-weight:600;margin-bottom:8px;">Resident Dashboard</h2>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:24px;">Look up your on-call schedule, reimbursement balance, upcoming evals, sick call record, and commute — all in one place.</p>
        <div style="margin-bottom:16px;text-align:left;">
          <label style="display:block;font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:4px;">EZ ID</label>
          <input type="text" id="ezIdInput" placeholder="e.g. EZ12345" style="width:100%;padding:10px 14px;background:var(--bg-input);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text-primary);font-size:14px;outline:none;" autocomplete="off">
        </div>
        <div style="margin-bottom:24px;text-align:left;">
          <label style="display:block;font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:4px;">PIN</label>
          <input type="password" id="pinInput" placeholder="4-digit PIN" maxlength="4" inputmode="numeric" pattern="[0-9]*" style="width:100%;padding:10px 14px;background:var(--bg-input);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text-primary);font-size:14px;outline:none;">
        </div>
        <button class="btn btn-primary" onclick="lookupUser()" style="width:100%;padding:10px;font-size:14px;">🔍 Look Up</button>
        <div id="userLoginError" style="color:var(--red);font-size:12px;margin-top:12px;display:none;"></div>
        <label style="display:flex;align-items:center;gap:6px;margin-top:12px;font-size:12px;color:var(--text-secondary);cursor:pointer;">
          <input type="checkbox" id="rememberEzId" style="accent-color:var(--accent);"> Remember my EZ ID
        </label>
      </div>
    </div>
    <div id="userDashboardContent" style="display:none;"></div>
    <style>
      .user-card { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-lg); padding:20px; margin-bottom:16px; }
      .user-card h3 { font-size:13px; font-weight:600; margin-bottom:12px; display:flex; align-items:center; gap:6px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px; }
      .user-card .card-value { font-size:22px; font-weight:700; }
      .user-card .card-label { font-size:11px; color:var(--text-muted); margin-top:2px; }
      .user-stat-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px; }
      .user-stat { background:var(--bg-secondary); border-radius:var(--radius); padding:14px; text-align:center; border:1px solid var(--border); }
      .user-stat .num { font-size:20px; font-weight:700; }
      .user-stat .lbl { font-size:10px; color:var(--text-muted); margin-top:4px; text-transform:uppercase; }
      .user-info-row { display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
      .user-info-row .field { font-size:12px; color:var(--text-secondary); }
      .user-info-row .field strong { color:var(--text-primary); }
      .user-badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
      .user-badge.on { background:var(--green-dim); color:var(--green); }
      .user-badge.off { background:var(--red-dim); color:var(--red); }
      .user-badge.warn { background:var(--yellow-dim); color:var(--yellow); }
      .user-list { list-style:none; padding:0; }
      .user-list li { padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04); font-size:13px; display:flex; justify-content:space-between; }
      .user-list li:last-child { border-bottom:none; }
      .user-list .val { font-weight:600; }
      .user-header-card { display:flex; align-items:center; gap:20px; flex-wrap:wrap; }
      .user-avatar { width:56px; height:56px; border-radius:50%; background:var(--accent-glow); display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:700; color:var(--accent-light); flex-shrink:0; }
      @media (max-width:640px) { .user-header-card { flex-direction:column; text-align:center; } }
    </style>
  `;

  // Enter key support
  document.getElementById('ezIdInput').addEventListener('keydown', e => { if (e.key === 'Enter') lookupUser(); });
  document.getElementById('pinInput').addEventListener('keydown', e => { if (e.key === 'Enter') lookupUser(); });
  // Pre-fill remembered EZ ID
  const savedEzId = localStorage.getItem('aos_ezid');
  if (savedEzId) {
    document.getElementById('ezIdInput').value = savedEzId;
    document.getElementById('rememberEzId').checked = true;
    document.getElementById('pinInput').focus();
  }
}

async function lookupUser() {
  const ezId = document.getElementById('ezIdInput').value.trim();
  const pin = document.getElementById('pinInput').value.trim();
  const errorEl = document.getElementById('userLoginError');
  const loginSection = document.getElementById('userLoginSection');
  const dashSection = document.getElementById('userDashboardContent');

  errorEl.style.display = 'none';
  if (!ezId) { errorEl.textContent = 'Please enter your EZ ID.'; errorEl.style.display = 'block'; return; }
  if (!pin || pin.length !== 4 || !/^\d{4}$/.test(pin)) { errorEl.textContent = 'PIN must be 4 digits.'; errorEl.style.display = 'block'; return; }

  // Simple PIN verification — check against the PIN DB
  loginSection.style.display = 'none';
  dashSection.style.display = 'block';
  dashSection.innerHTML = '<div class="loading" style="padding:60px 0"><div class="loading-spinner"></div><span>Looking up your data...</span></div>';

  try {
    const res = await fetch(`/api/user/${encodeURIComponent(ezId)}?pin=${encodeURIComponent(pin)}`);
    const data = await res.json();

    if (data.error) {
      dashSection.innerHTML = `
        <div style="max-width:480px;margin:40px auto;text-align:center;">
          <div style="font-size:48px;margin-bottom:16px;">😕</div>
          <h2 style="font-size:18px;margin-bottom:8px;">Not Found</h2>
          <p style="color:var(--text-secondary);font-size:13px;">${data.error}</p>
          <button class="btn btn-primary mt-3" onclick="renderUser()">Try Again</button>
        </div>`;
      return;
    }

    renderUserDashboard(data, ezId);
    // Remember EZ ID if checkbox checked
    if (document.getElementById('rememberEzId').checked) {
      localStorage.setItem('aos_ezid', ezId);
    } else {
      localStorage.removeItem('aos_ezid');
    }
  } catch (e) {
    dashSection.innerHTML = `
      <div style="max-width:480px;margin:40px auto;text-align:center;">
        <div style="font-size:48px;margin-bottom:16px;">⚠️</div>
        <h2 style="font-size:18px;margin-bottom:8px;">Connection Error</h2>
        <p style="color:var(--text-secondary);font-size:13px;">Could not reach the server. The dashboard service may be down.</p>
        <button class="btn btn-primary mt-3" onclick="renderUser()">Try Again</button>
      </div>`;
  }
}

function renderUserDashboard(data, ezId) {
  const contact = data.contact || {};
  const fullName = [contact.firstName, contact.lastName].filter(Boolean).join(' ') || ezId;
  const initials = (contact.firstName?.[0] || '') + (contact.lastName?.[0] || '') || '?';
  const category = contact.category || 'Resident';
  const pgy = contact.pgy || '';
  const hospital = contact.location || contact.hospital || '';
  const email = contact.email || '';

  const oncall = data.oncall_today || [];
  const reimbursement = data.reimbursement;
  const evals = data.evals || [];
  const sickCalls = data.sick_calls || [];
  const commute = data.commute;

  const content = document.getElementById('userDashboardContent');

  content.innerHTML = `
    <!-- Header Card -->
    <div class="user-card">
      <div class="user-header-card">
        <div class="user-avatar">${initials}</div>
        <div style="flex:1;min-width:200px;">
          <div style="font-size:20px;font-weight:700;">${fullName}</div>
          <div class="user-info-row" style="margin-top:6px;">
            <span class="field"><strong>EZ ID:</strong> ${ezId}</span>
            <span class="field"><strong>Role:</strong> ${pgy ? `PGY-${pgy}` : category}</span>
            ${hospital ? `<span class="field"><strong>Location:</strong> ${hospital}</span>` : ''}
            ${email ? `<span class="field"><strong>Email:</strong> ${email}</span>` : ''}
          </div>
        </div>
        <div style="text-align:right;">
          ${oncall.length > 0
            ? `<span class="user-badge on">🟢 On Call Today</span>`
            : `<span class="user-badge off">⚪ Not On Call</span>`
          }
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="user-stat-grid">
      <div class="user-stat">
        <div class="num" style="color:var(--accent-light)">${oncall.length > 0 ? oncall.map(o => o.hospital || '').filter(Boolean).join(', ') : '—'}</div>
        <div class="lbl">On-Call Today</div>
      </div>
      <div class="user-stat">
        <div class="num" style="color:var(--green)">${reimbursement && reimbursement.balance !== undefined ? `$${reimbursement.balance.toLocaleString()}` : '—'}</div>
        <div class="lbl">Reimbursement Balance</div>
      </div>
      <div class="user-stat">
        <div class="num" style="color:var(--blue)">${evals.length > 0 ? evals.filter(e => !e.completed).length : '—'}</div>
        <div class="lbl">Pending Evals</div>
      </div>
      <div class="user-stat">
        <div class="num" style="color:${sickCalls.length > 3 ? 'var(--red)' : sickCalls.length > 0 ? 'var(--yellow)' : 'var(--green)'}">${sickCalls.length}</div>
        <div class="lbl">Sick Call Records</div>
      </div>
    </div>

    <!-- Detail Cards -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;">

      <!-- On-Call Details -->
      <div class="user-card">
        <h3>📅 Today's On-Call</h3>
        ${oncall.length > 0
          ? `<ul class="user-list">${oncall.map(o => `
            <li><span>${o.hospital || 'Hospital'}</span><span class="val">${o.name || ''}${o.role ? ` (${o.role})` : ''}</span></li>
          `).join('')}</ul>`
          : `<p style="color:var(--text-muted);font-size:13px;">You're not on call today.</p>`
        }
      </div>

      <!-- Reimbursement -->
      <div class="user-card">
        <h3>💰 Reimbursement</h3>
        ${reimbursement
          ? `<div style="display:flex;gap:16px;flex-wrap:wrap;">
              <div>
                <div class="card-value" style="color:var(--green)">$${(reimbursement.balance || 0).toLocaleString()}</div>
                <div class="card-label">Available Balance</div>
              </div>
              <div>
                <div class="card-value">${reimbursement.used ? `$${reimbursement.used.toLocaleString()}` : '$0'}</div>
                <div class="card-label">Used This Year</div>
              </div>
              <div>
                <div class="card-value">$${(reimbursement.max || 0).toLocaleString()}</div>
                <div class="card-label">Annual Max</div>
              </div>
            </div>`
          : `<p style="color:var(--text-muted);font-size:13px;">Reimbursement data service unavailable.</p>`
        }
      </div>

      <!-- Pending Evals -->
      <div class="user-card">
        <h3>📝 Evaluation Status</h3>
        ${evals.length > 0
          ? `<ul class="user-list">${evals.slice(0, 8).map(e => `
            <li><span>${e.form_name || e.eval_type || 'Evaluation'}</span>
            <span class="val" style="color:${e.completed ? 'var(--green)' : 'var(--yellow)'}">${e.completed ? '✅ Done' : '⏳ Pending'}</span></li>
          `).join('')}</ul>`
          : `<p style="color:var(--text-muted);font-size:13px;">No evaluation records found for your EZ ID.</p>`
        }
      </div>

      <!-- Sick Call Record -->
      <div class="user-card">
        <h3>🏥 Sick Call History</h3>
        ${sickCalls.length > 0
          ? `<ul class="user-list">${sickCalls.map(s => `
            <li><span>${s.date || s.reported_at || ''}</span>
            <span class="val" style="color:${s.violation ? 'var(--red)' : 'var(--green)'}">${s.reason || s.type || s.status || 'Recorded'}</span></li>
          `).join('')}</ul>`
          : `<p style="color:var(--text-muted);font-size:13px;">No sick call records found.</p>`
        }
      </div>

      <!-- Commute -->
      <div class="user-card">
        <h3>🚗 Commute</h3>
        ${commute
          ? `<div>
              <p style="font-size:13px;color:var(--text-secondary);margin-bottom:8px;">
                <strong>From:</strong> ${commute.address || commute.origin || 'Home address'}
              </p>
              ${commute.duration ? `<p style="font-size:13px;color:var(--text-secondary);"><strong>Duration:</strong> ${commute.duration}</p>` : ''}
              ${commute.distance ? `<p style="font-size:13px;color:var(--text-secondary);"><strong>Distance:</strong> ${commute.distance}</p>` : ''}
              ${commute.traffic ? `<p style="font-size:13px;color:var(--text-secondary);"><strong>Traffic:</strong> ${commute.traffic}</p>` : ''}
              ${commute.message ? `<p style="font-size:12px;color:var(--text-muted);margin-top:8px;">${commute.message}</p>` : ''}
            </div>`
          : `<p style="color:var(--text-muted);font-size:13px;">No address on file to calculate commute.</p>`
        }
      </div>

    </div>

    <div style="text-align:center;margin-top:24px;padding:16px 0;">
      <button class="btn btn-ghost" onclick="renderUser()">← Look Up Another Resident</button>
      <span style="color:var(--text-muted);font-size:11px;margin-left:12px;">Secured with PIN authentication</span>
    </div>
  `;
}
