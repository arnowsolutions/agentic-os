/* Montefiore Urology — Voice Command Cheat Sheet */
/* Lists all voice commands for Telegram report generation */
/* Health status polled live from /api/status */

async function renderVoiceCommands() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <style>
      .vc-header { margin-bottom: 24px; }
      .vc-header h1 { font-size: 1.6rem; font-weight: 700; margin: 0 0 4px; }
      .vc-header p { margin: 0; color: var(--text-muted); font-size: 13px; }
      
      .vc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 20px; }
      .vc-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
      .vc-card-header { padding: 16px 20px; font-weight: 600; font-size: 14px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; }
      .vc-card-body { padding: 16px 20px; }
      
      .vc-command { padding: 12px 0; border-bottom: 1px solid var(--border-dim); }
      .vc-command:last-child { border-bottom: none; }
      .vc-cmd-voice { font-weight: 600; font-size: 13px; color: var(--accent); margin-bottom: 2px; }
      .vc-cmd-what { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
      .vc-cmd-tag { display: inline-flex; align-items: center; gap: 4px; font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
      .vc-tag-telegram { background: rgba(0,122,255,.15); color: #007aff; }
      .vc-tag-email { background: rgba(52,199,89,.15); color: #34c759; }
      .vc-tag-pdf { background: rgba(255,204,0,.15); color: #b8860b; }
      .vc-tag-chart { background: rgba(188,140,255,.15); color: #bc8cff; }
      
      .vc-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-bottom: 12px; }
      .vc-badge-green { background: rgba(52,199,89,.15); color: #34c759; }
      .vc-badge-blue { background: rgba(0,122,255,.15); color: #007aff; }
      .vc-badge-yellow { background: rgba(255,204,0,.15); color: #b8860b; }
      .vc-badge-red { background: rgba(255,59,48,.15); color: #ff3b30; }
      .vc-badge-gray { background: rgba(142,142,147,.15); color: #8e8e93; }
      
      .vc-examples { background: var(--bg-card-alt); border-radius: 8px; padding: 14px; margin: 12px 0; }
      .vc-examples p { margin: 4px 0; font-size: 12px; color: var(--text-muted); }
      .vc-examples code { background: rgba(0,0,0,.15); padding: 1px 6px; border-radius: 4px; font-size: 11px; }
      
      .vc-schedule-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 12px; }
      .vc-schedule-item { background: var(--bg-card-alt); border-radius: 8px; padding: 12px; font-size: 12px; }
      .vc-schedule-item .sched-icon { font-size: 16px; margin-bottom: 4px; }
      .vc-schedule-item .sched-name { font-weight: 600; font-size: 12px; }
      .vc-schedule-item .sched-time { color: var(--text-muted); font-size: 11px; }
      .vc-schedule-item .sched-cron { font-family: monospace; font-size: 10px; color: var(--text-muted); margin-top: 2px; }

      .vc-health-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; }
      .vc-health-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
      .vc-health-dot.online { background: #34c759; }
      .vc-health-dot.offline { background: #ff3b30; }
      .vc-health-dot.warning { background: #ff9f0a; }
      .vc-health-dot.loading { background: #8e8e93; animation: vc-pulse 1s ease-in-out infinite; }
      @keyframes vc-pulse { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }
    </style>
    
    <div class="vc-header">
      <h1>🎤 Voice Commands</h1>
      <p>Say these commands on Telegram to generate reports with charts and email delivery</p>
    </div>
    
    <!-- Live health status badges -->
    <div id="vcHealthBadges" style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px">
      <div class="vc-badge vc-badge-gray">⏳ Loading health status...</div>
    </div>
    <div id="vcHealthDetails" style="display:flex;flex-wrap:wrap;gap:12px;margin:-12px 0 20px 4px;font-size:11px;color:var(--text-muted)"></div>
    
    <div class="vc-grid">
      <!-- GME Reports -->
      <div class="vc-card">
        <div class="vc-card-header">💰 GME Reports</div>
        <div class="vc-card-body">
          <div class="vc-command">
            <div class="vc-cmd-voice">"Generate GME report"</div>
            <div class="vc-cmd-what">Bar chart + category pie chart + PDF + email</div>
            <div style="display:flex;gap:4px;margin-top:4px">
              <span class="vc-tag vc-tag-telegram">📱 Telegram</span>
              <span class="vc-tag vc-tag-email">📧 Email</span>
              <span class="vc-tag vc-tag-pdf">📄 PDF</span>
              <span class="vc-tag vc-tag-chart">📊 Chart</span>
            </div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"Show me GME spending"</div>
            <div class="vc-cmd-what">Quick GME snapshot by resident</div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"Who still has GME funds left"</div>
            <div class="vc-cmd-what">Only shows residents with remaining balance</div>
          </div>
        </div>
      </div>
      
      <!-- Coverage Reports -->
      <div class="vc-card">
        <div class="vc-card-header">📅 Coverage Reports</div>
        <div class="vc-card-body">
          <div class="vc-command">
            <div class="vc-cmd-voice">"Generate coverage report"</div>
            <div class="vc-cmd-what">Today's shifts + absences + future coverage status</div>
            <div style="display:flex;gap:4px;margin-top:4px">
              <span class="vc-tag vc-tag-telegram">📱 Telegram</span>
              <span class="vc-tag vc-tag-email">📧 Email</span>
              <span class="vc-tag vc-tag-pdf">📄 PDF</span>
            </div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"What's the coverage gap"</div>
            <div class="vc-cmd-what">Unassigned shifts needing attention</div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"Who's on call this week"</div>
            <div class="vc-cmd-what">Weekly call schedule overview</div>
          </div>
        </div>
      </div>
      
      <!-- Absence Reports -->
      <div class="vc-card">
        <div class="vc-card-header">🤒 Absence Reports</div>
        <div class="vc-card-body">
          <div class="vc-command">
            <div class="vc-cmd-voice">"Generate absence report"</div>
            <div class="vc-cmd-what">Absence trend chart + department breakdown + PDF</div>
            <div style="display:flex;gap:4px;margin-top:4px">
              <span class="vc-tag vc-tag-telegram">📱 Telegram</span>
              <span class="vc-tag vc-tag-email">📧 Email</span>
              <span class="vc-tag vc-tag-pdf">📄 PDF</span>
              <span class="vc-tag vc-tag-chart">📊 Chart</span>
            </div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"Who called out today"</div>
            <div class="vc-cmd-what">Quick list of today's absent staff</div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"Absence trends this week"</div>
            <div class="vc-cmd-what">Line chart showing absence volume by day</div>
          </div>
        </div>
      </div>
      
      <!-- Consolidated -->
      <div class="vc-card">
        <div class="vc-card-header">📊 Full Reports</div>
        <div class="vc-card-body">
          <div class="vc-command">
            <div class="vc-cmd-voice">"Generate full report"</div>
            <div class="vc-cmd-what">ALL data — GME, coverage, absences — charts + PDF + email</div>
            <div style="display:flex;gap:4px;margin-top:4px">
              <span class="vc-tag vc-tag-telegram">📱 Telegram</span>
              <span class="vc-tag vc-tag-email">📧 Email</span>
              <span class="vc-tag vc-tag-pdf">📄 PDF</span>
              <span class="vc-tag vc-tag-chart">📊 3 Charts</span>
            </div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"Email me the full report"</div>
            <div class="vc-cmd-what">Generates full report + sends to your email with PDF attachment</div>
          </div>
          <div class="vc-command">
            <div class="vc-cmd-voice">"Send the report to (email)"</div>
            <div class="vc-cmd-what">Generates and emails to a specific address</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Scheduled Reports -->
    <div class="vc-card" style="margin-bottom:20px">
      <div class="vc-card-header">⏰ Scheduled Reports (Auto-Delivered via Cron)</div>
      <div class="vc-card-body">
        <div class="vc-schedule-grid">
          <div class="vc-schedule-item">
            <div class="sched-icon">💰</div>
            <div class="sched-name">Monday GME Report</div>
            <div class="sched-time">7:00 AM · Every Monday</div>
            <div class="sched-cron">0 7 * * 1</div>
          </div>
          <div class="vc-schedule-item">
            <div class="sched-icon">📅</div>
            <div class="sched-name">Friday Coverage Report</div>
            <div class="sched-time">8:00 AM · Every Friday</div>
            <div class="sched-cron">0 8 * * 5</div>
          </div>
          <div class="vc-schedule-item">
            <div class="sched-icon">🤖</div>
            <div class="sched-name">Telegram Slash Commands</div>
            <div class="sched-time">/gme · /coverage · /absences</div>
            <div class="sched-cron">On-demand via telegram_report_handler.py</div>
          </div>
        </div>
        <div class="vc-examples">
          <p style="margin-bottom:6px"><b>💡 Example responses:</b></p>
          <p>"Generate full report" → <code>Bar charts + absence trend + PDF saved to reports/</code></p>
          <p>"Email me the GME report" → <code>Chart + PDF attached via Gmail</code></p>
          <p>"Send the report to jessie@montefiore.org" → <code>Emailed directly</code></p>
          <p style="margin-top:8px"><b>📋 Also available on the Manager Command Center page</b></p>
        </div>
      </div>
    </div>
    
    <!-- Manager Commands Reference -->
    <div class="vc-card">
      <div class="vc-card-header">🎮 Manager Commands (Dashboard Only)</div>
      <div class="vc-card-body" style="font-size:12px;line-height:1.7">
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px">
          <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/coverage</code> — Today's call + gaps</div>
          <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/team</code> — Resident list with status</div>
          <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/approve</code> — Pending actions</div>
          <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/gap</code> — Uncovered shifts</div>
          <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/today</code> — Who's where now</div>
          <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/swap</code> — Pending swaps</div>
        </div>
      </div>
    </div>
  `;

  // Load live health status after rendering
  loadVoiceHealth();
}

/**
 * Poll /api/status for report generator and system health.
 * Updates the live badges in the voice commands page.
 */
async function loadVoiceHealth() {
  const badges = document.getElementById('vcHealthBadges');
  const details = document.getElementById('vcHealthDetails');
  if (!badges) return;

  try {
    const status = await api.getStatus();

    // System overall status
    const sysHealthy = status.status === 'healthy';
    badges.innerHTML = `
      <div class="vc-badge ${sysHealthy ? 'vc-badge-green' : 'vc-badge-red'}">
        ${sysHealthy ? '✅' : '❌'} System: ${status.status}
      </div>
      <div class="vc-badge vc-badge-green">📊 ${status.skills_count || 0} skills</div>
      <div class="vc-badge vc-badge-blue">📧 Email Delivery: Ready</div>
    `;

    // Agent details
    const agents = status.agents || [];
    details.innerHTML = agents.map(a => {
      const dotClass = a.status === 'online' ? 'online' : a.status === 'warning' ? 'warning' : 'offline';
      return `<span class="vc-health-row">
        <span class="vc-health-dot ${dotClass}"></span>
        ${a.name}: ${a.status}
      </span>`;
    }).join('') + `
      <span class="vc-health-row" style="color:var(--text-muted);font-size:10px">
        Uptime: ${Math.floor((Date.now()/1000 - status.uptime) / 60)} min
      </span>
    `;
  } catch (e) {
    badges.innerHTML = `
      <div class="vc-badge vc-badge-red">❌ Health endpoint unreachable</div>
    `;
    details.innerHTML = `<span class="vc-health-row" style="color:#ff3b30">Failed to poll /api/status: ${e.message}</span>`;
  }
}
