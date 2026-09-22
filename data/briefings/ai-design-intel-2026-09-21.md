# AI Design Intel — September 21, 2026
Sources scanned: X (available — site:x.com queries returned results for "AI design" tool, Midjourney prompt design, "design director" AI, AI typography/generative design, Figma AI plugin), Reddit (all 6 subs blocked via JSON — datacenter IP 429/HTML wall; substituted site:reddit.com web_search for graphic_design, UI_Design, midjourney, StableDiffusion; r/webdesign and r/DesignSystems surfaced via web search), HN (available — hnrss newest q=AI design / q=generative design / q=typography), GitHub (available — 5 search queries: ai+design, topic:generative-art, topic:design-tools, topic:image-generation, ai+design 30-day), Google News (available), last30days-pro aggregator (HN 8 / GitHub 5 / Web News 8). Candidates considered: 27. Passed the bar: 6.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| @shadcn/lint | Tool | ✅ Adopt it | Turns your design-system rules into machine-verifiable errors agents must obey — enforcement, not prompting |
| Awwwards-mcp | Tool / Workflow | ✅ Adopt it | Gives agents curated award-winning references + design DNA + motion recording; kills the "invent from nothing" default |
| Primitives (Dusk Research) | Tool | ✅ Adopt it | Precision design instruments (contrast, type scale, measure) — computational craft instead of eyeballed guesses |
| Open Design System Bench | Tool | 👀 Watch it | Measures how AI-ready your component library actually is; early but the right question |
| figma-font-handler | Tool | 👀 Watch it | Feeds real licensed local fonts to AI assistants — attacks typographic slop at the source |
| Keyline | Tool | 👀 Watch it | Figma rules → agent resolves the right component instead of dumping the whole file; single-commit v0 |

---

### @shadcn/lint
**Link:** https://github.com/shadcn-ui/lint
**Type:** Tool
**What it is:** An agent-first linter for Tailwind design systems from shadcn. You declare what's allowed in your system (which classes a component may carry, which variants exist, which theme tokens are permitted); when an agent violates a rule, the lint error explains what broke and suggests the correct component/variant/token from your actual system. Works with Tailwind v4 (shadcn/ui not required), available for both ESLint and Oxlint.
**What's good about it:** This is the correct architectural answer to AI design slop: don't ask the model nicely — make the wrong thing a build error. The README's own framing is the point: TypeScript can tell an agent that `padding` is not allowed on a Button, but it cannot tell it *how to size the Button*. `@shadcn/lint` closes that gap by reading your components, variants, and theme to produce a fix suggestion alongside the violation. The team validated across 150+ agent task runs, with almost every task reaching zero violations in one correction round, and measured fix cost 10–48% lower than AGENTS.md rules alone (Claude control runs). That is a real, quantified craft gain — not a demo.
**Pros:**
- Converts design-system policy from prose guidance into a verifiable, enforced gate — the single hardest problem in agent-generated UI
- Errors carry system-specific remediation (your components, your variants, your theme), so agents self-correct in one round instead of thrashing
- Zero-rewrite adoption: works on existing Tailwind v4 projects, monorepo-aware (`settings.shadcn.ui` + per-app theme config), MIT licensed
- Actively shipped — releases and parser fixes landing through Sep 20, 2026 (theme parsing past comments, scoped color namespaces, exports patterns)
**Cons:**
- Tailwind-only. The Unified Platform and Big Reef Chapter Player are not Tailwind component libraries, so this is not a drop-in for your current React surfaces
- Rule authoring is real design work — you must first be able to state your system precisely enough to encode it, which is the hard part most teams skip
- Fast-moving, 18 commits in its first week; rules/config shape may still churn before it settles
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** The most valuable thing here is not the linter — it's the pattern, and the pattern is directly portable to every Shareef surface. Today our anti-slop defense in agent work is prose: the "Signs of AI Design" rules file we adopted on Sept 19, AGENTS.md-style instructions, and my own review pass. Prose is advisory; a linter is enforced. `@shadcn/lint` proves you can encode a design system as machine-checkable constraints and get measurably better agent output for it. For the Urology Unified Platform — navy #003da5 as the single accent, Inter, SVG icons, a fixed grid — the equivalent move is a small project-specific check set: forbid non-token hex literals, forbid accent colors outside the palette, forbid arbitrary spacing values off the scale, require icon stroke consistency. That is a weekend of work that permanently raises the floor on every agent-authored component, and it is exactly what a design director at a top agency means by "systems thinking." This pairs with the design-rules file we already have: rules tell the agent what to avoid, the linter proves it obeyed. Adopt the tool where Tailwind applies; adopt the pattern everywhere else without waiting.
---

