# Active Projects

## Agentic OS (Current)
- Status: Building Phase 1
- Priority: HIGH
- Building complete agent orchestration platform
- 8 phases planned

## CloudMart
- Status: Active (ongoing)
- GCP DevOps multi-region e-commerce platform
- GKE Autopilot, Cloud SQL, Cloud CDN, Istio, Next.js

## Vapi Voice Assistant — Montefiore Urology
- Status: Active / Iterating
- Priority: HIGH
- Shareef's personal AI voice assistant for call handling, schedule lookups, staff rosters
- Backend: FastAPI bridge on port 8090, Cloudflare quick tunnel → Vapi.ai
- Data sources: Call_Schedule xlsx, QGenda CSV export, associates.csv, Drive-sync'd location rosters
- Tools registered: verifyCaller, getTodaySchedule, scheduleByDate, getWeekendSchedule, getPersonSchedule, getPersonMonth, qgendaToday, qgendaUpcoming, qgendaWhere, staffAtLocation, staffFind, knowledgeSearch, submitSickCall, takeMessage, getWeather, getNews, swapCall, scheduleMeeting, getDeadlines, getEvaluationsDue, emailSchedule, emailStaffRoster, queryLocationRoster
- PH2 = Penthouse 2 (support-staff location, not a call campus)
- Location-roster source = urologyresidencyprogram@gmail.com Drive folder
- Interim email policy: all emails go to SCHEDULE_EMAIL_RECIPIENT env var; flip to per-caller lookup at go-live
- Data health dashboard: GET /api/vapi/data-health shows per-source status (ok/missing/stale/parse_error/auth_required)

### Pending: New Caller Info-Capture Flow
- Currently: takeMessage gathers caller info ad-hoc after auth failure
- Next: structured flow that captures name, phone, email, reason, callback preference, urgency in a guided conversation
- Not yet designed — waiting on Shareef feedback
