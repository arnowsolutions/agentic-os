async function renderCalendar() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">📅 Calendar of Events</div>
        <div class="page-subtitle">Dr. Sankin vacation dates, call schedule events & upcoming department activities</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderCalendar()">🔄 Refresh</button>
      </div>
    </div>
    <div id="calendarContent">
      <div class="loading"><div class="loading-spinner"></div><span>Loading calendar data...</span></div>
    </div>
  `;

  try {
    const res = await fetch('/api/calendar/events?days=365');
    const data = await res.json();
    const events = data.events || [];

    // Group events by month
    const months = {};
    events.forEach(ev => {
      const start = ev.start?.date || ev.start?.dateTime?.slice(0,10) || 'unknown';
      const monthKey = start.slice(0, 7); // YYYY-MM
      if (!months[monthKey]) months[monthKey] = [];
      months[monthKey].push(ev);
    });

    const sortedMonths = Object.keys(months).sort();

    let html = '';
    
    if (events.length === 0) {
      html = `<div class="empty-state"><div class="empty-state-icon">📅</div><div class="empty-state-title">No upcoming events</div><div class="empty-state-desc">No calendar events found for the next year.</div></div>`;
    } else {
      html = `<div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center">
        <div style="color:var(--text-muted);font-size:13px">${events.length} events over the next 365 days</div>
        <div style="display:flex;gap:8px">
          <span style="font-size:11px;padding:2px 8px;border-radius:4px;background:var(--yellow-dim);color:var(--yellow)">🏖 Vacation</span>
          <span style="font-size:11px;padding:2px 8px;border-radius:4px;background:var(--blue-dim);color:var(--blue)">📞 Call</span>
        </div>
      </div>`;

      sortedMonths.forEach(monthKey => {
        const monthEvents = months[monthKey];
        const [y, m] = monthKey.split('-');
        const monthName = new Date(parseInt(y), parseInt(m)-1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        
        html += `<div class="card" style="margin-bottom:16px">
          <div class="card-header" style="font-size:16px;font-weight:600;padding:12px 16px;border-bottom:1px solid var(--border);background:var(--bg-card-alt)">
            ${monthName}
            <span style="float:right;color:var(--text-muted);font-size:13px;font-weight:400">${monthEvents.length} event${monthEvents.length > 1 ? 's' : ''}</span>
          </div>
          <div style="padding:0">`;

        monthEvents.forEach(ev => {
          const start = ev.start?.date || ev.start?.dateTime?.slice(0,10) || '—';
          const end = ev.end?.date || ev.end?.dateTime?.slice(0,10) || '';
          const summary = ev.summary || 'Untitled Event';
          const desc = ev.description || '';
          const source = ev.source || '';

          // Format date range for display
          let dateStr = start;
          if (end && end !== start) {
            // For all-day events, Google returns end date as exclusive (day after last day)
            const endDate = new Date(end + 'T12:00:00');
            endDate.setDate(endDate.getDate() - 1);
            const endStr = endDate.toISOString().slice(0,10);
            if (endStr !== start) {
              dateStr = `${start} → ${endStr}`;
            }
          }
          
          // Determine event type badge
          const isVacation = summary.toLowerCase().includes('vacation') || summary.toLowerCase().includes('sankin');
          const isCall = summary.toLowerCase().includes('call');
          let badge = '';
          if (isVacation) {
            badge = '<span style="font-size:11px;padding:2px 8px;border-radius:4px;background:var(--yellow-dim);color:var(--yellow);margin-left:8px;white-space:nowrap">🏖 Vacation</span>';
          } else if (isCall) {
            badge = '<span style="font-size:11px;padding:2px 8px;border-radius:4px;background:var(--blue-dim);color:var(--blue);margin-left:8px;white-space:nowrap">📞 Call</span>';
          }
          
          const sourceLabel = source === 'manual' ? '<span style="font-size:10px;color:var(--text-muted);opacity:0.5;margin-left:6px">(manual)</span>' : '';
          
          html += `<div style="padding:10px 16px;border-bottom:1px solid var(--border-light);display:flex;align-items:flex-start;gap:12px">
            <div style="min-width:36px;text-align:center;padding:4px 0">📌</div>
            <div style="flex:1;min-width:0">
              <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px">
                <strong style="font-size:14px">${summary}</strong>${badge}${sourceLabel}
              </div>
              <div style="font-size:12px;color:var(--text-muted);margin-top:4px">
                📅 ${dateStr}
              </div>
              ${desc ? `<div style="font-size:12px;color:var(--text-muted);margin-top:4px;opacity:0.7">${desc}</div>` : ''}
            </div>
          </div>`;
        });

        html += `</div></div>`;
      });
    }

    document.getElementById('calendarContent').innerHTML = html;

  } catch (err) {
    document.getElementById('calendarContent').innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Failed to load calendar</div>
        <div class="empty-state-desc">${err.message}</div>
      </div>`;
  }
}
