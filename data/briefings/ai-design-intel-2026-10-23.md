# AI Design Intel — October 23, 2026
Sources scanned: X (available via web search — 2 phrasings returned results, but mostly undated articles; no dated within-week X threads confirmed, so no X-only items are claimed), Reddit (r/graphic_design, r/UI_Design, r/midjourney via web_search — JSON API blocked by HTML interstitial on all 6 subs incl. r/web_design, r/FigmaDesign, r/StableDiffusion), HN (hnrss newest, 3 queries — thin: newest "AI design" hit is Oct 14), GitHub (search API + topic queries), Google News RSS (2 queries). Candidates considered: 14. Passed the bar: 6.

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| Canva Craft | Tool | 👀 Watch it | Two-stage "plan the composition, then render" — the first mainstream model whose architecture is an art director's job description |
| Noo–Studio: Designing Icons With AI | Workflow / Idea | ✅ Adopt it | The most useful document published this week on keeping an AI-assisted drawing set coherent enough to be a real family |
| Figma agent GA + Specs / Guidelines | Tool | ✅ Adopt it | Brand rules as versioned Markdown that the agent must read before it draws — that is the anti-slop mechanism we have been improvising |
| Webflow Campaigns | Tool | 👀 Watch it | Brand-system extraction into DESIGN.md is the right idea; extracting from a live page means it inherits the site's drift |
| aislopmeter | Tool | 👀 Watch it | Scores the exact tells we ban by name and cites file:line — useful as a pre-ship gate, dangerous as a taste oracle |
| kangarooking/design-skills | Workflow | ❌ Skip it | Two skills, Chinese-language, holiday-poster and blind-box specific; the *shape* of the idea is already better developed in our own skills |

---
### Canva Craft
**Link:** https://www.canva.com/newsroom/news/canva-craft/
**Type:** Tool
**What it is:** Canva Research's first from-scratch image model, launched October 22, which splits generation into two stages: a planning model that writes out what elements appear, their spatial relationships, relative scale, visual hierarchy and any text, then a rendering model that draws that plan at up to 2K across 30+ aspect ratios. Live now in Dream Lab for all Canva users, plus a public API.

**What's good about it:** The architecture is the story, not the leaderboard placement. Every image model until now has been asked to solve composition and rendering in one pass, which is why text lands crooked and hierarchy drifts — it was never told there *was* a hierarchy. Craft separates the two, and in doing so makes the plan itself an artifact you can argue with. The training data is also the correct bet: millions of human-made templates from Canva's library rather than photographs, "unlike flat images, these templates teach the model exactly how layout, hierarchy, and typography fit together." Typography is modelled explicitly before a pixel is rendered, and the JSON boundary boxing feeds Canva's Magic Layers so the output becomes editable elements instead of a flat JPEG. That last part is the difference between a mood board and a working file.

**Pros:**
- Composition and typography are decided as a structured plan *before* rendering — which is precisely the order a designer works in, and the reason it can hold legible text and precise object placement.
- Editable output via Magic Layers means a generated asset can be handed to a human for typesetting rather than being regenerated to fix one word — the single biggest failure mode designers complain about with image generators.
- Trained on templates, not photos; fine-tuned with adversarial human comparison where "when automated evaluations and human judgments differed, we sided with the designer."
- Public API and a coming MCP server make it usable inside real pipelines, not just as a browser toy.

**Cons:**
- It is still a *design-sauce* model aimed at people who need a flyer by Thursday. A composition plan optimised for a template library trends toward template competence, not distinctive art direction.
- Ranked fourth on DesignArena behind three GPT-Image variants — and DesignArena is crowdsourced, which means it measures appeal to the crowd, not to a creative director.
- Sitting inside Canva means the gravity is toward Canva-shaped output: polished, centred, safe, and entirely familiar. Nothing in the launch materials suggests a point of view.
- Brand-new, day-old, no independent craft assessment yet; fine print and technical drawings are explicitly named as still weak.

**Should we...**
- 👀 **Watch it** — promising, not proven yet

**Why:** The interesting claim here is not "better images" — it is that a model can hold a composition spec in its head and then execute it, which is the first architecture that resembles how a real design team works. For Shareef that matters in exactly one place today: the marketing and social creative for the residency program, where the recurring problem is not generating a picture but getting text, logo and a consistent grid into one frame without a regeneration roulette. The Magic Layers path is the one to test — generate the ground image, let the model hold the negative space for the headline, then set the actual type ourselves. But the template-trained DNA is the thing to be suspicious of: a model taught on a quarter-billion Canva designs will reproduce the median of that library, and the median of that library is competently generic. Use it as a rendering hand, never as the eye. If our own type and grid go in at the plan stage, this is a genuine production accelerant for the Sub-I welcome materials and social tiles. If we let it compose, we will ship something that looks like it came from Canva, because it did.

