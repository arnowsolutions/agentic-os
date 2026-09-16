# AI Design Intel — September 15, 2026
Sources scanned: X (available — 4 queries returned live results), Reddit (JSON API blocked across all 6 subs — HTML login wall returned instead of JSON; ALL subs covered via web_search), HN (unavailable — hnrss.org returned 502 Bad Gateway on all 3 queries, same as Sept 13; partial HN coverage via last30days-pro aggregator), GitHub (available — repo search + topic search + per-repo metadata API), Google News (available — RSS returned dated results). Candidates considered: 24. Passed the bar: 6.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Impeccable design skill (Bakaus) | Technique/Skill | ✅ Adopt it | 23 named commands give coding agents a real design vocabulary — and it's already ported to Hermes Agent |
| OpenPencil | Tool | ✅ Adopt it | MIT-licensed AI-native vector design tool, .op JSON files, built-in MCP server, 8 code-export targets — pushed today |
| "Claude beige" / algorithmic unilo | Idea | ✅ Adopt it | Names the exact slop wave we're about to walk into — beige, Instrument Serif, rounded cards, all identical |
| pdf-design agent skill | Tool/Workflow | ✅ Adopt it | Fixes AI documents that look like printed web pages; self-review loop renders every sheet for inspection |
| Figma Make two-way GitHub integration | Tool/Workflow | 👀 Watch it | Visual edits become real PRs against the real repo — but the core launch was May 2026, coverage is what's new |
| Figma Goldman Sachs AI roadmap | Idea | 👀 Watch it | Code Layers, Figma Agent, 50% Make price cut — signals where the canvas is heading, no adoptable artifact yet |

---
### Impeccable design skill (Paul Bakaus)
**Link:** https://github.com/pbakaus/impeccable
**Type:** Technique / Agent Skill
**What it is:** An open-source agent skill (Apache 2.0) that gives coding agents a working design vocabulary — 23 invocable commands including `bolder`, `quieter`, `distill`, `polish`, `typeset`, `layout`, `colorize`, `delight`, `overdrive`, `clarify`, `adapt`, plus `audit` and `critique` for evaluation. Each command routes to a documented playbook rather than a vague adjective. Ships four modes (Persuade, Operate, Read, Experience) selected by *surface*, not by product.
**What's good about it:** This is the most concrete answer yet to the "AI slop" problem, and the mechanism is genuinely intelligent rather than cosmetic. The core insight: engineers and designers using the same model get different results purely because designers have precise words. Impeccable compresses that professional vocabulary into something a model can act on. Crucially, "bolder" is *defined* — not gradients, glass, or neon, but hierarchy, scale, and decisive type. The skill carries a self-critique test: "Show someone your work and say AI made this bolder. If they believe you, you failed." It also caps its own perfectionism with a bounded verification pass instead of an open-ended self-QA loop.
**Pros:**
- Twenty-three commands with real procedures behind them, not prompt decoration — `bolder` and `quieter` are things art directors actually say, now each backed by a documented procedure
- Explicit anti-pattern list we can adopt verbatim: overused fonts, gray text on colored backgrounds, pure black/gray (always tint), cards nested inside cards, bounce/elastic easing as dated
- Mode-selected-by-surface is the distinction most design prompts miss — a dashboard and a campaign page should not be designed under the same rules
- The brief outranks the skill's own taste, stated as a failure condition — the client's direction wins over the tool's default
- Runs across Claude Code, Codex, Cursor, Copilot, Gemini CLI **and has already been ported to Hermes Agent**, so this is directly usable in our existing stack
- Apache 2.0 — no licensing friction for commercial department work
**Cons:**
- Bakaus himself concedes that running the identical prompt with GPT-5.5 on extra-high and *no* Impeccable installed showed only a "slight" difference. The vocabulary layer's durable advantage is his argument, not a proven result
- It is a refinement and steering layer, not a generator — it will not invent a design direction for you, and it assumes you can already tell good hierarchy from bad
- Twenty-three commands is a real learning surface; teams that skip the mode-selection discipline will get inconsistent output
- A licensed rebrand reportedly out-installs it, which muddies the version landscape if you go looking for the "real" one
- Geared toward UI/frontend code — its advice transfers to print and social creative only by principle, not by command
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This is the single most useful thing in this brief for Shareef, and the reason is specific: Impeccable's anti-pattern list is essentially a written-down version of the critique Shareef already makes by instinct — no purple-gradient AI look, no gray on color, no reflexive cards-in-cards, theme is never a default. For the Urology Unified Platform UI (premium dark, single accent, Inter, SVG icons), the `audit` and `critique` commands give us a repeatable way to check that every new surface still honors that restraint instead of drifting toward the same Inter-on-dark default that Impeccable explicitly flags — which matters because our platform legitimately *is* Inter, so the differentiator has to come from hierarchy, spacing, and decisive use of the accent rather than from the font itself. For marketing and social creative for the residency program and the Sub-I welcome materials, `bolder`/`quieter`/`delight` map directly onto real art-direction conversations, and because a Hermes port already exists, this slots into the design flow we're building rather than requiring a new harness. Treat it as the quality gate on our work, not as the idea generator.

