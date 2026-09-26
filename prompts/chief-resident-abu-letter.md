# Annual ABU Chief Resident Confirmation Letter

Reusable template for the Program Director's confirmation letter that every
chief resident needs each year for the American Board of Urology Qualifying
(Part 1) Examination.

Latest generated set: 2026-2027 cycle (John Hill, John Hordines, So Yeon Pak).

## What the Board requires, verbatim

> A letter from you, the Program Director, confirming that the applicant is
> expected to successfully complete at least six months as chief resident by
> June 30, `<EXAM_YEAR>`, must be received in the Board office by January 1,
> `<EXAM_YEAR>`. In addition, a Program Director's Evaluation Form for each
> resident who has applied for the exam will be emailed to you and/or your
> residency coordinator in late January for completion by March 1, `<EXAM_YEAR>`.

## How to run it (Agentic OS)

**Resident Letters page → Letter Type → "ABU Chief Resident Confirmation (annual)"**
→ pick the exam year → **Generate Letter**. One `.docx` per chief is produced
with a download link.

Equivalent command line:

```bash
cd /workspace/agentic-os
python3 letterhead_letters.py --list-years                 # cohorts + current chiefs
python3 letterhead_letters.py --exam-year 2027 --out DIR   # build the batch
```

## The rules that make this work

1. **Never rebuild the letterhead.** The department's Word file already carries
   the Montefiore/Einstein banner, the department block and Dr. Sankin's
   signature. `letterhead_letters.py` copies
   `data/letterhead/Residency_Program_Letterhead_-_Alex_Sankin.docx` and writes
   only the body between the `Date:` line and the `Thank You` closing. Everything
   else in the file — header, signature image, credential block — is copied
   byte-for-byte.
2. **Wording lives in `data/letter_templates/abu_chief_confirmation.json`**, not
   in code. Edit the JSON to change the letter; placeholders are
   `{name}`, `{last}`, `{exam_year}`, `{start_year}`.
3. **The recipients come from the canonical roster**, never a hardcoded list:
   `unified.chief_meeting_attendees` (`role='chief'`) joined to
   `public.contacts` (PGY, graduation year, program start).
4. **Verify the fit by rendering.** The credential block is ~11 lines, so a
   long letter spills onto a second page with the letterhead repeating over the
   orphan lines. The template's body fits one page at ~26 rendered lines.
5. **The salutation is `To Whom It May Concern:`** — not a named addressee
   (changed 2026-09). Do not revert it to "Dear Executive Director".

## Deadlines to watch

| Item | Due |
|---|---|
| Confirmation letter in the Board office | January 1 of the exam year |
| Program Director's Evaluation Form | March 1 of the exam year |
| Qualifying (Part 1) Examination | mid-July of the exam year |

## Signature block (do not regress)

The block under Dr. Sankin's signature is:

```
Montefiore Medical Center                              <- bold
The University Hospital for Albert Einstein College of Medicine
Montefiore Hutchinson Campus
1250 Waters Place, Tower One, Penthouse
Bronx, New York 10461
347-842-1700 Office
267-980-4606 Mobile
917-962-5410 Fax
```

The as-received template wrongly carried the residency coordinator's cell
(929-696-3195) as "Cell" and the program switchboard as "Office". Corrected
2026-09-25; the pristine original is archived at
`data/letterhead/originals/`. Confirm any phone number against the CRM contact
record before trusting a template — `public.contacts.mobile` is the authority.

## Do not add

No exam dates, no invented claims about a resident's performance, licensure or
credentials. The "in good standing" clause in the first paragraph stays — it is
the Program Director's professional attestation carried by his signature (no
resident table records standing; the only status is `category`: `Resident` vs
`Archived`). Only what the Board asks for and what the roster records.
