# AI Design Intel — November 15, 2026
Sources scanned: X (thin — three query phrasings returned only stale 2025/early-2026 threads and engagement bait; no 7-day design-craft post cleared the bar), Reddit (all six subs blocked at JSON — an identical 190KB block page for graphic_design, web_design, UI_Design, midjourney, StableDiffusion, FigmaDesign; web_search fallback returned only multi-year-old threads), HN (hnrss.org returned 502 on all three feeds; last30days-pro HN index returned 8 hits, none design-relevant and none inside 7 days), GitHub (REST search `ai design` + 5 topic searches: typography, figma, generative-art, design-tools, image-generation), Google News (2 feeds, 93 items). Candidates considered: 34. Passed the bar: 7.

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| suzhe-ui — design method as a skill | Technique | Adopt | Encodes prohibitions and sixteen documented rejections instead of a look. |
| Inrond — Inter with a roundness axis | Tool | Adopt | Type and component radius share one parameter, with zero reflow at every setting. |
| sui-motion-graphic-reel | Workflow | Watch | A persistent "critique profile" that applies your taste before you repeat yourself. |
| MiniMax-H3-Image (open weights) | Tool | Watch | 16 reference images is real art direction — but no seeds means no brand consistency. |
| Google Pixel × Highsnobiety PIFT | Idea | Watch | Documented proof that AI works at the "visualize for the client" stage, not authorship. |
| gpucanvas — WebGPU infinite canvas | Tool | Watch | An agent-readable view of a live layout: structure as JSON, not screenshots. |
| resocket "pixeljury" + claude-resocket-plugin | Tool (claimed) | Skip | 50 stars each, two files each, zero code. Star-farmed shells. |

---

### suzhe-ui — a web design method encoded as a skill
**Link:** https://github.com/suzhe-ai/suzhe-ui · the method's origin: https://suzhe.ai · created **15 November 2026** · Apache-2.0 · 11 stars, 0 forks
**Type:** Technique / Workflow
**What it is:** A Claude Skill that encodes the web-design method behind suzhe.ai. You classify the page by **register** before designing anything — commerce for brand and shop flows, editorial for sign-in/about/share cards, separate rules for formal pages and tools — then apply that register's tight constraints: commerce gets exactly three backgrounds (white, `#f5f5f7`, black, alternating so adjacent sections never match), system fonts, one accent `#0071e3`, pill buttons; editorial gets warm paper or warm black, one serif statement, ink buttons, thin borders, no heavy shadows. Every page also gets one **signature visual** that belongs to this product and this task. Then: hide what is unavailable, help text is one sentence, motion marks state changes, effects degrade by device tier, improve incrementally instead of rebuilding.
**What's good about it:** The `rejected.md` file. Sixteen documented rejected attempts, each with the approach, the client's verdict in their own words, why it failed, the intermediate version, and the final fix. Entry one is "copying apple.com outright," and the verdict is the most useful sentence I have read this month: *"It's obviously imitating Apple's website, but the result is just okay. I can't say exactly what's wrong, it just feels a bit cheap."* That names the exact failure Shareef fights — work that is competent, expensive-looking, and cheap — and then explains the mechanism: you can copy a skeleton, but the register belongs to the page's role, not to the reference.
**Pros:**
- It encodes **prohibitions**, not just instructions. "Three backgrounds only," "one signature visual per page," "no full-bleed third-party brand colour" — negative constraints are what stop a model drifting into the default AI look, because a model will always add unless something tells it not to.
- The register system is real design thinking: same tokens site-wide, different register per page role. Identity moments get warmth; commerce gets bustle; tools get quiet. Almost nobody ships this distinction, and its absence is why institution sites read as one long undifferentiated surface.
- Sixteen rejections with client verdicts and fixes. It is the only artifact in this week's scan that *teaches* taste rather than asserting it.
- Delivered as a plugin/skill for Claude Code, so it acts at the point of generation rather than sitting in a style guide nobody opens.
**Cons:**
- Eleven stars, published today, effectively one commit. An untested single-author artifact, and "Apple-grade" is a self-applied adjective.
- The constraints are Apple's specific answers — `#0071e3`, `#f5f5f7`, pill buttons — presented as a method. Take the register discipline and the rejection log; adopt the palette and you will build an Apple store with a hospital's logo.
- Scoped to marketing and consumer web. It says nothing useful about dense institutional UI — schedule tables, multi-field forms, call-out flows — which is most of what Shareef builds.
- One register per page is a clean rule that breaks on hybrid pages. A residency landing page that also has to take an application is both commerce and tool.
**Should we...**
- ✅ **Adopt it** — the method, not the values.
**Why:** The transfer is that the Unified Platform currently has one register for everything, which is why the marketing-shaped pages feel like product screens and the product screens feel like nothing in particular. Name three registers and write the prohibitions for each: the platform is a **tool** register (quiet, dense, one accent, no decorative motion); the Sub-I welcome material is an **identity/editorial** register (warm ground, one serif statement, one signature visual that belongs to this program and no other); residency social is a **commerce** register (loud, one asset per post, one focal point). Then steal `rejected.md` as a format — keep a running file of approaches that failed with the reason in the reviewer's own words. A list of what didn't work and why is the most persuasive design document there is, and it is the artifact that stops next year's team repeating this year's decisions.