---
### OpenPencil
**Link:** https://github.com/ZSeven-W/openpencil
**Type:** Tool
**What it is:** An open-source, AI-native vector design tool (MIT, Rust + Tauri desktop) positioned as a Figma alternative. Design files are `.op` — plain JSON, so they are human-readable, Git-friendly and diffable. Built-in MCP server (`op-mcp`) installs into Claude Code, Codex, OpenCode, Kiro or Copilot CLIs so agents can read, create and modify designs from the terminal. Features "Concurrent Agent Teams" (multiple agents working different sections in parallel with per-member canvas indicators), style-guide library with tag matching, UIKit import/export, and code export to React + Tailwind, HTML + CSS, Vue, Svelte, Flutter, SwiftUI, Jetpack Compose and React Native.
**What's good about it:** The architecture choices are what a design director would actually want. A JSON document format means design becomes reviewable in a pull request — real diffs, real version history, no binary-file blindness. The MCP server plus the CLI means the same design file is addressable by an agent and a human without exporting between tools. And a style-guide library with tag matching is the controlled-generation signal we look for: it constrains output to declared styles rather than leaving the model to freestyle. It also imports `.fig` files, so existing Figma work isn't stranded.
**Pros:**
- MIT licensed, 5,935 stars, actively developed — repo pushed the same day as this brief (Sept 15)
- `.op` JSON format is Git-diffable and human-readable; design variables generate CSS custom properties, so tokens travel with the design
- Built-in MCP server with one-click install into the major agent CLIs — no Node.js required, stdio transport plus a live HTTP endpoint
- Eight code-export targets from a single source file, which directly serves a design-system-as-source-of-truth workflow
- Concurrent Agent Teams let several agents work separate sections in parallel — useful for multi-section page work
- Imports `.fig` and `.pen`, so it can meet existing Figma assets partway
**Cons:**
- Rust + Tauri desktop build means evaluation is heavier than opening a browser tab; this is not a five-minute try
- The repository carries a sponsored model-API banner and Discord-run community support — no vendor SLA behind it
- "World's first" claims and a large feature surface on a young project (created Feb 2026) invite the usual open-source maturity risk
- Style-guide presets like glassmorphism and brutalist are exactly the kind of named-look shortcuts that produce sameness if used as a starting point rather than a constraint
- Concurrent agent teams are an impressive demo and an unproven editorial model — parallel generation is a coherence risk for brand work
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** The Git-diffable `.op` format is the specific thing that makes this worth Shareef's time. Our entire Unified Platform workflow already treats code as the source of truth, with design tokens and components as the shared contract — a design tool whose native file *is* reviewable JSON closes a gap we currently paper over with exported assets and screenshots. For the Urology platform's card-based grids and its SVG icon set, the UIKit import/export and design-variable-to-CSS-custom-property path means a change to a spacing or accent token can propagate as a real diff rather than as a re-export. The MCP server is the other half: because it addresses `.op` files over stdio or a local HTTP endpoint, an agent can work on the same design file the designer has open, which is the practical version of "design and code in one environment." Use the style-guide library as a *constraint* (declare the Montefiore navy and single-accent system, then let the agent work inside it) and not as a preset picker — the brutalist and glassmorphism presets are the trap here, not the feature.

