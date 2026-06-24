# CE-Style UI/UX & Copy Review — Montefiore Urology Email/PDF Report System

**Date:** 2026-06-20  
**Scope:** Design + copywriting review of the Montefiore Urology automated report emails and PDFs.  
**Files reviewed:**
- `/workspace/agentic-os/send-report.py` (HTML email builder)
- `/workspace/agentic-os/report-generator.py` (matplotlib charts + ReportLab PDFs)
- `/workspace/agentic-os/gme_transactions.py` (transaction query helper)
- `/workspace/email-pdf-design-reference.html` (internal visual spec)
- `/home/hermeswebui/.hermes/email_accounts.yaml` (HTML signature block)
- Generated artifacts in `/workspace/agentic-os/reports/latest/gme_20260620_041047/`

**Not in scope:** code correctness, backend logic, data pipeline integrity beyond what appears in rendered output.

---

## Reviewer Personas Used

| Persona | Lens |
|---------|------|
| **Design Director (Brand & Visual Systems)** | Consistency with the approved reference, hierarchy, whitespace, color, typography |
| **Email Markup Engineer** | Client compatibility (Outlook/Gmail/Apple Mail), responsive behavior, table semantics |
| **PDF/Print Designer** | Page layout, chart fidelity, readability, page furniture |
| **Medical-Admin Copywriter** | Tone, clarity, accuracy, redundancy, accessibility of language |
| **Accessibility / UX Auditor** | Contrast, semantic structure, screen-reader considerations |

---

## Findings by Severity

### P0 — Must fix before sending to stakeholders

| ID | Area | Finding | Why it matters | Recommended fix |
|----|------|---------|----------------|-----------------|
| F-P0-01 | Email — Data accuracy | The "Annual Limit" in every resident callout is hard-coded to `$1,250.00` (`send-report.py` line 201). It does not read `annual_cap` from the resident object or `gme_summary`. | Sends potentially false financial data to the department; destroys trust; may trigger incorrect budget decisions. | Pull `annual_cap` dynamically from the resident record or `gme_summary`. Only fall back to `$1,250` when data is genuinely missing, and log/flag the fallback. |
| F-P0-02 | Email — Content mismatch | The transaction table under each resident uses headers `Date / Description / Amount`, but the only row rendered is a summary (`{count} transactions, ${total} total`). | Column headers promise line-item detail; the row contains aggregated data. Looks broken and is confusing. | Either render real transaction rows (date, description, amount) or remove the table and show a compact summary sentence. If line items are too long, link to the PDF. |
| F-P0-03 | PDF — Data fidelity | `generate_pdf` re-parses free text and skips any non-bullet line containing `:` that was already captured as a KPI (`report-generator.py` lines 569–572). This heuristic can silently drop legitimate body lines. | Important report content may be omitted from the PDF without warning. | Build a structured data model (dicts/sections) in the generator, then pass that model to both email and PDF renderers. Do not re-parse free text with heuristics. |
| F-P0-04 | Brand | Neither the email nor the PDF includes the approved Montefiore/Einstein logo. The header is plain text only. | The design reference implies a branded header; plain text looks like an unapproved internal memo rather than an official department report. | Add the approved logo image (with `alt` text and a text fallback) to the email header and PDF title area. Ensure the logo is high-resolution and host it from a reliable CDN or embed it. |

### P1 — Should fix soon (high impact, moderate effort)