---

### Inrond — Inter with a roundness axis
**Link:** https://github.com/Hairline-UI/inrond · live specimen: https://inrond.hairlineui.com · **v1.0 released 14 November 2026** · OFL-1.1 · 15 stars, 0 forks · by Hairline UI
**Type:** Tool / Technique
**What it is:** A variable font built on Inter 4.1 that adds a `ROND` 0–100 axis. At `ROND 0` it renders identically to Inter; turn the axis up and every stroke end and outer corner rounds. It keeps all of Inter: 2,937 glyphs, Cyrillic/Greek/Vietnamese, 39 OpenType features, the optical size axis and the drawn italic.
**What's good about it:** The metric guarantee. "Advance widths and kerning are identical to Inter at every roundness, so switching, theming or animating never reflows text." That is the only thing separating a usable type system from a font demo — you can animate roundness across a page and not one line break moves. Then the system move: the README pairs the axis with the UI corner radius, one token for both — `--round: 60; --radius: calc(var(--round) * 0.22px)`. Type and cards soften together, instead of one rounding while the other stays square.
**Pros:**
- Zero reflow at every `ROND` value — same advances, same kerning as Inter, so it is drop-in for an existing Inter codebase rather than a rebuild.
- The axis binds to the radius token: one parameter drives type and components. The most coherent "soft UI" system logic I have seen this year.
- Complete Inter coverage — real italic, `opsz`, Cyrillic, Greek, Vietnamese, 39 features. Not a Latin-only novelty.
- Frozen builds ship alongside the axis (`Inrond Round` at 100, `Inrond Soft` at 50) at roughly 1.5× Inter's file size, so you can take the look without paying for the axis.
- OFL-1.1, self-hostable, unicode-range subsets so a Latin page downloads only the Latin file.
**Cons:**
- Roundness is a very loud decision. Past `ROND 60` it reads "friendly consumer app" — the wrong register for a clinical platform's trust surface, and it will fight a flat, thin-stroke SVG icon set drawn with square terminals.
- 15 stars, a repo one day old, one maintainer, and no track record at extreme axis values in Safari and Firefox. You are the test case.
- It is a derivative of Inter 4.1, so it inherits Inter's release cadence. When Inter moves, Inrond chases, and your type is now on someone else's schedule.
**Should we...**
- ✅ **Adopt it** — as a single-surface pilot, not a migration.
**Why:** Shareef's platform is Inter, one accent, SVG icons — a disciplined, quiet system. Inrond matters because it lets that system gain a second dimension without gaining a second typeface, which is a move a design director makes and a template does not. Scope it to one surface: the Big Reef Chapter Player, the light, softer-context product where a warm geometry is an asset. Pilot at `ROND 40`, judge against the existing icons at 13–15px, and if the terminals and the icons start arguing, the answer is no — knowledge gained in an afternoon rather than a quarter.

---