---
### "Claude beige" / algorithmic unilo
**Link:** https://finance.biggo.com/news/2f5a42f720e6d734
**Type:** Idea
**What it is:** Paul Bakaus's framing — now circulating widely — that AI slop is not a fixed aesthetic but a *moving target*. The purple gradients that defined 2022–23 AI output are gone from frontier models; what replaced them is "Claude beige": Instrument Serif (often italic) headlines, warm beige/tinted backgrounds, rust-red accents, tracked-out serif subheads, rounded nested cards, eyebrow text and ticker bars. The failure mode of this is not ugliness — it's sameness. Bakaus calls it "algorithmic unilo"; Anish Acharya's summary of the same talk uses "algorithmic Uniqlo or IKEA."
**What's good about it:** This is the most useful diagnostic idea published this week, and it directly contradicts how most teams defend their AI output. The usual defense is "it doesn't look like AI" — but Bakaus's point is that the tells moved, and the new tell is *competence plus uniformity*. He also offers the causal explanation that matters for tooling: the purple gradient era came from Tailwind's default color palette, and each rejected aesthetic just migrates the model to the next nearest cluster in latent space. Separately, the a16z writeup of the same talk notes the structural limit — LLMs were trained on the *output* of humanity, not the input, so they know what good design looks like but not what led to it. That's the cleanest statement of why taste remains the human's job.
**Pros:**
- Names a specific, checkable pattern (beige grounds, Instrument Serif italic, rust accents, rounded nested cards) so we can audit our own work against it rather than relying on a vague "does this look AI" feeling
- Reframes the goal correctly: the target is not "not ugly," it's "not interchangeable with everything else shipping this month"
- Explains *why* the tells move (framework defaults → latent-space attractors), which means we can predict the next wave instead of reacting to it
- Corroborated independently — the Carly substack notes Claude Design's house style already reads as recognizable, and quotes Itay Dreyfus: "these are the aesthetics we've been maintaining for years, thus this is what the model throws out"
- The "trained on output, not input" observation justifies keeping a human art director in the loop on principle rather than sentiment
**Cons:**
- The analysis is a diagnosis with no prescription — Bakaus explicitly refuses to ship an "auto" mode or solve taste, so there's no setting to change and no product to install
- The underlying talk is from July 2026 (AI Engineer World's Fair); the September 10 article is *new coverage* of an established position, so this is not a fresh capability, and anyone treating it as news is late
- Naming a trend accelerates it as a counter-trend — "avoid Claude beige" can itself become a shared look, which is the same trap one level up
- "Algorithmic unilo" is memorable but unfalsifiable as stated; there's no threshold for when consistency becomes sameness
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef this functions as a slop-detection instrument, and it lands at the exact right moment. He is building a department-wide social media and marketing program on the side, which means a high volume of AI-assisted creative — precisely the volume at which a house look silently becomes an algorithmic-uniformity problem. The actionable move is to add these specific tells to the QA gate: warm beige grounds, Instrument Serif italics, rust-red accents, rounded nested cards, eyebrow text. The Montefiore brand system already pushes us away from the beige wave — navy #003da5 is a committed, saturated brand color rather than a tinted neutral — so the platform and campaign work is structurally protected. The real exposure is the social creative and any generated hero imagery, where the model's default palette will try to pull toward the current attractor. Note too that the "portrait-first" and "real photos, light #f5f5f0" decisions for campaign work read as correct against this analysis: they are choices, and choices are what stops signaling the absence of a decision.

---
### pdf-design agent skill
**Link:** https://github.com/Georgi45/pdf-design
**Type:** Tool / Workflow
**What it is:** An agent skill (MIT) that fixes the specific failure where an AI asked for "a nice PDF report" returns a web page sent to the printer — white frame around every page, a cover floating in the middle of an A4, pages that stop halfway. It teaches the agent to lay out one fixed-size sheet at a time with full-bleed backgrounds, real embedded vector text, built-in `editorial`/`warm`/`dark` themes (brand = one small CSS file), and a self-review step where a print script measures every page — content cut off, text over the footer, half-empty pages, missing fonts — and renders a PNG of each sheet for the agent to actually look at before delivering.
**What's good about it:** It solves a problem by *closing the loop*, not by adding a template. The root cause is correctly identified: browsers don't have pages, so printing HTML gives you a website on paper. The fix — fixed-size `<section class="sheet">` elements with their own backgrounds, `@page` injected at exact sheet size with zero margins, fonts and images embedded because Chrome prints before web fonts load — is real print-production thinking, the kind of detail that separates designed documents from generated ones. The self-review is the premium signal: the agent has to look at a rendered PNG of every sheet, so "here is your PDF" with a broken page 4 stops being an acceptable ending. Text stays selectable and searchable vector text rather than screenshots glued into a page.
**Pros:**
- Explicit self-review loop with measurable output (`[WARN] Sheet 3: empty gap of 34 % (82 mm)`) — the agent gets flagged and must fix before handing over
- Real vector, selectable, searchable text with embedded fonts, not flattened screenshots — matters for anything a client or trainee will search
- Brand is one small CSS file with a `data-theme` pointer, and fonts download via a script, so our palette drops in without forking the skill
- Requires only Node 22+ and an existing Chrome — no npm install, no headless-browser setup
- Uses genuinely good typefaces in its own examples (Fraunces, Instrument Sans), signalling the author thinks about typography rather than defaulting
- Plain HTML in, so the design stays editable by the agent and reprintable
**Cons:**
- Very new and essentially unvetted — 4 stars, single-author repo created September 10, 2026, one commit. This is an idea worth stealing more than a dependency worth adopting blindly
- `claude.ai` support is explicitly experimental (needs Chromium in the sandbox); the reliable path requires an agent with a terminal
- Limited to three built-in themes and A4/A4-landscape/16:9 formats — anything unusual is on you
- The bundled example fonts pull toward the same Instrument-Serif-adjacent territory the "Claude beige" finding warns about, so the defaults are not the safe choice
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** Shareef's operations run on generated documents — the reimbursement tip sheet, CE:Full HTML reports, chief residents' meeting materials, Sub-I welcome packets — and the platform's own standard is that data lands in the inbox and reads well there rather than behind a link. This skill targets exactly the gap between "competent HTML page" and "designed document," and it does so with the discipline we keep asking for: one idea per sheet, a sheet plan shown before building, full-bleed backgrounds, and a mandatory visual inspection of every rendered page. The workflow it teaches is worth adopting even if the skill itself gets forked — for a Sub-I welcome packet or a paper-ready reimbursement sheet, "the agent must look at a PNG of each page before it hands anything over" is the practice we want in the loop regardless of which tool implements it. For the Big Reef Chapter Player's polished light theme, the PDF export path is a secondary benefit; the primary value is that documents stop looking like web pages. Keep our own palette in the CSS file rather than using the shipped themes.

---
### Figma Make two-way GitHub integration
**Link:** https://venturebeat.com/technology/are-designers-the-new-swes-figma-makes-new-two-way-github-integration-turns-designs-into-live-production-code-with-built-in-governance
**Type:** Tool / Workflow
**What it is:** Figma Make gains the ability to import an existing Git repository into the Figma desktop app, let you visually edit the application's underlying code on the canvas, and push changes back to engineering as standard GitHub pull requests. It moves the tool from a one-way prototyping sandbox into a local development environment that operates inside normal version control. The multi-model AI toggles between Claude Sonnet, Claude Opus and Google Gemini models; Supabase integration provides backend, secret storage and Postgres; it is available to Full seats at $16–$90/month.
**What's good about it:** The governance framing is the part a design director should care about. Visual AI edits accumulate as local commits and ship as pull requests, so they pass through the same CI, security checks and code review as any engineering commit — no shadow design-to-code channel. It anchors generated code to the existing design system (color tokens, typography rules, component variants, auto-layout), which is the difference between generating a lookalike and extending a system. And the practical win is real: working locally against the repo the team actually ships from means changes can merge, instead of producing code an engineer has to rebuild against the real codebase.
**Pros:**
- Pull-request-based workflow means visual edits are reviewed like any other change; no unreviewed path into production
- Reads and applies the existing design system — tokens, type rules, component variants — rather than inventing a parallel style
- Two-way sync ends the drift between a design sandbox and the shipping repository
- Supabase integration supplies backend, secrets and Postgres, so a prototype can become a real application
- Model-agnostic across Anthropic and Google models, reducing lock-in to a single vendor's output style
**Cons:**
- **The core launch is not new** — Figma's own blog post for the local-code capability is dated May 28, 2026. What's current is the September press/analysis cycle, not the capability. Treat the VentureBeat framing as commentary with a commercial motive
- Figma is in a defensive posture: the stock sits far below its IPO pricing and the piece reads partly as a case for Figma's relevance against Lovable and Claude Design
- It is a frontend optimization tool for mid-to-large cross-functional product teams, not a general builder — narrow fit
- Requires access to the company codebase, meaning real onboarding and permissions work before any value
- Model toggling may produce inconsistent code style across a codebase if teams don't standardize on one
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** The direction is exactly right for the Unified Platform, which is a React application with a real design-system contract and a live production surface — the governance model (visual change as a reviewed PR) is precisely how we would want any canvas-based edit to reach production. The reason this is Watch rather than Adopt is honesty about dates: the capability announced in the September coverage shipped in May, so there is no new thing to adopt this week, only a clearer articulation of what it means and a vendor under visible pressure to defend its position. For Shareef's surfaces the near-term relevance is limited — the platform work is already code-first, and the marketing and Sub-I creative don't live in a repository at all. What's worth tracking is whether Figma's design-system adherence becomes reliable enough that a canvas edit to a token or component can be trusted to propagate correctly. If it does, it becomes a genuine upgrade path for the platform's card grids and icon system. Revisit when there is a concrete version, not a press cycle.

---
### Figma Goldman Sachs AI roadmap
**Link:** https://investing.com/news/transcripts/figma-at-goldman-sachs-communacopia--technology-conference-2026-ai-push-93CH-4892556
**Type:** Idea
**What it is:** Figma used the Goldman Sachs Communacopia + Technology Conference (September 8, 2026) to outline an AI-assisted design and development push. CEO Dylan Field described Code Layers — code sitting directly on the canvas next to design elements, already drawing strong customer interest pre-launch — plus Figma Agent and new AI features aimed at both designers and non-designers. Figma cut Figma Make credit pricing by roughly 50% in some cases, prioritizing volume over near-term margin. Field stated that frontier models are improving but quality, hallucination and design-system adherence remain major gaps, and that Figma is not trying to replace designers — rather to lower the barrier to entry while raising the ceiling for professionals.
**What's good about it:** Field's stated position on model limitations is unusually candid for an earnings-adjacent appearance and matches what the practitioner community is saying: design-system adherence is still the unsolved problem, and that is exactly where premium work lives. The "lower the floor, raise the ceiling" framing is the correct read of the market — as AI makes competent design ubiquitous, the differentiated 10–20% becomes the entire competitive field, which is good news for anyone who can actually art-direct. The 50% price cut also makes the Figma Make tooling materially cheaper to evaluate, which is a practical consideration for department spend.
**Pros:**
- Candid public acknowledgment that design-system adherence remains a major model gap — useful confirmation when justifying human review of AI output
- Code Layers puts code on the canvas next to design, addressing the handoff problem structurally rather than with process
- Explicit "not replacing designers" positioning, with AI aimed at raising the professional ceiling — aligned with how we want to use these tools
- Roughly 50% Make credit pricing cut lowers the cost of experimentation
- Gives visibility into where the canvas is heading, which informs how much to invest in canvas-based workflows at all
**Cons:**
- This is an investor-conference transcript, not a product release — no adoptable artifact, no version, nothing to evaluate today
- Code Layers is pre-launch and described by interest level, not capability; "strong interest" is not a shipped feature
- Price cuts at an IPO-stage company under margin scrutiny are as much a competitive and financial signal as a product decision
- Roadmap items delivered via conference remarks are the least reliable form of a product commitment
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Worth tracking as context rather than as an action item. Two things here genuinely matter to Shareef's decision-making. First, Field naming design-system adherence as an unresolved gap is the clearest vendor-side confirmation that generated UI still cannot be trusted to respect a system like ours — the Unified Platform's premium dark theme, single accent and SVG icon discipline are exactly the properties that erode when a model generalizes. That supports keeping human review as a hard gate rather than a nice-to-have. Second, the pricing shift lowers the real cost of evaluating Figma Make for prototyping work on Sub-I materials and client-style site concepts. The reason this stays at Watch is straightforward: a conference transcript is a promise, and Code Layers has not shipped. The single most useful thing to note is the strategic direction — Figma is betting the canvas remains the best abstraction layer above commoditized code, and is building AI into it so the design system, not the prompt, constrains the output. If that lands, it's the right shape for how we work. Until it ships, it's a data point, not a tool.

## Slop Radar
- **"Claude beige" — the current wave:** warm beige/tinted grounds, Instrument Serif italics, rust-red accents, tracked-out serif subheads, rounded nested cards, eyebrow text. It reads as competent, not ugly, which is exactly why it spreads. Audit generated creative for these specific tells rather than for "does this look AI."
- **Competence-as-sameness:** the new failure mode is not a bad design, it is the *same* design. If every AI-assisted asset we ship shares one look, the look stops being a decision and starts signalling the absence of one — and it underperforms because it doesn't stand out.
- **Framework defaults masquerading as palette:** the purple-gradient era traced back to Tailwind's default color palette. Any time we accept a tool's shipped default theme, we are inheriting someone else's attractor. Declare colours, never accept them.
- **Screenshot-glued documents:** PDFs and decks where the page is an image of a layout rather than designed vector text. Unsearchable, unselectable, soft in print, and impossible to edit — the document equivalent of a flattened export.
- **Named-look presets:** style-guide shortcuts offered as starting points (glassmorphism, brutalist, retro) reproduce the same convergence problem at the tooling layer. Use style systems as constraints, not as choosers.

## Overall Assessment
The most important shift visible this week is not a new tool — it is a correction in how the field is talking about AI design quality. The conversation has moved off "which model generates the nicest image" and onto two more useful questions: what vocabulary lets a human actually steer an agent (Bakaus's 23 commands, now ported to Hermes Agent), and how do we recognise slop when it no longer looks like slop ("Claude beige," algorithmic unilo). Both point the same direction — the differentiator is no longer generation capability, which is commoditizing fast, but the quality of the steering layer and the specificity of the human judgement going into it. Against that backdrop, Shareef's highest-leverage move this week is to adopt Impeccable's anti-pattern list as the house QA gate and add the "Claude beige" tells to it — one document, two sources, immediately applicable to every surface he owns. It costs nothing, requires no new tool, and converts the sharpest thinking in the field this week into a checklist that stops our output from converging on the current default. The second move, if there's room, is to open OpenPencil and evaluate whether the Git-diffable `.op` format is a real fit for the platform's token and component workflow — that one is a genuine architectural decision and deserves deliberate evaluation rather than a snapshot judgement.

-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-09-15.md — PENDING VERIFICATION
Email: PENDING
Vault: PENDING