| ID | Area | Finding | Why it matters | Recommended fix |
|----|------|---------|----------------|-----------------|
| F-P1-01 | Email — Status semantics | Resident status labels are `Good / Moderate / High` without context. "High" is ambiguous (high usage? high risk?). | Recipients cannot quickly assess cap risk or action needed. | Adopt the design-reference badges: `Cap Exhausted`, `On Track`, `${X} Remaining`, or `High Usage`. Make the meaning self-evident. |
| F-P1-02 | Email — Visual hierarchy | The resident callout box gives equal visual weight to "Status" and "Annual Limit", burying the actual remaining dollar amount. | The most actionable number (`$ remaining`) competes with static limit info. | Make the remaining balance the primary figure (larger, bold, color-coded); render the annual limit as smaller secondary metadata. |
| F-P1-03 | Email — Attachment discovery | The PDF attachment is mentioned only in small footer text; there is no prominent attachment callout. | Busy recipients often miss attachments, especially on mobile. | Add a highlighted attachment box near the top of the email: "📎 `gme_report.pdf` attached — includes charts and full transaction tables." Match the green attachment box in the design reference. |
| F-P1-04 | PDF — Layout fidelity | The PDF resident breakdown is rendered as plain paragraphs/bullets instead of the design reference's row layout with colored dots and percentage columns. | Harder to scan and deviates from the approved spec. | Build a resident-row Table with dot indicator, name, PGY class, used, remaining, and percent columns, matching the reference. |
| F-P1-05 | Charts — Contrast | Pie chart percentage labels use `#c9d1d9` (light gray) which is low-contrast against several slice colors and the white background. | Reduced readability, especially when printed or projected. | Use dark navy `#1a3a5c` for labels, or white labels with a dark text shadow. Verify ≥ 4.5:1 contrast. |
| F-P1-06 | Charts — Aspect ratio | PDF embeds charts at a fixed `width=6.0in, height=2.6in` regardless of the native matplotlib aspect ratio. | Distortion or excessive whitespace; long resident names in the bar chart may be truncated. | Preserve the original aspect ratio, or scale to container width with auto-calculated height. |
| F-P1-07 | Email — Client compatibility | The main card and resident callouts rely on `box-shadow` and `border-radius`, which are not supported in Outlook and many older clients. | The email will look broken or unpolished for a large share of recipients. | Use table-based cells with background colors for the card/callout effect; avoid `border-radius`/`box-shadow` on critical structural elements. |
| F-P1-08 | Copy — Redundancy | "A PDF copy of this report is attached" appears in both the intro paragraph and the footer note. | Repetitive and amateurish; wastes reading time. | Mention the attachment once, prominently, in the attachment callout box (see F-P1-03). |

### P2 — Polish & consistency

| ID | Area | Finding | Why it matters | Recommended fix |
|----|------|---------|----------------|-----------------|
| F-P2-01 | Brand — Typography | The email mixes `Times New Roman`, `Georgia`, and an `Arial` footer note. The PDF uses `Helvetica` only. | Weak brand voice; the footer in the email feels like a different document. | Standardize: Times New Roman/Georgia for email body, Helvetica for PDF. Make the email client note match the email typeface or remove it. |
| F-P2-02 | Email — Responsive | The four-column metric cells use `width:25%`; on narrow mobile screens the labels/values will wrap awkwardly. | Poor mobile reading experience. | Stack metrics vertically below ~480 px using media queries or a fluid table layout. |
| F-P2-03 | PDF — Page furniture | The PDF lacks page numbers, a running header, or the report type in the footer. | Multi-page transaction PDFs are hard to navigate and feel unfinished. | Add page-numbered footers and a running header on subsequent pages. |
| F-P2-04 | PDF — Chart placement | Charts are appended after all text rather than placed near the relevant section. | Context is lost; readers must scroll back and forth. | Insert the bar chart after Resident Breakdown, the category chart after Spending by Category, and the absence trend after Absences. |
| F-P2-05 | Charts — Color semantics | The absence chart tints the entire background red/yellow based on count thresholds. The pie chart uses an ad-hoc palette. | Inconsistent alarm language; a red background can feel alarming for normal variation. | Use a neutral background with a colored line/marker; reserve red for severe thresholds only. Unify chart palette with the brand colors. |
| F-P2-06 | Email — Preheader | No hidden preheader text is set. | Email clients will display the first line of body or fallback text, often producing an unflattering preview. | Add a hidden preheader div: "GME reimbursement summary for AY 2026–27 — PDF attached." |
| F-P2-07 | Email — Subject | The subject line uses an em dash `—`, which can be mangled by some mail servers/clients. | Subject may show garbled characters or truncation. | Use a plain hyphen or colon: `Montefiore Urology - GME Reimbursement Summary`. |
| F-P2-08 | Copy — Greeting personalization | The greeting hard-codes "Shareef" even though the script supports `--email` for other recipients. | Wrong salutation for CCs, admins, or other stakeholders. | Use the recipient's display name from the address, or default to a neutral "Team" / "Good Morning". |