### sui-motion-graphic-reel
**Link:** https://github.com/suiyang-meta/sui-motion-graphic-reel · created **12 November 2026**, pushed 13 November · CC-BY-4.0 · 4 stars · by Sui Yang (@asksui.ai)
**Type:** Workflow
**What it is:** A Claude Code skill for making motion-graphic reels by writing code that renders frame by frame — no After Effects. The order is enforced: find or build a design system, or get three design directions each with a sample frame and pick one → script and voiceover with per-character timing → storyboard shown for approval before anything is built → build shot by shot → pre-render review (paper pass, machine measurement of static frames, then a review agent applying your own critique profile) → export → the AI zooms in and re-checks → handoff that states plainly what it saw, what it changed, and what it left alone.
**What's good about it:** The critique profile. *"You pick a fault once — 'this is too empty', 'the type is clipped' — it writes it into your review profile, and before the next film exports it checks against that profile first."* A machine-readable record of your taste, applied before you have to say the same thing twice. That is the missing piece in every AI creative workflow: models do not accumulate your standards, they restart from zero each session. And the craft rules are real motion principles rather than style choices — one visual language per film, one technique per shot, four layers per shot, the camera must move on its own, one focal point at a time.
**Pros:**
- A hard storyboard checkpoint before any production. That is studio discipline encoded, and it is what prevents the twelve-render dump.
- The three-stage pre-render review is correctly ordered: paper judgment, machine measurement of frames, then a taste pass — three different classes of error caught in the sequence that catches them cheapest.
- The critique profile persists across projects, so review effort compounds instead of evaporating.
- Honest process evidence: the README shows a 15-second opening contact sheet at half-second intervals and states it took seven revisions in a single day. That is what craft documentation looks like when someone is not selling.
**Cons:**
- Four stars, one author, and the entire README is in Chinese — a real barrier for anyone on the team who would need to run this, and no English docs yet.
- Needs a paid Claude Code plan plus a code-rendering pipeline. This is not operable by a non-programmer, which matters for Shareef's team.
- The critique profile is only as good as your notes. Feed it "make it pop" and you have automated vagueness.
- No rendered film is linked, only a contact sheet. I can judge the process; I cannot judge whether the output is good.
**Should we...**
- 👀 **Watch it** — and copy the idea this week.
**Why:** Motion is the conspicuous gap across Shareef's surfaces: the platform is static, the Chapter Player is static, social is stills. The immediately portable idea is the critique ledger — a short written list of the faults that recur in our own work ("too empty," "type clipped," "two focal points," "shadow doing the work"), applied as a checklist before anything ships. That costs nothing to start today and works on still images as well as film. The skill itself waits for an English README and someone on the team who actually wants to write code.

---

### MiniMax-H3-Image — open-weight 16MP generation + editing
**Link:** https://github.com/MiniMax-AI/MiniMax-H3-Image · model: https://huggingface.co/MiniMaxAI/MiniMax-H3-Image · created **9 November 2026**, last push 11 November · 371 stars · 68.65 GB BF16 (DiT) · optional NVFP4 prompt expander (17.9 GB)
**Type:** Tool
**What it is:** An open-weight image model from the MiniMax H3 family handling text-to-image and multi-image editing in one checkpoint: ~16MP output at any aspect ratio natively in 6 sampling steps, up to 16 reference images, and a bundled `h3-image-prompt-writing` agent skill that turns a brief or a set of references into a full prompt and renders it through the API.
**What's good about it:** Reference capacity and inspectable intent. Sixteen reference images per request is not a mood board — it is enough to supply palette, type specimen, lighting reference and prior campaign frames in a single call, which is the mechanical basis of art direction. MiniMax claims the output goes "beyond the familiar 'AI look'," and the expanded prompt can be returned, so you can see what the model decided you meant.
**Pros:**
- Up to 16 reference images, each up to 64 MiB — genuine art-direction surface area rather than one inspiration image.
- Native ~16MP at 1:3 to 3:1, custom dimensions 655,360–20,000,000 px, no upscaler. Enough for print and OOH crops without a second generative pass destroying the composition.
- Ships a prompt-writing skill that goes brief → prompt → render inside Claude Code, Codex or Cursor. A pipeline, installable with one `npx skills add`.
- Prompt expansion is inspectable and switchable — you can separate "what I asked for" from "what it rewrote."
**Cons:**
- **No user-specified seeds.** The disqualifying gap: reproducibility is the entire basis of a consistent campaign, and this is a slot machine at exactly the point where you need a lock.
- Also missing: mask-based inpainting and transparent backgrounds. Table stakes for production retouching — you cannot isolate a subject or hand back a clean cutout.
- 68.65 GB BF16 means two GPUs or aggressive quantization. The realistic path is the Hailuo/API, so "open weights" does not translate into control you actually hold.
- The showcase is game worlds, Caravaggio pastiches and Dunhuang murals — technically impressive, strategically irrelevant. The realism it optimizes for is not clinical photography, and a urology program is not buying concept art.
**Should we...**
- 👀 **Watch it** — revisit when seeds land.
**Why:** The number to remember is sixteen. Reference-driven generation is the only honest path from prompt luck to art direction, and every serious model is moving the same way. But without seeds it cannot hold a look across a campaign, and without masks it cannot be used for production retouching — so today it demonstrates where the ceiling is rather than giving us something to put a brand on. The quietly useful part is the bundled prompt skill: it formalizes "brief + references → prompt → render," which is the workflow worth building regardless of which model sits underneath.