---
### Noo–Studio — Designing Icons With AI
**Link:** https://noo-studio.com/paper/designing-icons-with-ai
**Type:** Workflow / Idea
**What it is:** A 72-minute, unusually honest studio paper from Piotr Paweł Zalewski documenting how Noo–Studio built a 116-icon (then 165-icon) variable icon font in about three days, with a Claude agent writing the drawings in Python, fontTools compiling the font, headless Chrome rendering each proof, and a *second* Claude agent reviewing with separate tests and no right to edit. The icons download free.

**What's good about it:** It answers the question every designer asks about AI-generated icon sets — why don't they read as a family? — with a mechanical answer rather than a vibe. A set reads as one family when every member obeys the same few decisions: one grid (24 units, 20 live), one stroke per weight taken from the studio's own typeface stems (2 units at Regular, 0.92 Thin, 2.94 Bold), one family of corners, at least one visible unit of white between any two parts, one optical size. Those decisions were written as numbers *before* the first icon was drawn, and then enforced by the build: "the build of Noo Icons refuses any icon whose parts come closer than one unit at any weight, any cut that leaves its solid, any contour that crosses itself and any ink outside the live area." Six checks run on every icon at every master and stop the build before a font is written. And the paper keeps the disagreement on the record — the reviewer's findings ("the first moon read as a face, the flat rings as a bowl, engine as a birthday cake") stayed in the report with the designer's objections and reasons.

**Pros:**
- Turns "consistency" from an adjective into a build that can fail. This is the difference between AI-assisted and AI-unsupervised, and it is repeatable on any icon or mark system we build.
- The two-agent separation — one draws, a different one judges with no edit rights — is a governance pattern, not a prompt trick, and it is portable to every design workflow we run.
- Concrete, transferable numbers: grid, live area, stroke-per-weight derived from the typeface, one unit of white. These are the levers that make a set cohere.
- Files are downloadable and the whole thing is open enough to read the prompts. It is a case study, not a sales page.

**Cons:**
- Icons only. The same discipline will not transfer cleanly to photography or editorial layout, where the "law" is much harder to write as numbers.
- It is a small studio with an agent-friendly setup (Python, fontTools, headless Chrome). Running this inside a Figma-only department means building the harness first.
- 72-minute read, and the middle is largely method documentation — good method, but you will skim to the numbers table and the prompts.
- Slightly self-congratulatory in tone and the icons are functional, not distinctive — this buys correctness, not character.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling

**Why:** The Unified Platform UI is named as "single accent, Inter, SVG icons" — which means the icon set *is* an identity surface, and it currently reads as whatever was handy rather than as a system. This paper gives us the missing method: define the grid, the live area, the stroke relationship to Inter, and the one-unit-of-white rule, then let the agent draw to those numbers and let the build reject the ones that miss. That is not "AI made our icons," it is a designer-authored law with an agent as draftsman, which is exactly the labour division a design director should insist on. The second reviewer agent with no edit rights is the part I would steal wholesale — it mirrors how we already work with critique, and it gives us a written record of disagreement instead of a summary that flatters the output. The Big Reef Chapter Player and the Sub-I welcome materials would both benefit from a coherent icon family built to one grid. Do not expect character from this method; expect correctness, which is the prerequisite for character.

---
### Figma agent GA + Specs and Library Guidelines
**Link:** https://help.figma.com/hc/en-us/articles/39582753756695-What-s-new-from-Config-2026
**Type:** Tool / Workflow
**What it is:** The in-canvas Figma agent left beta on October 6, 2026 (now consuming AI credits), and at Figma's first Config India event the company added Specs — a Markdown document type on the canvas for writing down requirements, design rules and agent instructions — plus Guidelines, markdown files of rules and anti-patterns attached to a design library that the agent reads on every prompt that uses that library.

**What's good about it:** This is the first mainstream design tool to admit out loud that the AI problem is a *context* problem. The agent works from your components, variables and tokens and can be steered by @-mentioning specific tokens and components; the new Guidelines layer lets a library owner write "never do this, do this, and here is why" in plain text that the agent must read before drawing. Figma's own framing is candid: AI output is non-deterministic and needs tools to steer it, and without written rules an agent produces something generic. That is the honest diagnosis, and a versioned Markdown rule file attached to a library is the most durable anti-slop artifact anyone has shipped this month. Specs also travel — they can be read by third-party agents and coding tools via MCP, which means the brand rules stop living inside one person's head or one file.