### P3 — Nice to have

| ID | Area | Finding | Why it matters | Recommended fix |
|----|------|---------|----------------|-----------------|
| F-P3-01 | Accessibility | Layout tables lack `role="presentation"`; the signature contains base64 images without `alt` text. | Screen readers may announce table structure; non-visual users get no information from signature images. | Add `role="presentation"` to layout tables; add `alt=""` for decorative images and meaningful `alt` for logos. |
| F-P3-02 | Dark mode | No `prefers-color-scheme: dark` handling. | Modern clients will invert colors unpredictably, possibly turning navy text light blue on a dark background. | Add dark-mode-aware styles with `data-ogsb` and MSO conditionals. |
| F-P3-03 | Charts — Typography | Chart labels use matplotlib defaults; no Montefiore brand typeface. | Slight brand disconnect in printed materials. | Use the approved brand typeface if licensable; otherwise keep a clean, consistent sans-serif. |
| F-P3-04 | PDF — Transactions | Each resident starts on a new page in the transaction PDF, creating many short pages when a resident has few transactions. | Wasted paper/space; choppy reading flow. | Use `KeepTogether` per resident only when needed; allow normal flow across pages. |
| F-P3-05 | Email — Interactive | No CTA or link to view the report online or reply with questions. | Forces manual forwarding or follow-up emails. | Add a concise reply line or a link to the department dashboard if one exists. |

---

## Concrete Redesign Recommendations

1. **Unify the data model.** Build one structured report object (residents, metrics, transactions, sections) and pass it to both the email builder and PDF builder. Stop parsing free text to derive layout.
2. **Implement the design reference literally.** The reference HTML already shows the intended stat-card row, resident rows with badges, green attachment box, and signature hierarchy. The PDF reference shows dotted resident rows and clean transaction tables. Match them.
3. **Fix the hard-coded annual cap immediately.** All financial figures in the email and PDF must be data-driven.
4. **Redesign the charts for clarity and brand consistency.**
   - Bar chart: keep navy bars, keep the cap line, use dark readable labels.
   - Category chart: switch to a horizontal bar or donut if there are more than five categories; ensure label contrast.
   - Absence trend: neutral background, color-coded line only, no full-plot tinting.
5. **Harden the email for real clients.** Remove reliance on `box-shadow`/`border-radius`, add MSO conditional tables, add a preheader, and test in Outlook, Apple Mail, and Gmail.
6. **Improve PDF page furniture.** Add page numbers, a running header, and place charts next to their related sections.
7. **Polish the copy.** Remove redundancy, clarify status labels, neutralize or parameterize the greeting, and simplify the subject line punctuation.

---

## Final Verdict

**Status: Not ready for executive distribution without fixes.**

The system has a clear structure and generally follows the navy/white brand palette, but it carries **data-accuracy risks (P0)** and **visual fidelity gaps versus the approved design reference (P1)** that undermine its professionalism. The email is more polished than the PDF, yet both need hardening for real-world email clients and print/PDF readability.

### Fix priority

1. **P0** — dynamic annual cap, transaction-table/content mismatch, fragile PDF text parser, logo/brand mark.
2. **P1** — status badges, attachment callout, PDF resident-row layout, chart contrast/aspect ratio, Outlook compatibility.
3. **P2** — responsive metric stacking, PDF page numbers, section-aware chart placement, preheader, subject-line punctuation.
4. **P3** — accessibility attributes, dark-mode support, online CTA, transaction PDF flow.

---

*Review produced by Hermes Agent (subagent). No source files were modified.*
