# AI Design Intel — October 17, 2026
Sources scanned: X (available via web_search — Pablo Stanley's Design Team agent post surfaced); Reddit (JSON API blocked again: all six subs return the identical 190,240-byte block page, md5 852a17d4f70e, same as yesterday — web_search fallback used for r/graphic_design, which returned only opinion threads, no technique or release inside the window); HN (hnrss + Algolia search_by_date + last30days-pro aggregator all available); GitHub (available); Google News (available). Candidates considered: 19. Passed the bar: 6.

Dedupe note: Solid Glass, Taste Library, Zack Design Skills, OpenPencil, desigma, Figxel MCP, CLI Style and the Atlassian DESIGN.md benchmark were judged on Oct 16 and are NOT re-covered — no new versions. The Google DESIGN.md / portable-context axis is deliberately not re-run again; Figma Specs below is a genuinely different artifact (a live canvas container, open beta, not a file format).

Sources note: last30days-pro returned a 2024 Figma/Apple Weather story as its top HN hit — stale, discarded, not used. Reddit's block is now three days running; treat "Reddit via web_search" as the normal mode, not an anomaly.

## Executive Summary

| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Figma Specs | Tool | ✅ Adopt it | A Markdown container on the canvas that frames, code and diagrams travel inside — the first place design intent and design evidence live in the same file that agents read |
| Awesome UX Skills — `craft` + `design-analysis` | Tool | ✅ Adopt it | 12 pasteable visual-craft rules (starting with "no gradients, no glow, no `transition: all`") plus a measured-extraction skill that returns real hexes and OKLCH instead of adjectives |
| SlopCop (Design Slop Cop) | Idea | ✅ Adopt it | 14 deterministic CSS/DOM checks that turn "this looks AI-made" into a score you can defend in a review — and 54% of 1,590 Show HN sites trip 2+ of them |
| Pablo Stanley's Design Team | Idea | 👀 Watch it | 16 argumentative design-agent roles with a creative director that sets hard constraints — the right thesis (friction is the process), still too agreeable by its author's own admission |
| CSS Composite Font Workshop | Tool | 👀 Watch it | Real InDesign-style composite typesetting for CJK + Latin, exportable as CSS or baked font files — genuine typographic craft, but not on any current surface |
| Choreon | Tool | 👀 Watch it | A motion-design pipeline with a storyboard, a critic that scores against the brand's own doctrine, and UI kits harvested as layered SVG — ambitious, two days of code behind it |

---

### Figma Specs

**Link:** https://www.figma.com/blog/introducing-figma-specs/
**Type:** Tool
**What it is:** Announced at Config India on October 15, Specs is a multiplayer Markdown container that lives on the Figma canvas — press `D` and you get a document sitting next to the frames it describes. You can drag in any `.md` file, embed a frame, a FigJam diagram or a code layer inline (so text and design sit side by side rather than a screenshot or a stale link), duplicate a spec per person for parallel riffs, and hand the spec's link to a coding agent so the Markdown, the frame references, the diagrams and Code Connect snippets all travel together through Figma's MCP server. The agent can read and reply to comments inside a spec the way a human collaborator would. Open beta on paid plans as of October 15; code layers moved to public beta the same day and code-layer editing is free on paid plans through November 4.

**What's good about it:** The craft insight inside Specs is narrower and better than the marketing around it: it concedes that Markdown is now the format everyone writes context in and then names exactly why raw Markdown fails — it is "single player," its links to the work are brittle, and it is divorced from the project that produced it. Specs' answer is to make the context *addressable on the canvas*, so a design decision and the artifact it governs are one object. That is the same problem the last two briefs circled from the file-format side (DESIGN.md, `.op` files), solved from the collaboration side, and the inline-embed mechanic is the part no flat file can copy. The research-preview evidence in Figma's own post is the right kind: an engineer wrote a spec mapping edge-case principles, embedded FigJam diagrams, collected comments, fed the spec to his agent via MCP, then kept updating the spec on the canvas as the code progressed. That loop — write, argue, implement, revise the source — is how a real design system stays honest, and it is exactly the loop that currently does not exist on the Unified Platform.

**Pros:**
- Design intent and design evidence share one addressable object (frames, FigJam, code layers embedded inline) — no screenshots, no dead links, no drift between the spec and the thing it describes
- Multiplayer Markdown with agent comment threads means review happens in the document, not in a chat log; the agent can be asked to answer every open comment with a proposed fix
- Specs travel to coding agents intact through MCP (Markdown + frame refs + diagrams + Code Connect snippets in one link) — that is the missing handoff we have been faking with prose
- Real named production users in the launch post (Figma engineering, Intuit's design system team documenting icon metadata) — not a demo reel

**Cons:**
- Open beta on paid plans only, and agent work inside Specs consumes AI credits — the free window that exists for code layers (to Nov 4) does not extend to Specs
- It is a container, not an enforcement mechanism: nothing in Specs stops an agent from ignoring the spec, so discipline still has to come from the prompt and the review
- Canvas-embedded Markdown invites sprawl — three duplicated specs per direction is a feature until you have twelve and no idea which one shipped
- Ties your written design intent to a commercial tool's file model, which is the same lock-in critique aimed at Figma for a decade, now applied to your own reasoning

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This is the first tool from a major vendor that solves the actual problem on Shareef's surfaces, which is not generation but *retention of intent*. The Unified Platform has a premium dark theme, a single accent, Inter and SVG icons — but the reasoning behind each of those decisions lives in prose documents and in my memory, and every regeneration is a chance to lose it. Specs gives that reasoning a home on the artifact, and because a spec can embed the real frame and the real code layer, the document stops being a description of the design and becomes part of it. Concretely: one Specs file per surface (Unified Platform, Chapter Player, residency marketing creative, Sub-I welcome materials), each embedding the frames it governs and the anti-patterns list, handed to agents by link rather than pasted into a prompt — which also answers the Atlassian finding from yesterday, since a linked spec is on-demand context, not an all-at-once dump. The cons are real but bounded: the paid-plan requirement is a problem we already have solved (Figma is in use), the sprawl risk is a naming convention, and the enforcement gap is what the craft rules below are for. Fall back to a plain `.md` in the repo the day Figma's file model stops being worth paying for; the *structure* — intent, evidence, anti-patterns, one container — is the thing worth adopting, and it survives the tool.

---

### Awesome UX Skills — `craft` and `design-analysis`

**Link:** https://github.com/tommyjepsen/awesome-ux-skills
**Type:** Tool
**What it is:** A collection of ~24 UX and AI-product design skills by Tommy Jepsen (265 stars, created May 2026, install via `./install.sh` into `~/.claude/skills/`) covering research methods, heuristics reviews, Dieter Rams' principles, accessibility, AI trust and governance patterns. Two of the skills are the reason it clears the bar. **`craft`** is 12 numbered visual-craft rules applied at the CSS-property level, with an explicit bans list and a critique output format that ends in three priority fixes. **`design-analysis`** is a design-forensics skill that screenshots a URL with Playwright at 1440×900 and 390×844, samples real pixels for exact hexes, reads computed styles, and returns typography, palette with area shares in hex and OKLCH, composition, spacing, shape and motion — then emits the whole thing as shadcn/ui tokens. Its instructions are blunt: "Never guess a hex code, a font size, or a spacing value that you could have measured. Two scripts below do the measuring. Run them."

**What's good about it:** `craft` is the most immediately usable anti-slop document I have read this week, because every rule ends in a value you can paste rather than an aspiration you can nod at. R1 bans gradients with the correct diagnosis — "gradients are the default move when a color decision hasn't been made" — and names the fix: a better neutral, a hairline border, or texture, with one deliberate exception for gradient-as-brand. R2 bans glow because "emphasis borrowed instead of earned." R3 kills `transition: all` and demands named properties. R7 bans pure black on pure white and requires a single neutral ramp that borders also draw from. R9 puts hierarchy in weight and colour before size, and specifies `tabular-nums` for columns. R10 forces you to *pick one elevation language* rather than stacking border + shadow + background shift on the same card. R11 requires every state to be designed, including focus-visible. That is a design director's checklist written as lint rules, and it maps almost one-to-one onto the decisions that make the Unified Platform look premium rather than generated. `design-analysis` is the necessary other half: you cannot enforce craft you have not measured, and this skill refuses to let an agent confabulate a hex value.

**Pros:**
- Every craft rule ships with a concrete fix (real hexes, real ms, real properties) and an output format that limits the agent to three priority fixes instead of a lecture
- The bans list is precisely our Slop Radar, encoded executably: gradients, glow, `transition: all`, pure black/white, visual monotony, placeholder copy
- `design-analysis` measures rather than guesses — Playwright capture, real pixel sampling, computed styles, then tokens; and it explicitly hands off to critique skills only *after* measurement
- Plain `.md` skill files, no lock-in, installs into Claude Code/Codex and is readable as a document even with no agent in the loop

**Cons:**
- Repo has not been pushed since August 10, 2026 and nobody has stress-tested the rules against real client work — the 265 stars are mostly a Show HN bump
- `craft` is opinionated in a direction that could fight a deliberate brand (its "no gradients" and "no glow" bans are correct for us, but would wrongly flag careers where a gradient *is* the identity)
- `design-analysis` depends on Playwright and Node in the agent environment, which we do not currently guarantee — the measurement half may be the harder half to actually run
- The AI-product skills (`ai-tuners`, `ai-trust-builders`) are contemporary-practice summaries rather than original craft; read them as a vocabulary, not a standard

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** `craft` is the enforcement layer that yesterday's brief said we were missing. Adopting Figma Specs gives design intent a home; `craft` gives it teeth, because it converts "make it look premium" into a list an agent can be checked against and a human can review in thirty seconds. The direct application is the Unified Platform and the Chapter Player: R7's neutral ramp and R10's single elevation language describe exactly the discipline that keeps a dark premium UI from drifting into the "perma dark with medium-grey body text and saturated glow" pattern that SlopCop now measures at scale, and R11's state requirement is the difference between a demo screen and a shipped product. For marketing creative and Sub-I materials, R5 (no placeholder copy — write the real microcopy as part of the design work) and R4 (kill visual monotony) are the two rules that separate an art-directed piece from a template. The honest caveat is that this is a rulebook, not a taste transplant: 12 rules will make work *correct*, and only a direction will make it *ours* — so use it after the direction is set, and let it flag drift, never choose the look. I would install it this week and run it in critique mode against one existing Unified Platform page as a baseline, before writing another line of new UI.

---

### SlopCop (Design Slop Cop)

**Link:** https://slopcop.adriankrebs.ch
**Type:** Idea
**What it is:** A free, MIT-licensed tool that scores any website for AI design patterns. It loads the page in a real headless browser (Playwright), walks the live DOM, reads computed styles, and checks 14 deterministic CSS/DOM rules — no LLM in the judging path, deliberately, "because an AI judge would smuggle in the very bias the tool exists to measure." Each hit is named with evidence and a screenshot; the score is patterns-flagged over 14, tiered Low/Medium/High. The author, Adrian Krebs, scored 1,590 recent Show HN submissions: **22% High (4+ patterns), 32% Medium (2–3), 46% Low (0–1)** — roughly a third qualify as medium-to-heavy design slop. The catalogue is published with a real example crop per pattern, and the rules are one file each in the repo, so the whole thing is auditable and extensible.

**What's good about it:** The value here is not the verdict, it is the *vocabulary* — this is the first credible attempt to turn "that looks AI-made" into something you can put a number and a rule ID against in a design review. The pattern list is a genuinely sharp read on the house style of the last two years: templated display fonts used as the page default (Space Grotesk, Instrument Serif, Geist, Syne, Fraunces); one hero word set apart by a second font or an italic; indigo/violet on CTAs; gradient backgrounds and gradient-clipped hero text; the colored accent stripe on a card's top or left edge; backdrop-blur glass panels; saturated `box-shadow` glow; emoji in the nav; a centered hero set in Inter or a generic sans; perma-dark with muted grey body text; the 1·2·3 step row; the stat banner; the pill badge above the H1; the FAQ accordion. A designer friend's line in the post is the best sentence in the piece: "colored left borders are almost as reliable a sign of AI-generated design as em-dashes for text." Because every rule is a deterministic check, the result is repeatable and explainable — the opposite of the black-box detector genre.

**Pros:**
- Deterministic DOM/CSS checks with per-pattern evidence and screenshots — repeatable and arguable in a review, no model in the judging loop
- A published, browsable corpus: 1,590 Show HN sites scored, plus a per-pattern reference page with a real example crop for each of the 14 tells
- Rules are individually extensible files, so house-specific patterns (our own drift) can be added without forking the concept
- The honest framing is the point — "is design slop bad? Not really, just uninspired" — it measures unoriginality, not quality, and says so

**Cons:**
- Scoring is crude arithmetic (flagged ÷ 14), so a page tripping one trend that is genuinely the brand scores the same as a page that defaulted into it
- 5–10% false positives by the author's own manual QA, and "Perma dark" + "Centered + Inter" will fire on deliberately art-directed dark work like the Unified Platform
- Checks are surface-level by design: nothing about type scale discipline, grid, hierarchy, spacing rhythm, or whether the copy is real — the things that actually separate premium from average
- Small project (18 stars, one maintainer, no releases); the 190KB block page behaviour on Reddit today is a reminder that single-maintainer tooling is a dependency with a shelf life

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** Adopt it as a **red-team checklist before publishing**, not as a grade — and adopt it precisely because it will sometimes be wrong about us. Score the Unified Platform and the Chapter Player today and expect the Unified Platform to trip "Perma dark" and the Chapter Player to trip "Centered + Inter": that is not a failure, it is the tool proving it measures *trends* rather than taste, and having that distinction on paper is what lets us defend a deliberate dark UI against a stakeholder who has read a slop thread. The real application is the outward-facing work where the accusation is expensive: residency marketing creative, Sub-I welcome materials, and any client-style site. If a Sub-I landing page trips the accent-stripe + stat-banner + headline-badge cluster, that is a concrete, fixable brief for the next art-directed pass — and it is the same tell-set as our Slop Radar, now measurable. Run it on anything client-facing before it ships, keep the score in the file next to the design, and treat the 14 rules as the floor: clearing them means you are not obviously generated, not that you are good.

---

### Pablo Stanley's Design Team

**Link:** https://x.com/pablostanley/status/2041228653569396796
**Type:** Idea
**What it is:** An open-source agent team system from Pablo Stanley (co-founder of Blush, author of the Open Peeps and Humaaans illustration libraries): 16 specialised design roles installed with `npx skills add pablostanley/designteam-app`, each with personality traits on axes (Bold/Subtle, Playful/Serious, Experimental/Conventional) under a fixed 25-point budget so no agent can max everything — a researcher (Scout), copywriter (Aria), graphic designer (Pixel), UX designer (Flow), editorial designer (Reed), social designer (Buzz), creative director (Nova), plus eight more. Traits modulate the system prompt, so a bold-experimental designer makes different layout and colour decisions than a subtle-conventional one. In his own words from the post: agents split into phases, builders run in parallel on isolated artboards, and "they're not describing designs. They're calling 42 actual design tools, creating artboards, adding sections, styling nodes." In his worked example, Nova, the creative director, set hard constraints — "No gradients. No icon grids. No stock photography of handshakes or skylines. The restraint IS the design."

**What's good about it:** The thesis is the best-articulated one in the whole AI-design conversation this week, and it comes from a designer with real craft provenance rather than a tools influencer. "When building multi-agent systems we all seem to be optimizing for coordination... Assembly lines are great at producing the same thing over and over. But creative work, often, comes from chaos." His diagnosis of why agent-assisted design converges is exact: ask an AI to critique and you get a compliment sandwich; "that's not how a good art director talks. A good art director says 'I've seen this a hundred times, too predictable... what else you got.'" The 25-point personality budget is a genuinely clever constraint mechanism — it forces the system to make trade-offs instead of averaging, and it produces the one thing an averaged model never can: a *point of view that can be argued with*. And the creative director setting explicit bans before any builder runs is exactly the right order of operations — direction as prohibition first, palette second.

**Pros:**
- 16 differentiated roles with a hard personality budget — a structural answer to convergence, not a prompt trick, and it produces constraints you can quote back to an agent
- The creative-director-as-brief pattern (explicit bans: no gradients, no icon grids, no stock handshakes) is directly liftable even if you never install the system
- One-command install, works with Claude Code or Codex, from a designer with a real illustration portfolio behind him
- Stanley publishes his own doubts in the same post, which is rare and useful

**Cons:**
- By his own admission the agents are still too cooperative: "Nova sets the rules and everyone follows them. Nobody pushes back and says 'actually, this dark palette is wrong for this brand'" — the stated thesis is not yet delivered by the implementation
- ~80 API calls per site built — expensive enough that it is a curiosity, not a workflow
- Benchmarked inside Efecto, his own commercial design tool, so the result set is not independent
- "16 roles" is the same fantasy as "8 design skills": role-play personas are cheap to create, and nothing here demonstrates that personality sliders beat one well-written brief plus a ban list

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** The idea is worth adopting today and the software is not. What Shareef is missing on the residency marketing creative and Sub-I materials is not more generation — it is *a direction that says no to things*, and Stanley's Nova pattern is the cleanest written expression of that in the wild: bans before builders, restraint as the design. I would lift the mechanic now — one creative-director pass that writes explicit prohibitions for a specific brief, reviewed by a human, before any layout tool is opened — because that single change is the difference between art direction and prompting. What keeps the system itself at Watch is the author's own concession: the agents do not actually disagree, so the friction that is supposed to be the feature is not there yet. Revisit when a before/after shows a genuine creative-director veto changing an outcome, not just setting a constraint everyone obeys. Also note the 25-point budget as a reusable idea for our own direction documents: you cannot be bold *and* subtle *and* experimental — pick a balance and write it down.

---

### CSS Composite Font Workshop

**Link:** https://github.com/charlie5188/css-composite-font
**Type:** Tool
**What it is:** An MIT-licensed browser tool (created October 13, 47 stars, no build step) that builds composite fonts the way InDesign does — a separate font, size and baseline for CJK ideographs, kana, full-width punctuation, Western text, digits, symbols and Zhuyin, tunable per weight, proofed live. A one-click Auto-adjust measures the fonts and sets the Western size and the baseline so capitals sit centred on the CJK character face. Three outputs: paste-ready CSS of a few KB using multiple `@font-face` rules sharing one family name with `unicode-range` and `size-adjust`; TTF/OTF/WOFF2 baked in the browser for Figma, Keynote, Word; and, experimentally, Swift/Kotlin/Flutter code for native apps. It also checks regional glyph forms for Simplified, Taiwan, Hong Kong and Japanese and exports `text-autospace` and `line-break`. Interface in English, 简体中文, 繁體中文 and 日本語.

**What's good about it:** This is craft of a kind the AI-design conversation almost never touches, and it is the kind that actually separates a typographer from someone who picked Inter. The README states the problem with unusual precision: a plain `font-family` fallback "can't make the Western font a little larger to match the CJK character face, decide whether quotes and dashes come from the CJK or the Western font, or keep the balance right as text gets bolder." That is a real production problem — Latin-cap-height versus CJK-em-size mismatch is why bilingual work almost always looks cheap — and the solution is standards-based CSS (`unicode-range` + `size-adjust` on shared family names) rather than a proprietary pipeline. Weight-awareness is the other serious detail: settings made at 400 carry to every weight, and variable fonts take any weight, which is exactly where naive composite setups fall apart when a heading goes bold. Publishing the mechanism in the README, including the browser-support floor and the "a baseline shift needs a small script" caveat, is the mark of someone who has shipped this rather than demoed it.

**Pros:**
- Solves a specific, unglamorous, genuinely hard typographic problem with standard CSS and a documented mechanism, not a black box
- Weight-aware across the whole scale, with variable-font support — the part that composite font implementations usually get wrong
- Three real output formats including baked font files for design apps that have no composite support, plus experimental native code
- Regionally correct checks (Simplified / Taiwan / Hong Kong / Japanese glyph forms) — a design-history-aware detail most tools ignore entirely

**Cons:**
- Zero relevance to Shareef's current surfaces: the Unified Platform, Chapter Player, residency marketing, Sub-I materials and client sites are all Latin-script English
- The bilingual work it serves is genuinely hard to art-direct — an agent can apply it, but judging whether the result is typographically correct requires someone who reads the script
- If Montefiore ever produced Arabic or other RTL patient-facing material, this tool does nothing for it; the RTL problem set is different
- Small, one-author project with no releases; a standards-based tool is more durable than most but the maintenance question is unanswered

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** This is the best example this week of the standard I want us judged against — it does not generate anything, it makes an existing craft decision correct, and it explains the mechanism so a designer can keep it. For Montefiore specifically the practical case is thin today: the department's English-language surfaces get nothing from it, and I will not pretend otherwise. What earns it a Watch rather than a Skip is the direction of travel. A Bronx academic urology department serving a large multilingual patient population will eventually need patient-facing material in Spanish, Bengali or Arabic, and when that work starts, the failure mode will be exactly the one this tool fixes — bilingual layouts that read as cheap because the Latin type was never optically sized to the second script. Keep it bookmarked as the reference for how to write about typographic craft in our own documentation: name the problem, give the mechanism, publish the caveats, ship the CSS. The RTL case (Arabic, Urdu) needs a different tool and a different brief; do not assume this one covers it.

---

### Choreon

**Link:** https://github.com/vialcollet/choreon
**Type:** Tool
**What it is:** An MIT-licensed, local-first AI motion design studio from the team behind Omeon — "you direct, Choreon animates." The pipeline is: a framing interview where a director agent challenges the brief on 13 axes (goal, audience, locked message, hook, arc, rhythm, end frame, format) and nothing starts until each is decided; a storyboard where every shot has intent, on-screen text and a timed beat map plus a reference frame; shots written as `scene.html` files animated by a small deterministic runtime and rendered frame-by-frame through headless Chromium and ffmpeg with real motion blur; a **critic agent** that scores each render on six axes against the project's own doctrine and sends it back to the animator until it clears the bar; voice-over recorded in one take with Whisper word-timing so shots cut to the words; frame-accurate notes (pause, box the problem, dictate, and the note becomes the shot's new plan); sound design with a "one sound per gesture" doctrine; and a UI-kit harvester that takes any URL and rebuilds nav, inputs, buttons and cards as **layered SVG** in two variants (faithful and simplified) ready to animate. Each project carries its own `DESIGN.md`, `motion.md`, colour, fonts and `brand/house-rules.md`.

**What's good about it:** Three things here are senior-level, not demo-level. First, the critic loop is scored **against the brand's own doctrine** rather than a universal notion of good — "the studio rules are pure craft (timing, legibility, continuity, product truth) and say nothing about taste. Each project carries its identity and its taste." That is the correct separation, and almost nobody gets it right: craft rules are transferable, taste is per-project, and a critic that judges against the wrong one destroys the work. Second, "lessons": recurring mistakes become short rules that a human validates and that are then injected into every agent and checked by the critic — a studio that accumulates judgement instead of discarding it. Third, `scene.html` shots with a deterministic runtime rather than a video model means the motion is *reproducible* and *diffable*, and the UI-kit harvester producing layered SVG (not a screenshot) is the honest answer to "animate our real interface." The disclosed cost — an 8-second teaser for about $16 at API prices — is the kind of number that makes the rest of the claims legible.

**Pros:**
- Critic scores against per-project brand doctrine, with craft separated from taste — the most sophisticated quality loop I have seen in an agentic creative tool
- Deterministic coded shots with real motion blur, so output is reproducible and revisable rather than re-rolled
- UI-kit harvesting into layered SVG means real interface elements become animatable assets instead of redrawn approximations
- The framing interview (13 axes with defaults and options) enforces brief discipline before any generation, which is where most slop actually originates

**Cons:**
- Created October 12 — five days old, no releases, and the entire pipeline rests on a single SvelteKit/Bun/Claude Agent SDK stack that one team maintains
- Runs on your Claude subscription or API key with no stated cost ceiling; the author's own $16-for-8-seconds figure makes a 60-second piece a real line item
- Requires a heavy local toolchain (Bun, SQLite, Playwright, ffmpeg, optional Resolve Lua bridge) — plausible for one motivated person, not for a department
- The critic is an agent scoring agents, and Stanley's point applies: an LLM critic tends to grade generously unless the doctrine is unusually strict — the demo films are self-selected

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Motion is the layer where Shareef's surfaces are weakest and where AI tooling is most uniformly bad, and Choreon is the first pipeline I have seen that treats motion as *direction* rather than generation. The 13-axis framing interview is worth stealing outright for residency marketing video: before anything animates, someone has to decide the hook, the arc, the locked message and the end frame — and if you cannot answer those, the video was never going to work. The UI-kit harvester matters more for us than the demo films do, because the plausible first use is animating real Unified Platform components for a Sub-I or residency piece, and layered SVG is the only version of that which respects the actual interface. What holds it at Watch is entirely operational: five days old, a multi-service local stack, uncapped token spend, and a self-selected reel. The test before any adoption is narrow and cheap — take one existing Montefiore asset, write the brief and the prohibition list, and see whether the critic rejects its own first render. If it does, the loop is real. If the first render scores fine, it is a pretty pipeline with a rubber stamp.

---

## Slop Radar

- **The slop scoreboard is now public and it grades you whether you asked or not.** With 54% of 1,590 Show HN sites tripping 2+ deterministic tells, "it looks AI-made" is no longer a matter of taste — accent stripes, headline badges, stat banners and violet CTAs are becoming a documented fingerprint. Assume someone will run the check on our client-facing work; design as if the score is part of the deliverable.
- **"16 roles," "8 skills," "12 rules" — the role-count arms race.** Bigger org charts of agents are being sold as depth. A personality slider is not a portfolio, and role-play personas are the cheapest thing in the stack to manufacture. Judge the before/after, never the headcount.
- **Compliment-sandwich critics.** An agent that reviews its own or a sibling agent's output grades generously by default, which turns the "critique loop" into a rubber stamp. Any review step must be scored against an explicit, written doctrine with a pass bar — and a human must have written the doctrine.
- **Per-weight typographic neglect.** The most common silent cheapness in generated work is not the font choice, it is the absence of optical adjustment — Latin sized to a second script, display line-heights left at body values, `transition: all` standing in for designed motion. Craft is in the details that do not appear in a screenshot at 100%.

## Overall Assessment

The axis has shifted again, and this time toward the place the work actually lives. Two weeks ago the question was whether an agent could design; last week it was what artifact the design lives in; today the industry is answering with *containers for intent* — Figma Specs embeds the reasoning next to the frame and ships it by link, Choreon gives every motion project its own `DESIGN.md` and a critic that scores against it, Stanley's creative director writes bans before anyone draws. At the same time the audit side crystallised: `craft` turns 12 anti-slop rules into pasteable fixes with a 3-fix output cap, and SlopCop puts a defensible number on the same tells at corpus scale. Those two halves fit together — a written direction that agents obey, and a deterministic check that catches drift after the fact. For Shareef the single highest-leverage move this week is to pick **one** surface — the residency marketing creative, not the Unified Platform — and run the full loop once by hand: write a one-page direction with explicit prohibitions (Nova-style, Grademark-style ban list), put it in a Specs or a `.md` container that links the real artifacts, generate against it, then score the result with `craft` in critique mode and SlopCop before anyone outside sees it. One complete pass produces a template for every future piece, and it is the first time in this pipeline that "premium" will be something we can measure rather than argue about.