**Pros:**
- Anti-patterns as a first-class artifact. Writing down what the brand never does is exactly how a good agency style guide works, and now the machine has to read it too.
- The agent starts from your most-used components and tokens rather than from nothing, so output is variant-of-our-system rather than generative-adjacent drift.
- Specs are portable Markdown, referenceable to canvas elements and embeddable with FigJam diagrams and code layers — they survive outside Figma and outside the agent.
- Bulk maintenance prompts (standardise names, swap deprecated components, convert a flow to dark mode, replace placeholder copy) remove hours of the unglamorous work that eats craft time.

**Cons:**
- It consumes AI credits now, and per-user credit limits landed October 22 — the meter is running and that changes how freely you experiment.
- The value is entirely proportional to the quality of the guidelines you write. A vague rule file yields confident generic output with a design-system alibi.
- Figma's own launch framing is maintenance, not invention — three how-to posts about upkeep and craft. Do not expect it to generate a direction you have not already defined.
- Another place for rules to fork: if the Figma Guidelines and our code-level tokens disagree, the agent will happily obey whichever it read last.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling

**Why:** The Unified Platform is a single accent colour and Inter and a set of SVG icons — a small, strict system, which is the ideal condition for a rule-driven agent and the worst condition for an unguided one. Writing a Guidelines file for the platform that names the accent, the type scale, the icon grid, the spacing logic, and then a "never" list (no second accent, no gradient fills, no drop shadows used as hierarchy, no card-in-card), is a day of work that makes every future agent interaction land on-system instead of adjacent to it. This also solves a problem we have been handling socially rather than structurally: the moment someone else — a resident-facing marketing page, a Sub-I microsite — touches the brand, the rules travel with the library instead of living in an email. That is what a brand system is supposed to do. Treat credits as the constraint they are: use the agent for bulk edits and variants, keep the direction decisions where they belong.

---
### Webflow Campaigns
**Link:** https://webflow.com/blog/campaigns-launch
**Type:** Tool
**What it is:** A standalone Webflow product launched October 20 that takes a URL and a campaign brief, extracts the brand (colours, fonts, UI elements) into a reusable `DESIGN.md` design system, then generates a primary landing page, audience/target-account/keyword variants, and matched ad creative — pushing to Google Ads and connecting Marketo/HubSpot/Salesforce for pipeline reporting. Works alongside any CMS, and can be driven from Claude or Codex via Webflow's MCP.

**What's good about it:** The premise is right and it is where the industry is heading: one brief, one design system, many surfaces that all look like the same brand. Extracting the brand into `DESIGN.md` and handing that to agents is the correct mechanism, and the same file format now appears in three vendors' launches this month — that convergence is worth noticing. The "works alongside any CMS" decision is genuinely useful, because it means a campaign page does not require migrating the site. And the MCP route means a designer can build in their own tool and let the platform handle publishing, forms and attribution instead of forcing everything into Webflow's canvas.

**Pros:**
- Brand extraction into a portable `DESIGN.md` is the right abstraction, and it is exportable/readable rather than locked in a vendor's internal model.
- Variants per audience, account or keyword with matched ad creative means the campaign stays coherent across placements instead of drifting per channel.
- Works with any CMS and is drivable from external agents via MCP — low structural lock-in for a tool with this much surface area.
- Reporting ties sessions and conversions to pipeline in the same place, which is the part design rarely gets to see.

**Cons:**
- It extracts from the *rendered page*, not the system. One practitioner review notes that a site displaying eleven shades of blue because eight pages drifted will yield eleven tokens — the tool inherits your accumulated debt and politely calls it a system.
- It is a marketing-automation product wearing a design-system hat. The output aims at conversion competence, and conversion competence is exactly how a brand starts looking like everyone else's landing page.
- Personalised variants at scale is a noise generator unless traffic supports the split — six variants on two hundred visits tells you nothing.
- It will optimise the page while it runs, which raises the real governance question: who approves the agent's suggested changes to a live brand surface, and how fast?

**Should we...**
- 👀 **Watch it** — promising, not proven yet

