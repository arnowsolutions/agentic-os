#!/usr/bin/env python3
"""Build the AI brief HTML email from the markdown brief."""
import re
from pathlib import Path

SRC = Path("/workspace/agentic-os/data/briefings/ai-brief-2026-09-23.md")
OUT = Path("/tmp/ai-brief.html")

md = SRC.read_text()

lines = md.split("\n")
html_parts = []
i = 0
in_table = False
in_ul = False
first_para_done = False

def close_lists():
    global in_ul, in_table
    if in_ul:
        html_parts.append("</ul>")
        in_ul = False
    if in_table:
        html_parts.append("</table>")
        in_table = False

def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t

while i < len(lines):
    line = lines[i].rstrip()
    s = line.strip()

    # Table
    if s.startswith("|"):
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not in_table:
            close_lists()
            html_parts.append('<table>')
            in_table = True
            html_parts.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
        elif all(set(c) <= set("-: ") for c in cells) and cells:
            pass
        else:
            html_parts.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        i += 1
        continue
    else:
        if in_table:
            html_parts.append("</tbody></table>")
            in_table = False

    if not s:
        close_lists()
        i += 1
        continue

    if s == "---":
        close_lists()
        html_parts.append('<hr>')
        i += 1
        continue

    m = re.match(r"^(#{1,6})\s+(.*)$", s)
    if m:
        close_lists()
        lvl = len(m.group(1))
        txt = m.group(2)
        if lvl == 1:
            html_parts.append(f'<h1>{inline(txt)}</h1>')
        elif lvl == 2:
            html_parts.append(f'<h2>{inline(txt)}</h2>')
        else:
            html_parts.append(f'<h3>{inline(txt)}</h3>')
        i += 1
        continue

    if s.startswith("- "):
        if not in_ul:
            html_parts.append("<ul>")
            in_ul = True
        html_parts.append(f"<li>{inline(s[2:])}</li>")
        i += 1
        continue
    else:
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False

    if s.startswith(">"):
        html_parts.append(f"<blockquote>{inline(s[1:].strip())}</blockquote>")
        i += 1
        continue

    # Paragraph — merge consecutive non-blank, non-special lines
    buf = [s]
    j = i + 1
    while j < len(lines):
        nxt = lines[j].strip()
        if not nxt or nxt.startswith(("#", "-", "|", ">", "---")):
            break
        buf.append(nxt)
        j += 1
    html_parts.append(f"<p>{inline(' '.join(buf))}</p>")
    i = j

close_lists()

body = "\n".join(html_parts)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI &amp; Hermes Brief — September 23, 2026</title>
<style>
  body {{
    margin: 0; padding: 0;
    background: #f5f5f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    line-height: 1.6;
  }}
  .wrap {{ max-width: 760px; margin: 0 auto; padding: 24px 16px 56px; }}
  .card {{
    background: #ffffff;
    border: 1px solid #e0e0da;
    border-radius: 10px;
    padding: 32px 34px 40px;
  }}
  h1 {{
    font-size: 25px; line-height: 1.25; margin: 0 0 6px;
    color: #003da5; letter-spacing: -0.3px;
  }}
  .kicker {{
    font-size: 12px; text-transform: uppercase; letter-spacing: 1.1px;
    color: #6b6b66; margin-bottom: 18px;
  }}
  h2 {{
    font-size: 17px; margin: 34px 0 10px; color: #003da5;
    border-bottom: 2px solid #003da5; padding-bottom: 6px;
  }}
  h3 {{
    font-size: 19px; margin: 34px 0 10px; color: #111;
    letter-spacing: -0.2px;
  }}
  h3::before {{
    content: "";
    display: block; width: 34px; height: 3px;
    background: #003da5; margin-bottom: 12px;
  }}
  p {{ margin: 0 0 14px; font-size: 15px; }}
  ul {{ margin: 0 0 16px; padding-left: 20px; }}
  li {{ margin-bottom: 7px; font-size: 15px; }}
  strong {{ color: #111; }}
  code {{
    background: #f0f0ec; padding: 1px 5px; border-radius: 4px;
    font-family: "SFMono-Regular", Consolas, monospace; font-size: 13px;
  }}
  hr {{ border: 0; border-top: 1px solid #e8e8e2; margin: 30px 0; }}
  blockquote {{
    margin: 0 0 16px; padding: 10px 16px;
    border-left: 3px solid #003da5; background: #f7f9fc;
    font-size: 15px; color: #333;
  }}
  table {{
    width: 100%; border-collapse: collapse; margin: 16px 0 26px;
    font-size: 14px;
  }}
  th {{
    text-align: left; background: #003da5; color: #fff;
    padding: 9px 10px; font-size: 12.5px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.4px;
  }}
  td {{
    padding: 9px 10px; border-bottom: 1px solid #e8e8e2;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #fafaf7; }}
  .foot {{
    margin-top: 26px; padding-top: 16px; border-top: 1px solid #e0e0da;
    font-size: 12.5px; color: #6b6b66;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>AI &amp; Hermes Brief</h1>
    <div class="kicker">September 23, 2026 &nbsp;·&nbsp; Big Reef daily scan &nbsp;·&nbsp; window: Sept 16–23, 2026</div>
    {body}
    <div class="foot">
      Generated automatically from GitHub API, Hacker News RSS, Google News RSS, Reddit, and web search.
      Every item verified against a live source within the last 7 days. No padding, no recycled entries.
    </div>
  </div>
</div>
</body>
</html>
"""

OUT.write_text(HTML)
print(f"Wrote {OUT} ({len(HTML)} bytes)")