---

### Google Pixel × Highsnobiety — PIFT first cohort
**Link:** https://wwd.com/sourcing-journal/industry-news/google-pixel-highsnobiety-pift-ai-fashion-designers-1239412108/ · published **12 November 2026** · WWD (Sourcing Journal), by Alexandra Harrell · Berlin showcase, 12 November
**Type:** Idea
**What it is:** The Pixel Institute of Fashion and Technology gave independent designers Pixel phones, Google's AI tools and named mentorship (Girls in Blue Studio, photographer Campbell Addy, photographer-director Hugo Comte), then showed the resulting work in Berlin. Projects ran from OBS's first cotton-canvas bag to an Ottolinger mesh print to a Krobos dress derived from the shape of a single flower.
**What's good about it:** The quotes document the working mode that actually avoids slop. Ottolinger: *"We thought it would be faster or more random, but it turned into a real back-and-forth, almost like working with another designer in the studio."* Krob: *"I still want to design myself, but using AI to visualize my ideas for my clients is super helpful."* Both describe slow iteration and a communication use — not generation replacing authorship.
**Pros:**
- Names the correct division of labor: AI at the visualization and client-communication stage, human at the authorship stage. That is the most defensible position for a design team inside an institution.
- Several designers used it as a research engine rather than a renderer — Chet Lo ran Gemini Deep Research over shadows cast by blinds and 1980s anime colour. Reference-gathering is a low-risk, genuinely useful application.
- A taste filter with names attached rather than an open prompt contest. Human curation is what stops a program like this becoming a slop exhibition.
**Cons:**
- It is Google marketing. Every quote is a partner-selected testimonial; no failures, no cost figures, no rejected work, no mention of what the tools were bad at.
- Phone-based Gemini, fashion-specific, no published method — none of it is replicable as a workflow. You can quote it; you cannot adopt it.
- The outputs read as craft partly because the garments are physical objects that had to be made. Strip the material reality and several would be ordinary AI renders.
**Should we...**
- 👀 **Watch it** — use it as an argument, not a technique.
**Why:** Shareef will eventually have to defend using AI on program marketing to people who suspect it cheapens the work. This is the most usable evidence available: six named designers describing a slow, human-controlled back-and-forth in which the machine visualizes and the designer decides. The transferable line is Krob's — showing a client what an unfinished idea looks like is not a craft compromise, it is what a good art director already does with comps. What it is not is a license to generate final creative and call it art direction, and the article's silence on failure is the tell.

---

### gpucanvas — WebGPU infinite canvas with an agent-readable view
**Link:** https://github.com/berkantay/gpucanvas · live demo: https://berkantay.github.io/gpucanvas/ · technical write-up: https://berkant.me/blog/gpucanvas-webgpu-infinite-canvas · created **12 November 2026**, pushed 15 November · MIT · 461 stars, 28 forks
**Type:** Tool
**What it is:** An open-source infinite canvas that draws thousands of live DOM/React nodes with WebGPU instead of the DOM. Pan and zoom never touch the DOM, but clicks, typing and state still reach the real elements. Ships an editor with selection and snapping guides, WGSL shader effects on live components, pixel diffs between snapshots with a filmstrip of a node's history, and an "agent view" that exposes the canvas as a short JSON tree with ids plus an image of any region.
**What's good about it:** Two things. First, the benchmark is falsifiable: the same 5,000 live React screens, the same camera path, both frame rates measured live in one session, with a demo you can run yourself. Second, the agent view. Handing an AI agent a *structure* — a JSON tree with ids plus a region image — instead of a screenshot it must describe in prose is the first credible answer I have seen to "how does an agent actually see a design."
**Pros:**
- An honest, reproducible performance claim rather than a marketing multiple — same session, both sides measured, demo linked.
- Live components, not screenshots: state, clicks and typing still work, so the canvas is a real surface rather than a picture of one.
- The agent view (JSON tree with ids, region images, agent cursors and marks that follow the camera) is the correct primitive for AI-assisted layout review.
- Snapshot pixel diffs plus a history filmstrip is design version-control thinking, not just a viewer.
**Cons:**
- Chrome 157+ and WebGPU only, with no fallback path described. That is a long way from a hospital browser fleet.
- The demo's scale — 5,000 screens, 30 agent cursors — is a spectacle, not a use case. Nothing in Shareef's surfaces needs an infinite canvas.
- Shader effects (glass lens, VHS, glitch, shockwaves) are precisely what reads as "AI demo" when applied to brand work. The tool ships the slop and relies on you not to use it.
- Three days of commits and 28 forks: no production track record.
**Should we...**
- 👀 **Watch it** — for the agent view, not the canvas.
**Why:** This is design engineering, and it does not solve a problem Shareef has this quarter. The reason to keep it is conceptual: when an agent reviews or builds a layout, it should read structure (a tree with ids, a region reference) rather than a screenshot it has to narrate. That single pattern is directly applicable to the Figma-to-platform review problem, and it is the useful counterweight to this week's other finding — that the tools which claim to do visual QA against a design system are, so far, mostly fake.

