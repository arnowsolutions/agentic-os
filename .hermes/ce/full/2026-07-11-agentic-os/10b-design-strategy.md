# Phase 6.10b: Design Strategy & Conversion Audit

## Product Context

Agentic OS is an internal operations dashboard for Montefiore Urology — not a public-facing product. "Conversion" in this context means: **time-to-task completion** and **user adoption across the department** (residents, faculty, managers).

## User Personas & Needs

| Persona | Primary Goal | Key Pages |
|---------|-------------|-----------|
| **Resident** | Check schedule, submit evals, view GME balance | User Portal, Eval Portal, GME Detail, On-call |
| **Faculty/Attending** | View call schedule, complete evals | Staff Schedule, Eval Portal, Calendar |
| **Program Manager (Shareef)** | Send emails, manage contacts, monitor operations | Conference Email, CRM, Email Groups, Morning Briefing |
| **Admin/Developer (Mihir)** | Monitor system, run skills, manage agents | Dashboard, System Overview, Skills, Chat |

## Conversion Bottlenecks

### 1. Resident Portal Friction
- Requires EZ ID + PIN lookup — many residents won't know their EZ ID
- No "remember me" — re-enter PIN every visit
- No direct link to resident portal from anywhere

### 2. Email Sending Anxiety
- One-click resend has no preview/dry-run mode
- No "send test to myself first" workflow
- No confirmation dialog before sending to 80+ recipients

### 3. Navigation Overwhelm
- 70+ sidebar items in 7 groups — cognitive overload
- No favorites/recent pages
- Search helps but requires knowing the page name

### 4. No Notifications/Push
- Residents don't know when new evals are assigned
- Managers don't know when emails fail
- Only Telegram integration for alerts (not all users are on Telegram)

## Design Strategy Recommendations

### Quick Wins (Week 1)
1. **Add "Remember me" to Resident Portal** — store EZ ID in localStorage
2. **Add confirmation dialog to email resend** — "Send to 88 recipients?"
3. **Add "Recently Visited" section to sidebar** — last 5 pages
4. **Pin Resident Portal link** in sidebar header

### Medium Term (Month 1)
5. **Role-based default landing page** — residents → User Portal, managers → Dashboard
6. **Notification center** — in-app notifications for eval assignments, email results
7. **Mobile hamburger menu** — unlock phone usage for residents in clinic

### Long Term (Quarter 2)
8. **Guided onboarding** — first-time user flow for residents
9. **Analytics dashboard** — which pages are used, where users drop off
10. **Email scheduling** — schedule emails to send at optimal times

## Design Strategy Score: 4.5/10

The dashboard has the right pages for each persona but lacks the UX flows that make them discoverable and low-friction. Small changes (remember me, confirmations, recents) would have outsized impact on adoption.