**Why:** The `DESIGN.md` extraction idea is worth stealing even if we never buy the product: Write the brand rules down once, machine-readable, and let every generator read from that file. That is the same move as Figma Guidelines and the same move as the Noo build law, arriving from a third vendor in the same week — the market is converging on "written constraints, not vibes." But the failure mode is specific and it is ours: the Montefiore urology brand has lived through migrations, and a brand extracted from a live page cannot tell an intentional accent from a page that never got updated. If Shareef used this for residency recruitment campaigns, the agent would faithfully reproduce whatever the site currently *is*, including the drift. Watch for whether Campaigns can ingest a written spec instead of a URL; if it can, it becomes genuinely interesting for the campaign surfaces we run by hand today. Until then, it is a competent marketing tool, not an art-direction tool, and premium client-style websites are not something you ship out of a conversion engine.

---
### aislopmeter
**Link:** https://github.com/omergocmen/aislopmeter
**Type:** Tool
**What it is:** An MIT-licensed MCP server, CLI and bookmarklet that scores a website or web project for "slop" using 80+ rule-based checks across substance, language patterns, template design and unfinished details — then outputs per-finding fixes with exact `file:line` references, a before/after example, and a copy-as-prompt button for Claude/Cursor. Runs entirely locally, no keys, no account. Created October 17, 2026.

**What's good about it:** The check list reads like it was written by someone who has stared at a lot of generated pages. Template design flags purple gradients, glow, emoji and stock icons, Tailwind's default colours, grid backgrounds, small-caps labels above every heading, bounce and pulse motion, cards inside cards, and drift from your own `DESIGN.md`. Unfinished details catch lorem ipsum, `href="#"`, leftover chatbot scaffolding, "Vite + React + TS" in a footer, pages that are empty without JavaScript, text too small or line too long. It measures the *rendered* page with a browser when one is available — real computed contrast, fonts actually rendered, how much is centred, whether cards are truly identical — which is the right place to measure. It also produces the fix, not just the diagnosis, and calibrates deliberately: purple alone never scores heavy, and signs that a real business stands behind the page lower the score.

**Pros:**
- Rule-based and explainable rather than an LLM judge, with a documented reason: LLM-as-slop-judge agreed with human editors at κ≈0 — near chance. That is an unusually honest design decision.
- Findings cite `file:line` and ship with a prompt you can hand to Claude or Cursor, so the gap between diagnosis and fix is one click.
- Runs locally, reads only, no telemetry — usable on our own properties without shipping source anywhere.
- Bands are legible (0–19 clean, 80–100 pure slop) and configurable via a file that can exclude a check or protect a deliberate choice ("keep the purple of our logo and the hero photo").

**Cons:**
- Calibrated on 34 sites. That is a prototype sample, and the false-positive rate on a deliberately spare design will be high — austere, low-contrast editorial work trips several "unfinished details" checks by design.
- It cannot see whether the design is any *good*, only whether it is unoriginal. A page can score clean and still be dull, and score 45 and be excellent.
- Another rule file that can disagree with the design system (`DESIGN.md`) it checks against — the drift warning is also a source of drift.
- Node/MCP setup and a pre-1.0 tag set; the Turkish lists are admittedly young, and the whole thing is one maintainer's project.

**Should we...**
- 👀 **Watch it** — promising, not proven yet

**Why:** Our own slop radar is a list of patterns we ban by name — purple gradients, glow, emoji icon grids, cards in cards, small-caps kickers over every heading. This tool automates almost exactly that list and adds the one thing we keep missing: it measures the live render, so it catches the contrast and line-length failures that a visual review skims past. That makes it a plausible pre-ship gate for the marketing site and the Sub-I welcome pages, run as a smoke test rather than a scoring authority. I would not point it at the Unified Platform: a premium dark UI with intentionally restrained contrast will read as violations, and a false positive from a robot is a bad reason to change a good design. Treat it as a lint pass a junior would run — useful, faster than a human, and not the one who signs off.

---
### kangarooking/design-skills
**Link:** https://github.com/kangarooking/design-skills
**Type:** Workflow
**What it is:** An MIT-licensed collection of open-source Agent Skills (`SKILL.md` format) for AI image generation and visual design, created October 20. Two skills shipped: a Halloween poster colour-and-layout skill (four colour strategies, HEX anchors, area suggestions, hierarchy and contrast reasoning) and a 3D blind-box IP character sheet skill with Python/Pillow scripts.

**What's good about it:** The underlying idea is sound and matches where the craft is going: encode the design *decision* — colour strategy, area proportions, hierarchy, contrast — as a reusable procedure the agent must follow before it prompts anything. The halloween skill's separation of colour, style and layout into three decisions, with explicit HEX anchors and area ratios, and its insistence on generating the ground image first with reserved space for deterministic type later, is the correct professional order of operations. It also honestly states the limits: colour values and proportions are design *constraints*, not guarantees of what the model will execute, and exact text, logos and grids should be set in post. Its release standard — real generation examples and visual acceptance before declaring a skill "stable" — is a better bar than most.