---

### resocket "pixeljury" + claude-resocket-plugin
**Link:** https://github.com/DjinnTheFairy/resocket-pixeljury · https://github.com/Wolflakechip39019/claude-resocket-plugin · both created **14 November 2026** · 50 stars each, 0 forks each
**Type:** Tool (claimed)
**What it is:** Two repositories advertised respectively as "a visual QA CLI for AI-built frontends that renders pages, finds design and accessibility issues" and "a Uiprobe plugin for Claude Code: a check Claude can run against your Figma design." Both surfaced high in a GitHub search for `ai design` created this week.
**What's good about it:** The described capability. Diffing rendered UI against a design-system source of truth is the most useful missing tool in AI-built frontend work, and it is exactly what would most directly serve the Urology Unified Platform. That is why the listings are convincing enough to open.
**Pros (of the underlying idea, not these repos):**
- Automated visual regression against a Figma or token source of truth would catch design-system drift better than human review does.
- Framing QA as a gate the agent runs on its own output is the right shape for the problem, and worth building for real.
**Cons:**
- Both repositories contain exactly two files: `CONTRIBUTING.md` and `initial.html`. No README, no source, no release, no issues. Nothing to install.
- 50 stars each, 0 forks, both created the same day, with 17 keyword-stuffed topics between them. Search-optimized shells, not software.
- The descriptions promise rendering, screenshots, accessibility auditing and Figma comparison — an enormous surface, delivered as a single HTML file. The claims are simply not in the repository.
**Should we...**
- ❌ **Skip it** — entirely.
**Why:** This is the new tool-sourcing hazard, worth naming plainly: a star count now costs nothing to inflate, and search ranking rewards topic stuffing. Two repos, zero code, fifty stars apiece, one day old. The rule that comes out of this run is simple and should hold: never shortlist a repository without opening its file list and reading its last commit date. If a tool claims to compare built UI against a Figma design and the repository contains one HTML file, the answer is no — regardless of how precisely it describes a problem we actually have.

---

## Slop Radar
- **Phantom repos with real star counts.** Two "AI design QA" repos created 14 November, 50 stars each, two files each, zero code. Stars are no longer a proxy for anything; open the file tree.
- **"Desktop setup" repos.** `brave-plum-co/leonardo-ai-desktop` (359★, created 14 November) — a repository promising a "Leonardo AI 2026 desktop setup" is a distribution vector, not a design tool. Same family as the phantom repos, one step closer to a payload.
- **Roundness creep.** Two rounded-grotesque releases in five days — Goeist (a rounded Geist, shadcn-labs, 11 November, itself flagged experimental) and Inrond (14 November). Rounding is becoming the reflex "make it friendlier" lever, which means round-by-default is heading toward being as much of a tell as the purple gradient was.
- **"Anti-slop" is becoming its own template.** The first wave of anti-slop prompts, skills and presets — suzhe-ui, wensity/skills, tobiashaas/website-builder-toolkit, Antislop — is now numerous enough to converge. The moment "restraint" is installable, restraint stops being a signal: expect a wave of sites with three backgrounds, one accent and a serif statement, all obeying the same rulebook. Take the reasoning; refuse the preset.

## Overall Assessment
The strongest work this week was not generative — it was **prohibition infrastructure**. suzhe-ui ships sixteen documented rejections with the client's verdict attached; Inrond ships a metric guarantee that no line will ever reflow; sui-motion ships a critique ledger that remembers your standards between sessions; MiniMax pushes reference images to sixteen while still, revealingly, refusing to hand anyone a seed. Across four unrelated projects the shape is identical: premium AI design is being built out of constraints and post-mortems, not out of better prompts. That is the direction that matters for us, because constraints are what a design director can author and a prompt is what anyone can type. The single highest-leverage move for Shareef this week costs no software: write one page naming the three registers across our surfaces — tool, identity/editorial, commerce — and under each, the five things that register never does. That page will change more output than any tool in this brief. If there is time for one experiment after it, run Inrond at `ROND 40` against the Chapter Player and let the icons vote.