### Awwwards-mcp
**Link:** https://github.com/INSANE0777/Awwards-mcp
**Type:** Tool / Workflow
**What it is:** A free, open-source MCP server (v1.6.0, first stable release Sep 19) that hands coding agents real design references from award-winning websites: search with inline screenshots, "design DNA" extraction, page-structure band maps, and motion recording of live sites. Self-described as a Mobbin alternative; no API key required. Ships with companion skills (`motion-study`, `video-to-superprompt`) and a showcase of three full sites built with it.
**What's good about it:** It addresses the actual root cause of generic AI output — the model has no references, so it regresses to the mean of its training data (purple gradients, the same hero, the same card grid). This feeds it a curated, award-jury-scored corpus instead. The details show unusual care: it parses Awwwards' *per-dimension jury scores* (design / usability / creativity / content, weighted 40/30/20/10) so an agent can weigh references by judged quality rather than by likes; it probes for parser drift against committed HTML fixtures so it fails loudly when Awwwards changes markup rather than silently returning garbage; and it enforces politeness constraints (1 req/s, robots.txt paths) so it isn't a scraper that gets the user blocked. The `motion-study` skill with layered-analysis lenses and a superprompt hand-off is real art-direction tooling, not a wrapper.
**Pros:**
- Supplies curated, jury-scored references — the highest-signal anti-generic input you can give an agent, with quality weighting baked in
- Captures motion, which almost no reference tool does — directly relevant to premium web work and to our motion-design principles
- Honest engineering: 134 green fixture tests, drift detection, no false alarms on cosmetic changes, light runtime deps, MIT
- Free and keyless — no subscription gate on the reference library, and the skills ship in-repo
**Cons:**
- Single maintainer, 44 stars, one fork — bus factor of one, however disciplined the commit history
- It is a scraping layer over Awwwards' public HTML; if Awwwards fights back, the tool degrades (the drift probes help, but don't eliminate the risk)
- Reference-rich does not mean taste-rich: an agent with 500 beautiful sites can still produce pastiche. Without a strong brief it will imitate rather than art-direct
**Why:** For Shareef's marketing and client-facing surfaces this is the strongest input change available this week. The residency program marketing creative, Sub-I welcome materials, and premium client-style websites all suffer from the same failure mode: the agent has no reference vocabulary, so everything comes back looking like everything else. Feeding it Awwwards-grade references with a design DNA breakdown moves the output from "AI page" toward "someone with taste looked at good work first." The motion recording matters specifically for the Big Reef Chapter Player, where state transitions and scroll behavior define whether it reads as premium or as a template. I would adopt it as a discovery step, not a generation step: pull 3–5 references, extract the DNA (type scale relationships, grid rhythm, color restraint, motion timing), then art-direct our own thing against those measurements. Use it to *steer*, never to copy — the value is the reference vocabulary, and the moment an agent is told to "make it look like this site" we have simply traded one form of generic for another. Adopt with that discipline attached.
---