**Pros:**
- Colour strategy as a decision with named strategies (accent, thematic, adjacent, complementary) and area ratios is a transferable way to brief a model, and the "generate the base image, then typeset deterministically" workflow is exactly right.
- Explicit skill-writing standards: frontmatter, trigger conditions, inputs/outputs, verification scope, and separation of real cases from desktop exercises.
- MIT, small, readable, and easy to lift the *method* from even if the skills themselves don't fit.

**Cons:**
- The two skills are a holiday poster and a blind-box collectible IP sheet. Neither maps to anything Shareef designs, and the holiday one will be out of season immediately.
- Documentation is Chinese-first; prompts, references and examples assume a Chinese-language workflow and CJK type.
- The good ideas here are already better developed in the Noo–Studio paper, which shows the same discipline with real numbers and a build that enforces them — and in our own skills, which are specific to our surfaces.
- Two skills, zero releases, one maintainer, created four days ago. Nothing here is proven.

**Should we...**
- ❌ **Skip it** — slop-adjacent, hype, or redundant

**Why:** Not sloppy work — the reasoning is real and the sequencing (decide colour and hierarchy first, generate, then set type deterministically) is a recipe we should be following — but it is redundant with far stronger material we already have. The Noo paper gives us the same "write the decisions as numbers, then enforce them" argument with an actual build that refuses bad output, and our own skills are already scoped to our surfaces. Adding a Chinese-language Halloween poster skill to a urology department's stack buys nothing except another rule file that disagrees with the others. The one thing worth keeping is the sentence about colour values being constraints rather than guarantees, which is the correct humility to bring to any prompt-driven layout tool.

---

## Slop Radar
- **Written rules as the new moat — and the new slop alibi.** Figma Guidelines, Webflow's `DESIGN.md` extraction and aislopmeter all shipped in the same week. The trap: a rule file that says "premium, modern, clean" satisfies the mechanism and produces the same generic output with a design-system receipt.
- **"Extract the brand from a live URL" drift laundering.** Systems rebuilt from rendered pages inherit every stale page and call eleven blues a design system. Anything generated from your current site will faithfully reproduce your worst legacy page.
- **Blind-box / 3D IP sheets and holiday-poster skills as the default "design skill."** The 3D collectible chibi render is the current avatar of generated-design slop — glossy, symmetrical, weightless — and it is being packaged as a reusable design capability.
- **Leaderboard legitimacy.** "Fourth most advanced model" and arena rankings are being used to stand in for art direction. Crowd preference is a measure of familiarity, not craft; a model trained on templates will win template benchmarks.

## Overall Assessment
Three separate vendors converged this week on the same conclusion, arriving independently from a Canva research lab, a Figma product team and a Webflow launch: the way to stop generative tools producing generic work is to write the decisions down as explicit, machine-readable constraints *before* anything is generated. Canva built a model that plans composition before it renders; Figma shipped a Markdown format for brand rules and anti-patterns that its agent must read; Webflow extracts a design system into `DESIGN.md` and hands that to agents. That is the industry admitting that taste cannot be prompted into existence and must instead be specified. The corollary is uncomfortable and true: whoever writes the rules owns the look, and a badly written rule file is now a more expensive failure than no rule file, because it produces confident wrongness at scale. The highest-leverage move for Shareef this week is the cheapest one on the list — write the Unified Platform's design system as a short, opinionated Markdown document: the single accent, Inter and its scale, the icon grid and stroke, the spacing logic, and a hard "never" list (second accent, gradient fills, shadow-as-hierarchy, card-in-card, emoji icon grids). Attach it to the Figma library as Guidelines so the agent reads it every time. Then steal Noo–Studio's build-law method for the icon set, which is the one asset where "consistent across all materials" is measurable. Everything else on this list is a rendering hand; that document is the eye, and the eye is the part that cannot be generated.

-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-10-23.md — verified written (27,198 bytes, 6 item breakdowns, file timestamp Oct 23 06:51)
Email: Email sent: AI Design Intel — October 23, 2026
Vault: Vault: refused 1 item(s) that must not be filed: aislopmeter — already in the vault (incl. archived/rejected) — not re-filing / Vault: added 5 item(s) → 1610 total (2026-10-23).
