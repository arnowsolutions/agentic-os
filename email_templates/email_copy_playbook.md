# Montefiore Urology — Report Email Copy Playbook

This playbook pairs with the four HTML templates in this folder. The templates are rendered by `send_report.py` from structured report data produced by `report-generator.py`.

---

## Voice & Tone

- **Direct and human.** One short greeting, then the point.
- **Professionally warm, not clinical.** Hospital admin email, not a marketing blast.
- **Numbers-forward.** Lead with the metric the recipient cares about.
- **Actionable.** Say what is attached, what needs attention, and how to follow up.
- **No redundancy.** Mention the PDF attachment once, in a single prominent callout box.

---

## How Templates Are Rendered

`send_report.build_email_html(report_type, report_data, recipient_name)` replaces simple `{{placeholder}}` tokens with rendered HTML snippets. The snippets (metrics cards, resident rows, transaction tables, etc.) are generated in code so the data is always accurate and Outlook-safe.

### Common placeholders

| Placeholder | Source |
|-------------|--------|
| `{{report_name}}` | `report_data['report_name']` |
| `{{date_str}}` | `report_data['date_str']` |
| `{{greeting}}` | Good Morning / Afternoon / Evening (ET) |
| `{{recipient_first_name}}` | CLI `--recipient-name` or default `"Team"` |
| `{{preheader}}` | Auto-generated from report name + date |
| `{{signature_html}}` | Loaded from `~/.hermes/email_accounts.yaml` |
| `{{attachment_callout}}` | Built from `report_data['attachment_name']` |
| `{{metrics_cards}}` | Built from `report_data['metrics']` (up to 4) |

### Per-report placeholders

**GME** (`gme_reimbursement_email.html`)
- `{{academic_year}}`
- `{{resident_rows}}`
- `{{transaction_table}}`

**Coverage** (`coverage_gap_email.html`)
- `{{date_range}}`
- `{{coverage_status}}`
- `{{absence_rows}}`

**Absences** (`absence_summary_email.html`)
- `{{week_start}}`
- `{{department_section}}`
- `{{absence_rows}}`

**Full** (`consolidated_operations_email.html`)
- `{{date_range}}`
- `{{gme_summary_line}}`
- `{{gme_alert}}`
- `{{coverage_summary_line}}`
- `{{absence_section}}`

---

## 1. GME Reimbursement Summary

### Subject line
```
Montefiore Urology - GME Reimbursement Report (AY 2025-26)
```

### Preheader
```
AY 2025-26 reimbursement usage by resident — PDF attached.
```

### Key metrics
- Total Residents
- GME Used
- GME Remaining
- Annual Cap/Resident

### Status labels
| Usage | Label | Color |
|-------|-------|-------|
| `< 50%` | On Track | green |
| `50-79%` | Moderate | amber |
| `80-99%` | High Usage | red |
| `>= 100%` | Cap Exhausted | red |

### Body copy pattern
> Good Morning Shareef,
> Attached is the **GME Reimbursement Report** for the 2025-26 academic year, current through June 20, 2026.
>
> Resident breakdown and approved transactions are below; full charts are in the PDF.
>
> Please reply if you need resident-level detail or have any questions.

---

## 2. Coverage Gap Analysis

### Subject line
```
Montefiore Urology - Coverage Gap Analysis (June 16 – June 22, 2026)
```

### Preheader
```
Shift coverage status and absences for the week — PDF attached.
```

### Key metrics
- Locations
- Total Shifts
- Today's Shifts
- Future Shifts

### Status logic
- **All shifts covered** (green)
- **Low future shift count** (amber)
- **No future shifts scheduled** (red)

### Body copy pattern
> Good Afternoon Team,
> Attached is the **Coverage Gap Analysis** for June 16 – June 22, 2026. It covers scheduled shifts, current absences, and any coverage gaps that need attention.
>
> Reply if you need schedule changes or have coverage concerns.

---

## 3. Absence Summary Report

### Subject line
```
Montefiore Urology - Absence Summary Report (Week of June 16, 2026)
```

### Preheader
```
Sick-call entries, pending approvals, and late call-outs — PDF attached.
```

### Key metrics
- Total Absences
- Pending
- Approved
- Departments

### Body copy pattern
> Good Morning Team,
> Attached is the **Absence Summary Report** for the week of June 16, 2026. It includes all sick-call entries, pending approvals, and late call-outs.
>
> Reply if any entries need follow-up or correction.

---

## 4. Consolidated Operations Report

### Subject line
```
Montefiore Urology - Consolidated Operations Report (June 16 – June 22, 2026)
```

### Preheader
```
GME, coverage, and absence data in one summary — PDF attached.
```

### Key metrics
- GME Used
- GME Remaining
- Future Shifts
- Absences This Week

### Body copy pattern
> Good Afternoon Shareef,
> Attached is the **Consolidated Operations Report** for June 16 – June 22, 2026. This edition combines GME reimbursement, shift coverage, and absence data into one summary.
>
> 1. **GME Reimbursement** — 8 residents tracked. Total used: $X; remaining: $Y.
> 2. **Coverage** — Z future shifts on file. All shifts covered.
> 3. **Absences** — top entries listed; full details in the PDF.
>
> Reply if you need any section expanded or have questions.

---

## Plain-text fallback rules

If a client cannot render HTML, the same structured data can be rendered with `render_report_text(report_data)` in `report-generator.py`.

- Lead with report name and date.
- List metrics as `Label: Value`.
- Use emoji flags for attention items (`✅` / `⚠️` / `❗`).
- End with: `Reply for questions. PDF attached.`

---

## CLI usage

Generate a report and email it:

```bash
python3 /workspace/agentic-os/report-generator.py \
  --type gme \
  --email sfrasier@montefiore.org \
  --recipient-name "Shareef"
```

Send a pre-built PDF with structured data:

```bash
python3 /workspace/agentic-os/send-report.py \
  --pdf /workspace/agentic-os/reports/latest/full_report.pdf \
  --type full \
  --data /tmp/report_data.json \
  --email sfrasier@montefiore.org \
  --recipient-name "Shareef"
```

---

## Design guardrails

- **Outlook-first:** table-based layout, `role="presentation"`, no floats, no CSS Grid/Flexbox.
- **No hard-coded caps or amounts.** All dollar values and status labels come from `report_data`.
- **No placeholders leak.** `send_report._render_template()` strips any unreplaced `{{...}}` tokens.
- **One attachment callout per email.** Mention the PDF in the green box; do not repeat in the intro or footer.
- **Brand colors:** navy `#1a3a5c` headers, green `#065f46` for positive states, amber `#b45309` for moderate, red `#991b1b` for critical.