### Primitives (Dusk Research)
**Link:** https://primitiv.es/ (repo: https://github.com/duskresearch/primitives)
**Type:** Tool
**What it is:** A suite of single-purpose design instruments — one question, one tool — covering the fundamentals: color contrast, type scale (with ratio control, e.g. `?ratio=1.618`), measure, units, and specimen (which previews every Google Fonts family from Fontsource, sorts by *measured* x-height and width, and supports pinning to compare and pairing suggestions). Design values live in `src/data/tokens.json`; a build script writes `tokens.css`. Everything is URL-stateful and copyable ("Copy this setup" with a confirmation stamp).
**What's good about it:** This is the opposite of AI slop by construction: it is precision instrumentation for decisions people usually eyeball. The Specimen instrument is genuinely useful craft tooling — sorting typefaces by measured x-height and width, rather than by vibe, is how a type-literate designer actually narrows a shortlist. URL-stateful instruments mean a decision is a shareable, reproducible artifact (`primitiv.es/type/scale?ratio=1.618`) rather than a screenshot in a Slack thread. The code quality signals a design-led team: tokens as the single source, MIT license, fonts under OFL, and the same house design language as their other live projects. The commit log shows an agent doing careful work *under* human review — but reviewed and corrected, which is the workflow that actually produces quality.
**Pros:**
- Computational rigor where AI design usually guesses: real measured metrics (x-height, width, OS/2 metrics cited), real contrast math, real ratio math
- Shareable URL state makes every design decision a reproducible, reviewable artifact — excellent for keeping a system coherent across sessions and vendors
- Free, MIT, no account; contrast and type-scale instruments answer questions we hit constantly (accessible hues derived from #003da5, consistent type ramp)
- Design-token-first architecture maps cleanly onto our own token discipline for the Unified Platform
**Cons:**
- Very early and small — 2 stars, ~32 commits, single org; treat it as a working reference implementation, not infrastructure to depend on
- The instruments are intentionally narrow; you will not get an integrated system out of it, just excellent single-purpose answers
- No Figma bridge — values must be moved between tools by hand, which is where drift creeps in
**Why:** The single most useful anti-slop move available on this list, and it costs nothing. Generic AI output is generic partly because nobody computes anything: contrast gets eyeballed, the type ramp gets invented per page, the measure drifts, and spacing comes from whatever the model felt like. Primitives makes those decisions quantitative and repeatable. Concretely for Shareef: deriving accessible tints/shades from the Montefiore navy #003da5 that hold up against #f5f5f0 and dark surfaces, locking one type scale for the Unified Platform and reusing it rather than re-inventing per feature, and choosing a display face for residency marketing by measured x-height instead of by whoever suggested it loudest. Adopt the contrast and type/scale instruments immediately as reference tools; do not adopt the repo as a dependency. For a design director's brief, "we computed it" is the difference between a system and a mood board.
---

### Open Design System Bench
**Link:** https://github.com/christophhdesign/open-design-system-bench
**Type:** Tool
**What it is:** A plug-in benchmark that measures how AI-ready a design system is: it runs coding agents against your React + TypeScript component library on a defined task set, then grades the output. Tasks live in `tasks/` YAML; generating agents get Read/Glob/Grep/Edit/Write only (no Bash, no web) with `--strict-mcp-config` so project MCP servers can't leak into cells; a `hiddenExpectations` field lets a judge hold an expected-components catalog. Includes a static audit, generation graders, and generic fixtures, generalized from a production design system.
**What's good about it:** It asks the question almost nobody measures: not "is our design system good," but "can an agent actually use it correctly." That's the real bottleneck — most systems are documented for humans and hostile to agents (ambiguous component names, undocumented variants, no machine-readable intent), and the failure surfaces as inconsistent generated UI. The methodology is unusually rigorous for a benchmark: deterministic grading against git-diffed scratch repos, hidden expectations withheld from the generating agent, a reserved `context: mcp` phase for before/after-MCP KPI comparison, and an explicit principle that where a system genuinely lacks a component the benchmark *surfaces* the gap rather than papering over it. Reporting is designed to be read, with authored report contracts and a worked example.
**Pros:**
- Measures AI-readiness as an empirical score rather than a feeling — you can track whether a system change helped
- Clean methodology (isolated generating agent, hidden expectations, frozen baselines) makes results comparable across systems and over time
- The `context: mcp` phase, once shipped, will let us quantify whether an MCP layer actually improves output — a real decision input
- MIT, TypeScript, generic fixtures — adaptable to our component library rather than tied to theirs
**Cons:**
- React + TypeScript only; not applicable to marketing/print/social surfaces or to Figma-side work
- Requires an already-well-structured component library to bench meaningfully — running it against a messy system mostly measures the mess
- Last release and substantive commits are late August / early September; the September changelog documents a release but the repo isn't moving daily
**Why:** File this as the evaluation instrument for our own design system, not as a design tool. If we seriously intend for agents to build Urology Platform UI components — and we do — then whether the system is legible to an agent is a first-class design question, exactly like whether it's legible to a new hire. The 4-commit history and 50 stars mean we should not depend on it; we should steal its method. Their task-YAML + hidden-expectations + diff-grading structure is a template we can implement shallowly for our own components: a handful of canonical component-assembly tasks, a small expected-outcome list, run it before and after any system change, and see whether agent output actually improved or whether we just reshuffled tokens. That replaces opinion with evidence, which is how a design system earns authority inside an organization. Watch the repo; adopt the method now.
---

### figma-font-handler
**Link:** https://github.com/yannicschaer/figma-font-handler
**Type:** Tool
**What it is:** An MCP server plus Figma plugin that gives AI assistants access to the fonts actually installed on your machine, via Figma Desktop. Exposes `list_fonts`, `audit_fonts`, `set_font`, `replace_font`, `set_text`, and `execute`; `replace_font`/`set_font` preserve weights (Bold→Bold) where the target family carries them, and the `mapping` field reports exactly what was substituted. Derived from Strand AI's figma-slides-mcp (MIT), with the Slides tooling replaced by new font tooling; WebSocket bridge on :3056.
**What's good about it:** Typography is where AI design most visibly fails, and one reason is that the agent simply cannot see your fonts — so it reasons about type in the abstract and produces the tells we read as slop (wrong weights, collapsed hierarchy, fallback substitutions nobody chose). This gives the model ground truth: what is installed, what loads, what a replacement actually mapped to. `audit_fonts` is the quietly important tool — it reports fonts that are *listed* but *fail to load*, which is precisely the class of bug that ships silently and then renders as Times New Roman in front of a client. The author's own commit notes ("Verified live in Figma Desktop: plugin loads, list_fonts and audit_fonts work against a real file with locally installed fonts") plus a mock-Figma-API test suite and CI on Node 20/22 suggest a tool built by someone who has been burned by this before.
**Pros:**
- Solves a real, high-visibility failure: AI-driven type work against licensed, locally-installed fonts with correct weight mapping and transparent substitution reporting
- `audit_fonts` catches listed-but-unloadable fonts — a genuine pre-flight check for client-facing deliverables
- Reuses a proven MCP↔WebSocket↔plugin bridge (figma-slides-mcp) rather than inventing one; MIT, testable without Figma via mocks
- Single-purpose by design — no attempt to become a platform
**Cons:**
- Tiny and new — 1 star, 4 commits, one author, one week old; unproven under real load
- Requires Figma **Desktop** and a running assistant session; the plugin panel showing "Not connected" when no session is running is a confusing default (acknowledged and rewritten in the latest commit, but the friction is real)
- Mac/Windows/Linux font enumeration through Figma Desktop will always be a moving target as Figma changes its plugin host
**Why:** Watch it, but fix the *problem* now because we already have it. Our system runs on Inter across the Unified Platform, and any Figma work feeding those surfaces needs the agent to reason from the real font inventory, not from an imagined one. The slop this prevents is the boring kind that reads as unprofessional: an agent substituting a weight that doesn't exist, collapsing a hierarchy it can't see, or shipping text set in a fallback because a family never loaded. The tool is too early to depend on, but its two ideas are ready to adopt immediately — (1) give agents authoritative access to the actual font set before they touch type, and (2) build a load audit into the pre-flight for anything client-facing. So: watch the repo, and in the meantime encode "verify every declared font family actually loads, in every weight and style used" as a ship gate on Sub-I materials, residency marketing, and platform typography. That is a checklist item today and a tool later.
---

### Keyline
**Link:** https://github.com/TANISHQBAFNA/keyline
**Type:** Tool
**What it is:** A Figma-rules system for agents: you define design rules in Figma, and Keyline resolves the correct component for an agent — `npm run keyline -- resolve "Component Name"` — instead of dumping the entire Figma file into context. Ships as a Claude Code plugin (`.claude-plugin`), plus configs for Cursor, Cline, Windsurf, and OpenCode, with a Figma plugin and an MCP path (Figma MCP is the default route; no personal access token needed for normal use). The README is explicit about the division of labor: Keyline resolves components, *"You review for taste — Keyline is not the taste judge."* MIT, public release Sep 20, 2026.
**What's good about it:** The target is a real and under-served failure: an agent handed an entire Figma file drowns in context, hallucinates component names, hardcodes hex values, and re-invents components that already exist. Resolving *one right component per request* is the correct scope. Two signs of design maturity: it explicitly refuses to be the arbiter of taste (a discipline most AI design tools lack), and it ships rule files for six different agent harnesses out of the box rather than betting on one vendor. The graph-visualization path (`npm run dev`, sample data, no login) shows the author expects a designer to inspect and correct the mapping rather than trust it blind.
**Pros:**
- Correct problem framing: component *resolution* rather than file *ingestion* — less context, fewer hallucinations, less token burn
- Explicitly taste-neutral by design; the human reviews, the tool resolves — the right division of labor for a design system
- Works across Claude Code, Cursor, Cline, Windsurf, and OpenCode with shipped rule files; MIT
- Lightweight and inspectable — a graph view for the human, a resolve command for the agent
**Cons:**
- v0 in the most literal sense: 1 star, one commit, published yesterday, tagged as a "privacy-scrubbed" initial release
- Requires Figma MCP wired into your agent harness plus a reasonably structured Figma library — if the library is a mess, resolution is a mess
- No track record; the resolve quality across a large real library is entirely unproven
**Why:** Worth knowing about; not worth wiring up yet. The reason it earns a line in this brief is the design principle, which is right: a design system's job is to make the correct component the *easy* one to reach. When an agent can't find your Button, it invents one — and that invented Button is where slop enters the codebase, carrying its own padding, its own radius, its own hex. Resolving the real component by name is how you keep agents inside the system. This is the same thesis as `@shadcn/lint` from the other direction: lint makes violations visible after the fact; resolution prevents them before. For the Unified Platform, where we have a defined component vocabulary and a strong design system, a resolve-style layer is eventually the right architecture. But at one commit and one star, Keyline is a sketch. Note the pattern, revisit it in a month, and in the interim keep the discipline the README itself names: the agent resolves and builds, the human judges the taste. Never hand that second half to the model.
---

## Slop Radar
- **"AI design reference" tools that ship a gallery but no opinion** — dumping 500 beautiful sites into context produces pastiche, not art direction. References must arrive with a brief and a rule set, or they lower taste rather than raise it.
- **Cracked-software repos dressed as "AI-powered design software"** — this week's GitHub results were full of "AutoCAD-Cracked / Illustrator-Cracked / CorelDRAW-Cracked" listings using "AI-powered" as bait. Never a legitimate tool; a malware vector wearing a design label.
- **API-gateway spam masquerading as model releases** — a cluster of `*-api-gateway-*` repos (Nano Banana Pro, Grok Image, GPT-Image 2.5, Midjourney pricing) all created in the last five days by near-identical accounts. Zero craft content; pure reseller SEO. Ignore entirely.
- **"Prompt = complete visual identity" threads** — the recurring X format claiming one prompt yields a full brand system. It produces a mood, not a system, and it collapses the moment it meets a second surface or a real accessibility requirement.
- **Design benchmarks that generate agents can trivially game** — any evaluation visible to the model being evaluated measures compliance, not quality. Keep expectation sets hidden (the one thing Open Design System Bench gets right).

## Overall Assessment
This week's findings share one thesis, and it is the right one: the industry is moving from *asking* models to produce good design toward *constraining* them until good design is the path of least resistance. `@shadcn/lint` makes design-system violations a build error with a remediation attached. Awwwards-mcp replaces the model's default zero-reference aesthetic with jury-scored reference vocabulary. Primitives computes what AI design usually guesses. Keyline and figma-font-handler both work the same seam — give the agent ground truth about your components and your fonts so it stops inventing substitutes. That is the maturation pattern we want: less prompt poetry, more systems enforcement, measured (150+ agent runs; 10–48% cheaper fixes) rather than asserted. The countervailing risk is equally clear — reference galleries and benchmarks can become new forms of sameness if they replace a point of view instead of informing one, which is why Keyline's own README line ("You review for taste — Keyline is not the taste judge") is the most important sentence in this brief. **The single highest-leverage move for Shareef this week:** adopt the *enforcement pattern* behind `@shadcn/lint` against the Unified Platform directly — a short, project-specific rule set that fails on non-token hex values, accent colors outside navy #003da5, spacing off the scale, and inconsistent icon stroke weight, wired into the pre-flight for any agent-authored UI. We already tell agents what to avoid; this week we make it non-negotiable. Everything else on this list is an input improvement. That one is a floor.
-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-09-21.md — verified written (25,398 bytes, 6 items)
Email: Email sent: AI Design Intel — September 21, 2026
Vault: Vault: added 6 item(s) → 1414 total (2026-09-21).
