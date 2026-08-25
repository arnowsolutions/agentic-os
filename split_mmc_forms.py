#!/usr/bin/env python3
"""Split the 5-page MMC Access Forms PDF into its 3 separate forms."""
import fitz, os

src = '/workspace/agentic-os/data/subi-welcome-docs/MMC_Access_Forms_for_Sub-Interns.pdf'
doc = fitz.open(src)
print("total pages:", doc.page_count)

splits = {
    "01_MIT_System_Access_Form": [0, 1, 2],     # pages 1-3
    "02_Patient_Info_Confidentiality_Agreement": [3],  # page 4
    "03_ID_Badge_EZID_Info": [4],               # page 5
}
outdir = '/workspace/agentic-os/data/subi-welcome-docs/split_mmc'
os.makedirs(outdir, exist_ok=True)
for name, pages in splits.items():
    nd = fitz.open()
    for p in pages:
        nd.insert_pdf(doc, from_page=p, to_page=p)
    path = os.path.join(outdir, name + '.pdf')
    nd.save(path)
    td = fitz.open(path)
    first = td[0].get_text().split(chr(10))[0].strip()[:70]
    print(f"{name}: {len(pages)}pg -> {path} | '{first}'")
    td.close()
doc.close()
print("done")
