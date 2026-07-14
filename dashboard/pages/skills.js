/* ═══════════════════════════════════════════════════════════════════════
   Skills Hub — Clean skill browser
   Grid/list views, run, filter. No emoji.
   ═══════════════════════════════════════════════════════════════════ */

const SKILL_INDICATORS = ['#', '@', '&', '+', '~', '^', '*', '=', '%', '$', ':', ';'];

async function renderSkills() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Skills Hub</h1>
        <p class="page-subtitle">Browse, run, and monitor skill performance</p>
      </div>
      <div class="btn-group">
        <input id="skillFilter" class="form-input" style="width:200px" placeholder="Filter skills..." oninput="filterSkills()">
      </div>
    </div>
    <div class="tabs" id="skillTabs">
      <button class="tab active" data-view="grid" onclick="switchSkillView('grid')">Grid</button>
      <button class="tab" data-view="list" onclick="switchSkillView('list')">List</button>
    </div>
    <div id="skillsContainer"><div class="loading"><div class="loading-spinner"></div></div></div>
    <div id="skillDetail" style="display:none"></div>
  `;

  try {
    const skills = await api.getSkills();
    window._allSkills = skills;
    renderSkillGrid(skills);
  } catch (err) {
    document.getElementById('skillsContainer').innerHTML = `<div class="empty-state"><div class="empty-state-icon">—</div><div class="empty-state-title">${escapeHtml(err.message)}</div></div>`;
  }
}

function renderSkillGrid(skills) {
  const container = document.getElementById('skillsContainer');
  if (!skills || skills.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">—</div><div class="empty-state-title">No skills installed</div></div>';
    return;
  }
  container.innerHTML = `<div class="grid grid-3" id="skillGrid">${skills.map((s, i) => {
    const lastScore = s.scores && s.scores.length > 0 ? s.scores[s.scores.length - 1] : null;
    const avg = lastScore && lastScore.criteria_scores ? (lastScore.criteria_scores.reduce((a, b) => a + b, 0) / lastScore.criteria_scores.length) : null;
    const indicator = SKILL_INDICATORS[i % SKILL_INDICATORS.length];
    const scoreColor = avg !== null ? (avg >= 0.7 ? 'var(--green)' : avg >= 0.4 ? 'var(--yellow)' : 'var(--red)') : 'var(--text-muted)';
    return `<div class="skill-card" onclick="showSkillDetail('${s.name}')">
      <div class="skill-card-header">
        <div class="skill-card-icon">${indicator}</div>
        <div class="skill-card-name">${s.name.replace(/-/g, ' ')}</div>
      </div>
      <div class="skill-card-desc">${s.description ? s.description.slice(0, 100) + (s.description.length > 100 ? '...' : '') : 'No description'}</div>
      <div class="skill-card-footer">
        ${avg !== null
          ? `<span class="badge" style="background:${scoreColor === 'var(--green)' ? 'var(--green-dim)' : scoreColor === 'var(--yellow)' ? 'var(--yellow-dim)' : 'var(--red-dim)'};color:${scoreColor}">${(avg * 100).toFixed(0)}%</span>`
          : '<span class="badge badge-info">New</span>'}
        ${s.has_learnings ? '<span class="badge" style="background:var(--accent-dim);color:var(--accent-light)">Learnings</span>' : ''}
        <button class="btn btn-sm btn-primary" style="margin-left:auto" onclick="event.stopPropagation();quickRunSkill('${s.name}')">Run</button>
      </div>
    </div>`;
  }).join('')}</div>`;
}

function switchSkillView(view) {
  document.querySelectorAll('#skillTabs .tab').forEach(t => t.classList.toggle('active', t.dataset.view === view));
  if (view === 'list') {
    const skills = window._allSkills || [];
    document.getElementById('skillsContainer').innerHTML = `<div class="table-wrapper"><table><thead><tr><th>Skill</th><th>Score</th><th>Info</th><th></th></tr></thead><tbody>${skills.map((s) => {
      const lastScore = s.scores && s.scores.length > 0 ? s.scores[s.scores.length - 1] : null;
      const avg = lastScore && lastScore.criteria_scores ? (lastScore.criteria_scores.reduce((a, b) => a + b, 0) / lastScore.criteria_scores.length) : null;
      const scoreColor = avg !== null ? (avg >= 0.7 ? 'var(--green)' : avg >= 0.4 ? 'var(--yellow)' : 'var(--red)') : 'var(--text-muted)';
      return `<tr onclick="showSkillDetail('${s.name}')" style="cursor:pointer">
        <td><strong>${s.name.replace(/-/g, ' ')}</strong></td>
        <td>${avg !== null ? `<span class="badge" style="background:${scoreColor === 'var(--green)' ? 'var(--green-dim)' : scoreColor === 'var(--yellow)' ? 'var(--yellow-dim)' : 'var(--red-dim)'};color:${scoreColor}">${(avg * 100).toFixed(0)}%</span>` : '<span class="badge badge-info">—</span>'}</td>
        <td>${s.has_learnings ? '<span class="badge" style="background:var(--accent-dim);color:var(--accent-light)">Yes</span>' : '<span style="color:var(--text-muted);font-size:0.75rem">—</span>'}</td>
        <td><button class="btn btn-sm btn-primary" onclick="event.stopPropagation();quickRunSkill('${s.name}')">Run</button></td>
      </tr>`;
    }).join('')}</tbody></table></div>`;
  } else {
    renderSkillGrid(window._allSkills || []);
  }
}

function filterSkills() {
  const q = document.getElementById('skillFilter').value.toLowerCase();
  const skills = (window._allSkills || []).filter(s => s.name.toLowerCase().includes(q));
  renderSkillGrid(skills);
}

async function quickRunSkill(name) {
  try {
    const r = await api.runSkill(name);
    showToast(`"${name}" dispatched to ${r.agent}`, 'success');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}
