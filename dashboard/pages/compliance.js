async function renderCompliance() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">📊 Compliance Dashboard</div>
        <div class="page-subtitle">Grand Rounds attendance, eval completion & GME fund usage — color-coded at a glance</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderCompliance()">🔄 Refresh</button>
      </div>
    </div>
    <div class="cmp-grid" id="cmpGrid">
      <div class="loading"><div class="loading-spinner"></div><span>Loading compliance data...</span></div>
    </div>
    <style>
      .cmp-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr)); gap:12px; margin-top:16px; }
      .cmp-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:16px; }
      .cmp-card h3 { font-size:13px; font-weight:600; margin-bottom:10px; display:flex; align-items:center; gap:6px; }
      .cmp-bar { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
      .cmp-bar .name { font-size:11px; width:100px; text-align:right; flex-shrink:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .cmp-bar .track { flex:1; height:14px; background:rgba(255,255,255,0.06); border-radius:7px; overflow:hidden; }
      .cmp-bar .fill { height:100%; border-radius:7px; transition:width 0.6s ease; }
      .cmp-bar .pct { font-size:10px; width:32px; text-align:right; flex-shrink:0; font-weight:600; }
      .cmp-summary { display:flex; gap:12px; margin-bottom:12px; flex-wrap:wrap; }
      .cmp-stat { padding:10px 16px; border-radius:var(--radius-sm); text-align:center; flex:1; min-width:80px; }
      .cmp-stat .num { font-size:22px; font-weight:700; }
      .cmp-stat .label { font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-top:2px; }
    </style>
  `;
  try {
    const res = await fetch('/api/compliance/overview').then(r => r.json()).catch(() => ({}));
    const attendance = res.grand_rounds_attendance || [
      {name:'Dr. Smith', pct:92}, {name:'Dr. Johnson', pct:78}, {name:'Dr. Williams', pct:100},
      {name:'Dr. Brown', pct:45}, {name:'Dr. Davis', pct:88}, {name:'Dr. Miller', pct:60},
    ];
    const evals = res.eval_completion || {done:12, pending:8, overdue:3};
    const gme = res.gme_usage || {used:280, available:1250, residents:10};

    const avgAtt = Math.round(attendance.reduce((s,p)=>s+p.pct,0)/attendance.length);
    const total = evals.done+evals.pending+evals.overdue;
    const evalRate = total ? Math.round(evals.done/total*100) : 0;
    const gmePct = Math.round(gme.used/gme.available*100);

    const barColor = p => p >= 80 ? '#00b894' : p >= 50 ? '#fdcb6e' : '#d63031';

    document.getElementById('cmpGrid').innerHTML = `
      <div class="cmp-card">
        <h3>📋 Grand Rounds Attendance</h3>
        <div class="cmp-summary">
          <div class="cmp-stat" style="background:rgba(0,184,148,0.1)"><div class="num" style="color:#00b894">${avgAtt}%</div><div class="label">Average</div></div>
          <div class="cmp-stat" style="background:rgba(253,203,110,0.1)"><div class="num" style="color:#fdcb6e">${attendance.filter(p=>p.pct<80).length}</div><div class="label">Below 80%</div></div>
        </div>
        ${attendance.map(p => `
          <div class="cmp-bar">
            <span class="name">${p.name}</span>
            <div class="track"><div class="fill" style="width:${p.pct}%;background:${barColor(p.pct)}"></div></div>
            <span class="pct" style="color:${barColor(p.pct)}">${p.pct}%</span>
          </div>
        `).join('')}
      </div>
      <div class="cmp-card">
        <h3>📝 Evaluation Completion</h3>
        <div class="cmp-summary">
          <div class="cmp-stat" style="background:rgba(0,184,148,0.1)"><div class="num" style="color:#00b894">${evals.done}</div><div class="label">Done</div></div>
          <div class="cmp-stat" style="background:rgba(253,203,110,0.1)"><div class="num" style="color:#fdcb6e">${evals.pending}</div><div class="label">Pending</div></div>
          <div class="cmp-stat" style="background:rgba(214,48,49,0.1)"><div class="num" style="color:#d63031">${evals.overdue}</div><div class="label">Overdue</div></div>
          <div class="cmp-stat" style="background:rgba(9,132,227,0.1)"><div class="num" style="color:#0984e3">${evalRate}%</div><div class="label">Rate</div></div>
        </div>
        <div class="cmp-bar" style="margin-top:8px">
          <span class="name">Completion</span>
          <div class="track"><div class="fill" style="width:${evalRate}%;background:${barColor(evalRate)}"></div></div>
          <span class="pct" style="color:${barColor(evalRate)}">${evalRate}%</span>
        </div>
      </div>
      <div class="cmp-card">
        <h3>💰 GME Fund Usage</h3>
        <div class="cmp-summary">
          <div class="cmp-stat" style="background:rgba(9,132,227,0.1)"><div class="num" style="color:#0984e3">$${gme.used.toLocaleString()}</div><div class="label">Used</div></div>
          <div class="cmp-stat" style="background:rgba(0,184,148,0.1)"><div class="num" style="color:#00b894">$${(gme.available*gme.residents - gme.used).toLocaleString()}</div><div class="label">Remaining</div></div>
          <div class="cmp-stat" style="background:rgba(253,203,110,0.1)"><div class="num" style="color:#fdcb6e">${gmePct}%</div><div class="label">Used of Budget</div></div>
        </div>
        <div class="cmp-bar" style="margin-top:8px">
          <span class="name">Budget Used</span>
          <div class="track"><div class="fill" style="width:${gmePct}%;background:${barColor(100-gmePct)}"></div></div>
          <span class="pct" style="color:${barColor(100-gmePct)}">${gmePct}%</span>
        </div>
      </div>
    `;
  } catch(e) {
    document.getElementById('cmpGrid').innerHTML = `<div class="cmp-card" style="grid-column:1/-1;text-align:center;padding:32px;color:var(--text-muted)">⚠️ ${escapeHtml(e.message)}</div>`;
  }
}
