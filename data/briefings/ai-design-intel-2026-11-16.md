# AI Design Intel — November 16, 2026

Sources scanned: X (**reachable, thin.** Five phrasings via `site:x.com` returned mostly stale threads and profile pages; I snowflake-decoded fifteen status IDs rather than trusting the index — @froessell's toolkit dates to 3 February, @tomkrcha's Code on Canvas to 15 April, @MengTo's DESIGN.md notes to 25 April, @JaynitMakwana and @Ronycoder both to 20 October, @hewarsaber to 26 October. Exactly one landed in-window: **@UnrealEngine on AI-assisted level design, 11 November** — judged and dropped, because game level design teaches nothing transferable to a schedule screen. No in-window design-craft post cleared the bar. X: available but produced nothing usable today). Reddit (**JSON API blocked on all six subs again** — `graphic_design`, `web_design`, `UI_Design`, `midjourney`, `StableDiffusion`, `FigmaDesign` each returned an identical 190,240-byte challenge page, one attempt each; `web_search` fallback returned only multi-year-old threads with no retrievable dates, so no Reddit item is judged — again). HN (**`hnrss.org` 502 on all three feeds**; used the Algolia `search_by_date` API instead — 8,008 `design` hits since 9 November, top 40 reviewed; design-relevant in-window stayers were Doop, TouchSynth, Paperwall, Copper-KiCad and Loadsketch). GitHub (REST `ai design` created>2026-11-09 — 1,690 results, top 15 read — plus topic searches on `typography`, `figma`, `design-tools`, `generative-art`, `image-generation`, `design-system`; the last five returned nothing inside the window, only `typography` did). Google News (60 items across two feeds; only 2 in-window, both thin). Plus targeted index reads of Design Week and Creative Boom for in-window craft coverage. Candidates considered: 52. Passed the bar: 7.

Screened and dropped for lack of evidence rather than quality: **Ford's design chief on AI in car styling** (Detroit Free Press, 15 November — in-window and on-thesis, but the article is paywalled from the second paragraph; the two visible sentences are not a breakdown), **D&AD's AI & Creativity Report 2026 / "The Cost of the Shortcut"** (the Creative Boom piece that surfaces the best line in the genre — *"Live prompts for the word 'ketchup'. The model returned Heinz, almost every time. Forty years of distinctive brand-building set the default"* — is dated **18 August 2026**, three months stale, so the report itself needs a separate look), **Figma disabling Make Design after it cloned Apple's Weather app** (resurfaced at 113 points on HN this week but the 404 Media story is **2 July 2024**), **Afterbyte Mono v5.0.0** (11 November, OFL, 2,500 glyphs — real and honestly documented, but 1,508 of those glyphs derive from Noto Sans Mono and it ships one Regular weight with no variable axes; a mono for code editors, not a brand face), **kaankiziltug/logo-design-skill** (7,037 stars but created 26 September and last released 20 October — out of window), **openpencil** (7,252 stars, v0.8.5 on 27 October — out of window), and previously covered and deliberately not re-judged: suzhe-ui, Inrond, wensity/skills, sui-motion-graphic-reel, resocket, Goeist, Fontroom, Brandrail, Antislop, OpenDesigner, MiniMax-H3.

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| design-engineering (AgentsORG) | Tool / Workflow | 👀 Watch it | Twenty-two verbs, a grader and a design council — and a benchmark that admits its own effect is statistically nothing |
| craft (diego3g) | Workflow | ✅ Adopt it | States are a required step, not an afterthought, and every skill was written against a failing scenario first |
| real-site-design | Technique | ✅ Adopt it | Nineteen measured fingerprints from 29 rejected designs, and a checker that exits non-zero |
| Doop v0.15 | Tool | 👀 Watch it | An open-source canvas where agents stream editable work next to your cursor — alpha, but the artifact stays alive |
| Material 3 Expressive Skill | Tool | 👀 Watch it | "Express with intent" is the right rule; the wrong system for our surfaces |
| Landor × Crystal Ski | Idea | ✅ Adopt it | The brand device is cut from a letter in the wordmark, then made to do every job — steal the derivation, not the snowflake |
| Max Cameron's AI cigarette packs | Idea | ❌ Skip it | Beautifully straight-faced craft in service of a joke a hospital cannot tell |

---

### design-engineering — a skill graph that publishes its own null result
**Link:** https://github.com/AgentsORG/design-engineering · **v4.8.0 published 13 November 2026** (v4.4.0 on the 10th, v4.6.0 the same week) · MIT · repo public 10 November · 5 stars, 1 fork · 62 commits, one human contributor (HKTITAN) plus dependabot
**Type:** Tool / Workflow (skill graph + 13 agents + a benchmark)

**What it is:** A design-engineering skill for coding agents with 22 verbs behind one entry point — `review`, `polish`, `motion`, `tells`, `a11y`, `tokens`, `sound`, `council`, `grade`, `svg`, `stage`, `mobile`, `break`, `ship`, `film`, `diagram`, `options`, `pick`, `name`, `which`, `agentation`, `pov`. It reads a design brief, routes the request to the one node that owns it, and returns a Before / After / Why table where every "Why" cites the reference node that owns the rule. Thirteen specialist agents (design-council, design-judge, design-grader, ui-reviewer, motion-auditor, anti-pattern-scanner…) are delegation targets, each generated into Claude Code, Codex, Cursor, Gemini CLI and OpenCode from one source file.

**What's good about it:** The benchmark. A vendor in this category published a 219-run ablation of its own product and reported: with the skill, Opus 5.5 passed 91.4% of the rules; without it, 86.8%. **"The gap is 4.6 points, with a 95% interval from −1.9 to +11.1. The smallest gap this run could tell apart from noise is 9.2 points, so this one is noise."** It also reports the cost: $0.34 a run against $0.11, and 63 seconds against 29. Then it does something I have not seen any other design-skill vendor do — it strips its own parts out one at a time and reports that **no cluster moved the score past its noise floor**, naming six clusters "slim" and three "not measured at all, because no task exercises them." That is a design director's instinct applied to a product: publish the result that makes your own marketing harder.

**Pros:**
- **The scoring architecture is the best idea in the brief.** "Checks first. Deterministic checks run before any judge… **A check can only cap a score; only judges raise it.**" The worked example: judges said 7.1, a 2.9:1 contrast measurement capped it at 6.4. That is exactly how a studio review works — a senior can fall in love with a screen, but a gutless contrast reading still sinks it.
- `tells` — AI-default fingerprints in UI, code *and copy*, delivered as a deletion list. Deletion lists are the only review feedback that reliably changes the next draft.
- Real provenance for its rules: Emil Kowalski's practice, Vercel's design guidelines, Benji Taylor, Jakub Krehel, Apple's audio-haptic principles, and 47 launch films measured frame by frame. The film corpus is public under `docs/research/launch-films/` with the numbers attached.
- `pov.md` is a single file where taste overrides the skill's defaults, and seven worked forks ship with screenshots of the same card drawn seven ways — a genuinely useful demonstration that a system and a look are different objects.
- Installer is idempotent, backs up settings before editing, `--dry-run` first, `--uninstall` removes exactly what it wrote.

**Cons:**
- **Its own data says it does not reliably work.** A 4.6-point gain inside a ±6.5 interval, at three times the cost, is not a product claim — and the honest reading is that on these 23 tasks a strong model was already near the ceiling (86.8% unaided, 30 of 55 runs perfect).
- **It benchmarked the code, not the picture.** The README concedes it: *"a modal can pass every rule and still look wrong."* Every number in the repo is a regex over source text. Nothing measures whether the screen is good.
- Five stars, one human contributor, six days public — and the version numbers (4.4 → 4.8 in a week) show it was developed privately first, so the star count understates nothing and the community has vetted nothing.
- 22 verbs and 13 agents is a *system*, not a tool. Installing it changes how the agent behaves across every task in the repo, and the ablation says most of that surface is unmeasured.
- Three losses are documented and revealing: the skill arm kept an infinite `yoyo` loop in 2 of 3 tries on the task written to stop it, and left out a `ch` line length in 2 of 3 tries on the typography task. The parts it is least good at are typography and restrained motion — the two that matter most to us.

**Should we...**
- 👀 **Watch it** — and steal three things this week.
**Why:** The market spent the last fortnight selling constraint as prose, and yesterday's scan ended on the correct suspicion: rules written in a `DESIGN.md` are context, not enforcement. This repo is the first one I have seen that both enforces (the contrast cap, the `check` gate, the deletion list) *and* measures whether enforcement helped — and when the measurement came back flat, it printed the flat measurement. That combination is worth more than the tool: it gives Shareef a way to answer "did the design skill actually improve the output?" with a number instead of an opinion, which is the question an administrator will eventually ask about any of this. The three things to take without installing anything: (1) the **cap-only scoring rule** for our own reviews — automated checks may lower a verdict, never raise one, so a design can't be talked up past a failed contrast reading; (2) the **`tells` verb's shape** — a deletion list, not a suggestion list, run on any generated page before it reaches a meeting; (3) the **ablation habit** — before we credit a tool with the improvement, remove it and see if the output actually changes. Skip the 22-verb install until someone has run the bench themselves; a five-star repo with a null result deserves a second dataset, not a faith commitment.

---

### craft — design skills where "every state" is a required step
**Link:** https://github.com/diego3g/craft · created **15 November 2026**, pushed the same day · MIT · 62 stars, 1 fork · by Diego Fernandes (@diego3g)
**Type:** Workflow (seven skills + a plugin + a design brief file)

**What it is:** A design-skill plugin for Claude Code, Claude Desktop, Codex, OpenCode, Cursor, Gemini CLI, Copilot and Windsurf. Seven skills behind one router: `craft-setup` interviews you one question at a time and writes `DESIGN.md` plus foundation tokens and base components; `craft` designs a page or flow by **listing every state the screen can be in before drawing it**; `craft-states` enumerates empty, loading, error, long-content, permission and offline states *and fills them with realistic messy data*; `craft-explore` draws three directions that must differ in structure, interaction or density — "never just new colours"; `craft-system` audits role-named tokens and a per-component states matrix; `craft-sync` moves a system that already lives in code into the design tool and returns the guide's changes as a reviewed diff; `craft-critique` renders the design, looks at it, and reports hierarchy, spacing, contrast, text, consistency and motion ranked by impact.

**What's good about it:** The ordering, and the test discipline. It stops for approval at exactly two points — scope and the state list — and writes decisions into a dated log inside `DESIGN.md` so "Monday's decisions survive into Thursday's session." And the repo's own claim is checkable: `tests/scenarios/` contains **nine scenario folders**, one per skill plus a workflow, and the README states that "every skill was written test-first: scenarios ran without the skill, then with it." A scenario that fails before the change and passes after is the difference between a prompt and a component.

**Pros:**
- **States before pixels.** Most AI design output fails not because the layout is ugly but because it only ever draws the populated happy path — no empty table, no failed submission, no overlong attending name. Making the state list an explicit, approved artifact is the single highest-value process change available to the Unified Platform, and it is free.
- `craft-explore`'s rule — three directions that differ in *structure, interaction or density*, never in colour — kills the reskin masquerading as a concept. That is exactly fingerprint #1 in this brief, caught at the brief stage instead of the review stage.
- "Your project wins": every rule about *look* is labelled a default, and if the existing system does something else the agent follows the system. The correct posture for a platform with locked decisions.
- It tells you when it touches a shared component, and `craft-sync` treats design and code as one change rather than two that drift.
- Tool-agnostic adapters (Paper MCP, Figma MCP, plain HTML fallback) — no vendor lock, and HTML fallback means it works on a locked-down machine.

**Cons:**
- **One day old, 62 stars, one author, and the Figma adapter is untested** — the README says so: "The Figma adapter hasn't been tested yet, so reports are welcome." The path most of our work would use is the unproven one.
- No rendered evidence at all. There is no screenshot of a screen it produced, no before/after, no benchmark. The test-first claim is about skill *structure*, not about output quality — a scenario can pass while the design is dull.
- The `DESIGN.md` is still prose the model may drift from. The critique pass exists, but nothing in the repo fails a build; it is self-review, which is the weakest form of enforcement.
- Seventeenth entrant in a genre that has shipped a design-skill pack roughly every day since 8 November. The category is converging on the same rituals, and this one's distinguishing feature is process rigour rather than a new idea.
- Diego Fernandes is a well-known educator with a large audience — 62 stars on day one is momentum, not vetting.

**Should we...**
- ✅ **Adopt it** — the state-list discipline specifically.
**Why:** The Unified Platform's real quality gap is not typographic — it is that generated screens are only ever designed for the state where everything works. A call-out flow drawn with three residents, one absent, and a successful submit is a mockup; the same flow with a duplicate submission, a name that overflows the column, a shift that returns no eligible residents, and a request made from a phone on a bad connection is a screen. `craft-states` formalises that list, fills it with realistic messy data, and refuses to proceed until someone approves it — and that ritual costs nothing to run by hand, with or without the plugin. Take the two stop points (scope, states), the dated decision log, and the prohibition on colour-only "directions." Install the plugin on one screen — the Sub-I application form is the right trial, because it has every state and almost none of them designed — and if it produces a state matrix we would not have written ourselves, it earned its place. Test the Figma path before trusting it; the HTML fallback is the safe route today.

---

### real-site-design — nineteen measured AI fingerprints and a script that fails the build
**Link:** https://github.com/lisbeth718/real-site-design · created **11 November 2026** · MIT · 5 stars, 0 forks · by lisbeth718
**Type:** Technique (a method + two Playwright scripts + a measured corpus)

**What it is:** A Claude Code skill built on one observation: asking for a different style does not fix AI-looking sites, because the *skeleton* survives the reskin. So it measures **three real sites in the same category** — actual fonts, sizes, widths, radii, colours, imagery, nav and footer — and designs *inside the numbers those sites agree on*. It ships `measure.mjs` (prints a comparison table or JSON per URL: loaded fonts, body and h1 metrics, max content width, nav items, button radius and height distributions, card structures, footer columns, block order in the first 900px), `check.mjs` (19 fingerprint tests, screenshots at 1440×900 and 390×844, PASS/FAIL/SKIP with the measured value, **exits 1 on failure**), and `references/claude-fingerprints.md` — the corpus write-up.

**What's good about it:** The corpus is the real deliverable. **29 AI-generated designs, all produced by Claude, all rejected by the client** — 24 design boards (six "directions" each across four sites) plus four live sites plus one pilot rebuild. The counts are regex over the actual source, with samples hand-checked. Two findings land hard. First: *"the stated 'direction' changes the font, the colour and one hero gimmick. It does not change the page skeleton, the content, the rule system or the code idioms."* Evidence: 24 of 24 boards reuse the site's existing copy; vocabulary Jaccard between boards of the same site was 0.51, 0.38, 0.34 and 0.23. Second, the numbers behind the look we keep circling: fixed centred shell at 1240–1400px in **29 of 29** (exactly 1280px in 13); `h1` in `clamp(…vw…)` in **27 of 29**; negative heading tracking in **25 of 29**; heading line-height ≤1.05 in **23 of 29**; near-white ground in **25 of 29**, with warm off-white specifically in **14 of 29**. That is the "AI designer" aesthetic reduced to a grep.

**Pros:**
- A falsifiable method that requires no model: measure three peers, design inside the agreement. It is competitive audit, the thing good studios do before a pitch and almost nobody does before a prompt.
- `check.mjs` exits non-zero, so it can gate a build. After a fortnight of "constraints as prose," a script that fails is the only kind of constraint that survives a confident agent.
- The fingerprint file states its own thresholds so you can disagree with them, and the README's Limits section is unusually honest: "On its own it produces conventional results: correct for the category, but easy to forget."
- It names the trap that the whole anti-slop genre is walking into — the direction changes and the skeleton doesn't — and then measures the skeleton rather than theorising about it.
- Conventions are versioned with a "Last measured" date per category, so the reference set expires visibly instead of rotting silently.

**Cons:**
- **Five stars, one author, one portfolio.** "The method was validated on one portfolio of 4 sites (29 rejected designs and one accepted rebuild). It has not been tested across many teams or categories." All four sites are Claude-generated, so the corpus measures one model's habits, not AI design in general.
- The tells are web-marketing tells. Nothing in the 19 fingerprints covers a dense application UI — a schedule grid, a form with 40 fields, a role-gated dashboard — which is most of what Shareef builds. Its `max-width:1280` fingerprint, for instance, is correct-by-default in app chrome.
- The detectors are heuristics and the README says so: unusual markup can hide a nav or merge footer columns, and PASS only means the fingerprint wasn't found.
- Designing to the category median produces, by construction, a category-typical site. The author's own fix — one signature element drawn from a real fact about the product — is a single line of guidance carrying the entire distinctiveness load.
- Needs Node and a Playwright Chromium download; harmless on a laptop, a nuisance on a locked hospital image.

**Should we...**
- ✅ **Adopt it** — the method now, the checker on one surface.
**Why:** This is the only item today that attacks the actual mechanism of slop rather than the appearance of it, and it arrives with counted evidence. The transfer to Shareef's work is direct and slightly uncomfortable: the residency programme's marketing pages and the Sub-I welcome packet are competing in a category — academic medical recruitment — where every peer site uses the same blue banner, the same smiling-resident-in-a-corridor photograph and the same "training the future of…" headline. Nobody has ever measured those peers' actual numbers. Ten minutes with `measure.mjs` against three real program sites produces a table of what the category agrees on, and that table is the brief. Then the fingerprints become a pre-flight test on the output: run `check.mjs` against any page an agent generates, and the failure list — giant tight `clamp()` h1, warm off-white ground, one accent, hairline-ruled list, one-line footer — is the exact set of decisions to make deliberately rather than inherit. The one discipline to add, because the repo under-supplies it: the signature element. If the measured page could carry another department's logo unchanged, the measurement has produced a competent average, and the job is half done.

---

### Doop v0.15 — an open-source canvas where agents design next to your cursor
**Link:** https://github.com/kgoedecke/doop · https://doop.design · **v0.15.0 and desktop-v0.14.0 both published 16 November 2026** · AGPL-3.0 · 2,062 stars, repo created 22 August, pushed today · by Kyle Goedecke · *previously filed to the vault — the project is not new; the 0.15.0 release and the desktop build are this week's news.*
**Type:** Tool

**What it is:** An open-source alternative to Paper.design: a multiplayer design canvas for humans *and* agents. Every design lives on a shareable Canvas; humans edit in the browser; agents edit through a built-in **MCP server** and stream their work in live — cursors, presence, frame edits and agent status all visible to everyone in the file. Claude Code, Codex, ChatGPT, Cursor, OpenCode or any MCP client connects once; a built-in Doop Agent can also take a queued card or an @mention and design unsupervised. Pages within a canvas, click-through prototypes, threaded comments on elements, an activity feed, and a per-project style-rules file that every agent follows.

**What's good about it:** It makes the agent a *collaborator in the file* rather than a generator you copy from. That is a structural difference: the artifact stays editable, the edit history is visible, comments attach to the element, and a human can take the cursor at any point — none of which is true of a generated PNG or a screenshot of a screen. The multi-provider MCP design means the tool outlives whichever model is best this quarter, and "agents inherit exactly their human's access" is the correct permission model rather than an afterthought.

**Pros:**
- Editable artifact, live presence and per-element comments — the design file survives contact with a human, which is the whole argument against generated mockups.
- Any MCP client, one connection, plus a headless path (agent key as bearer header) for CI or n8n — so the same canvas can be driven by a person and by a pipeline.
- A project-level style-rules file that every agent follows: a token/system layer agents read, inside the tool where it can be seen.
- Real velocity on a real base: 2,062 stars, sixteen minor versions since August, shipping today.
- AGPL and self-hostable, with API, WebSocket and MCP on one port — deployable inside a network that will never approve a SaaS design tool.

**Cons:**
- **v0.x.** Pre-1.0 with sixteen minor versions in three months means the file format and MCP surface are still moving; anything built on it this quarter will need re-testing next quarter.
- It is a *canvas*, not a design system. Nothing here enforces a token, a spacing scale or a state matrix — the style-rules file is prose again, and the agent is free to ignore it.
- Two thousand stars and an 85KB README is a lot of surface for a small team; the failure mode of self-hosted collaboration tools is operational, not conceptual.
- Relevance to our actual surfaces is low. The Unified Platform is code, not a canvas; the Chapter Player is code; social is stills. This solves a problem Shareef does not currently have.
- AGPL is a real constraint if any of this ever sits behind something the department sells.

**Should we...**
- 👀 **Watch it** — as a pattern, not a purchase.
**Why:** Yesterday's brief made the point with gpucanvas that an agent should read *structure* — a tree with ids, a region reference — rather than a screenshot it has to narrate. Doop is the same idea with a collaboration layer on top, and it is the more mature expression of it: agents with cursors in a shared file, edits visible as they land, comments pinned to elements. What matters for us is the pattern it proves — when an agent works inside the artifact, review becomes a conversation in place instead of a paragraph describing what's wrong. That is the same insight as @TheoKode_'s "correct by pointing, not describing," and it is worth holding in mind the next time someone proposes reviewing generated screens by screenshot. As software it waits: pre-1.0, prose-based rules, and a canvas we don't currently use.

---

### Material 3 Expressive Skill — "express with intent," written as a rule
**Link:** https://github.com/asimawdah/material-expressive-skill · created **16 November 2026** · MIT · 15 stars, 1 fork · by Asim Awda
**Type:** Tool (agent skill)

**What it is:** An Agent Skill for designing, implementing and reviewing interfaces in **Material 3 Expressive** — Google's more tactile, shape-and-motion-forward evolution of Material — across Android/Compose, Wear OS, Flutter, Web and "adapt honestly elsewhere." The root `SKILL.md` is a decision engine that loads focused references only when a task needs them (expressive principles, foundations and tokens, components, motion, adaptive layouts, accessibility, platform guidance, a review checklist), plus a design-brief template and an implementation handoff template.

**What's good about it:** Its third principle is the sentence the entire "expressive UI" trend needs: **"Express with intent. Choose only the expressive treatments that make the important information or action easier to understand."** Principle two is the counterweight: **"Preserve Material semantics. A button must remain recognizable as a button; selected, disabled, destructive and navigational states must remain clear."** And principle five is the one our platform keeps failing — **"Ship complete states. Loading, empty, error, success, disabled, focus, hover and pressed states are part of the design."** For a design language currently being copied by every AI-generated mobile screen as "big rounded blobs and bouncy springs," a document that says *louder is not the same as clearer* is genuinely useful.

**Pros:**
- The intent test — does this expressive treatment make the important thing easier to understand? — is portable to any system, including ours, and kills decorative motion in one question.
- Explicitly refuses to over-claim platform parity: "do not claim native Compose expressive parity" on Web, and "does not bundle third-party UI packages." Rare honesty in this genre.
- Accessibility and internationalization are stated as release requirements, not a checklist appendix — keyboard, screen reader, contrast, text scaling, reduced motion, localization.
- Real engineering hygiene: a `validate_skill.py`, unit tests, a GitHub Actions validate workflow, and references that cite official sources with a version-verification policy.

**Cons:**
- **Material is the wrong system for Shareef.** The Unified Platform is Inter, one accent, flat SVG icons, a premium dark surface. Material's tonal palettes, elevation model and shape morphing would fight every one of those decisions, and adopting the skill risks the agent "helpfully" Materialising a bespoke interface.
- One day old, 15 stars, one author, no evidence of output — and no benchmark, in a week when a competitor published a null result.
- The expressive treatment is precisely the aesthetic now saturating AI-generated mobile UI: giant rounded shapes, colour that carries meaning, springy motion. Used without principle three it accelerates the convergence it claims to discipline.
- Android/Compose-first. The Web guidance is explicitly the adapted, non-native path, which is the only path we have.

**Should we...**
- 👀 **Watch it** — read principle three, skip the palette.
**Why:** Not for the system — for the two sentences. "Express with intent" and "preserve semantics" describe the failure mode of every AI-generated interface I have reviewed this year: the model adds shape, motion and colour because it has learned that expressive screens look designed, and strips the affordances that told a user what was tappable. On the Unified Platform this shows up as hover states that read as decoration and disabled states that read as enabled. Lift the intent test into our review checklist — *name what this treatment makes easier to understand, or remove it* — and lift the states requirement, which is the same rule `craft` enforces from a different direction. Leave Material's palette and motion language where they belong; a urology platform that suddenly morphs its buttons into pebbles will look like it was generated, which is the exact outcome this brief exists to prevent.

---

### Landor × Crystal Ski — a brand device cut from a letter
**Link:** https://www.designweek.co.uk/landor-reveals-snowflake-inspired-visual-identity-for-crystal-ski/ · published **16 November 2026** · Design Week · work by **Landor** (WPP) for TUI-owned Crystal Ski; campaign by VML
**Type:** Idea (a brand system worth studying)

**What it is:** A full rebrand of the UK's largest ski holiday provider, built on audience research that identified **nine new target groups** and a positioning line — "Escape to higher ground" — that moves the category from booking logistics to the restorative effect of the mountain. The centre of the system is the **"Crystal Lens"**: a sixfold-symmetry device *formed by the shape of the letter "Y" in the wordmark*, used as a framing tool that refracts imagery so one device can hold saunas, hot springs, raclette dinners and pistes. Supporting it: a wordmark with angled letterforms and crystalline cuts plus a diamond dot over the "i", the **Season** family from Display Foundry (structured Season Sans paired with expressive Season Mix), and a palette named from the environment — mountain stone, cloud white, evergreen, aurora, glacier, midnight, twilight, alpenglow — with photography deliberately shot from unexpected angles.

**What's good about it:** The derivation. A snowflake is the most obvious, most stolen, most stock-icon mark in this category — and Landor avoided the cliché by refusing to draw one from nothing. The device is *extracted from a letter in the client's own name*, which means it cannot be lifted into another brand without the wordmark coming with it. That is the structural difference between a logo system and a decoration: the mark is entailed by the identity rather than applied to it. Second, the naming of the palette: colours named for the place they came from (alpenglow, mountain stone) rather than for their job ("primary", "surface-alt") keeps a system legible to non-designers, which matters in a TUI-owned business where the brand has to survive marketing decks. Third, the type pairing is a real decision — a structured sans carrying information and an expressive cut carrying voice, from one family, which is a cheaper and more coherent move than buying two families.

**Pros:**
- A device derived from a letterform, not from a category cliché — the single most transferable idea in the brief, and it costs nothing to apply.
- Applied across a genuinely wide surface list without becoming wallpaper: digital billboard, social grid, smartwatch face, luggage tag, hard-shell case charm, print — the device changes density with substrate.
- A named palette taken from the subject's own environment instead of an abstract scale; usable by people who are not designers.
- One type family in two registers (structured + expressive) rather than two competing families.
- Photography direction as part of the identity — "unexpected angles" — rather than a stock library note.

**Cons:**
- **"Escape to higher ground" is a positioning line, not a thought.** Substitute any premium travel brand — a spa, a safari operator, a wellness retreat — and it works unchanged. Antislop's swap test fails it.
- It is Landor's own account of its own strategic brilliance, relayed by trade press: no client numbers, no before/after recognition data, no evidence the lens survives a TUI price banner.
- The sixfold lens is one bad application away from becoming a decorative overlay on every image — the risk of any framing device is that it becomes the wallpaper it replaced.
- Ski holidays are a category with a natural gift (snow has real geometry). Transplant the method to urology and there is no ready-made sixfold symmetry; the derivation has to be earned from an actual property of the subject.
- Nothing here is AI-related. It is included as a craft benchmark, not as a tool.

**Should we...**
- ✅ **Adopt it** — the derivation method.
**Why:** This is the answer to the question yesterday's brief ended on: how do you make work that is recognisable rather than merely correct? The measurable, repeatable answer is *derive the device from something only this subject has*. Crystal Ski got a letter Y. Montefiore Urology has: a department that is genuinely one of the largest in the country, a residency programme with 28 filmed faculty interviews nobody else has, and clinical subject matter — imaging, uroflow curves, cystoscopy — with real, ownable geometry. The transferable exercise for the Sub-I packet and the residency social system is a half-day one: list five properties that are true of this programme and no other (a number, an instrument, an anatomical form, a phrase from a resident), then build the device out of one of them instead of out of a template. Where Landor's own work is weakest is instructive too — the positioning line fails the swap test even though the mark passes it. The mark is the part worth copying; the words still have to be written.

---

### Max Cameron's AI cigarette packs — the straight face is the technique
**Link:** https://www.creativeboom.com/news/max-cameron-roasts-the-arrogance-of-ai-tech-bros-with-subversive-cigarette-packaging/ · published **16 November 2026** · Creative Boom · project by Max Cameron, senior copywriter at Mother London
**Type:** Idea (a craft demonstration)

**What it is:** A personal project: cigarette packets branded **"Palmallantir Original Silicon,"** a pun on Pall Mall and Palantir, on which the health warnings have been replaced with AI-hype reassurances — "Keep smoking, AI will save you," "AI cancer cure definitely on the horizon." The trigger was a Palantir CTO's anecdote about developers taking up smoking because they were confident AI would cure cancer. Shot as found objects on pub tables, on phones, so they read as "spotted" rather than launched.

**What's good about it:** The craft rule, stated by the author without flinching: **"We had to use the classic cigarette packets and treat the design as straight and real as possible. A blink-and-you-miss-it kind of approach."** He reproduces the category's conventions — the typeface on the pack, the warning-panel geometry, the photographic style of the health imagery — with enough fidelity that the joke only lands on second look. And the distribution decision is a design decision: photographed badly, on a phone, in a pub, because it had to look like evidence rather than an ad. That is a proper understanding of the medium it was made for.

**Pros:**
- Fidelity as the mechanism: the comedy is entirely in the print production values being correct. A sloppier packet would be a poster; an accurate one is a found object.
- Restraint in the writing — three or four words per warning, no exclamation marks, no explaining.
- The "spotted" photography is a deliberate distribution format, not a budget constraint dressed up as one.
- It is a clean example of bending a category code rather than breaking it: every convention of the pack is obeyed, and one element — the warning — is inverted.

**Cons:**
- **The subject is unusable for us.** A hospital marketing AI as a lethal addiction is a joke Shareef cannot make, and a residency programme that lampoons its own tools is a recruitment liability.
- It is a personal project with no client, no brief, no constraint, and therefore no evidence it survives one. The pub photos are charming; they demonstrate nothing about working under a compliance review.
- The reception was, in the author's own words, "pretty divided… some just called me a bot" — a reminder that irony travels badly on a platform that cannot read tone.
- It is commentary *about* AI, not AI-assisted design — included only because the technique is real.

**Should we...**
- ❌ **Skip it** — the technique is worth naming, the artifact is not ours to use.
**Why:** The one thing to carry into our own work is the fidelity rule, and it applies directly to the opposite kind of project: when we make something that has to be believed — a Sub-I welcome packet that reads as a real institutional document, a call schedule that looks like a schedule and not a dashboard — the credibility is in reproducing the conventions exactly and then changing one thing. That is the same discipline as Landor's derivation, arriving from the other direction: obey the code, then bend one element deliberately. What we must not do is what the project does. A department that spends this year defending AI use to skeptical faculty cannot also publish satire about AI hubris, and the brief's job is to keep those two rooms separate.

---

## Slop Radar
- **Warm off-white is now measurable, not just felt.** 25 of 29 rejected designs used a near-white ground; **14 of 29 used warm off-white specifically** (`#f1ece1`, `#f3eee3`, `#fbf4e4`, `#f6f4ee`). The cream page is as much a tell as the purple gradient was — and it is the one our own Sub-I materials are closest to shipping.
- **The reskin masquerading as a direction.** Six "directions" per site, and the vocabulary overlap between them was up to 0.51 Jaccard with 24 of 24 boards reusing the same copy. If three options share their headings, you were shown three typefaces, not three ideas.
- **Design-skill packs have become a genre with rituals but no evidence.** A pack a day since 8 November; the differentiator is now whether the vendor publishes a number. One did this week and the number was *flat*. Treat "install our skill" as unproven by default, and treat a vendor who reports its own null result as the only one currently worth reading.
- **"Expressive" as the new "premium."** Shape morphing, springs, giant radii and colour-as-meaning are arriving as a package, and generated mobile UI is already saturated with them. Expressiveness without an intent test is just a louder default.

## Overall Assessment
The story of the fortnight has been constraint, and this week it grew a spine: two of today's four tools ship something that can *fail* — a checker that exits 1, a scoring rule where automated checks may cap a verdict but never raise one — and one of them published a 219-run benchmark showing its own 4.6-point gain sits inside a ±6.5 noise interval at three times the cost. That null result is the most valuable artifact in the brief, because it disciplines the entire category: design skills are not improvements until someone measures the output, and almost nobody is measuring the output. The other movement is subtler and more useful — the best method today is not generative at all. Measure three real sites in your category, design inside the numbers they agree on, then add exactly one element derived from a fact only your subject has. That is a studio's competitive audit and a design director's derivation, arriving as open-source scripts. The single highest-leverage move for Shareef this week costs an afternoon and no software: run that measurement against three real academic-urology recruitment sites, write the agreed-on numbers into a one-page brief, design the Sub-I packet inside them, and then apply the one test that separates craft from competent — if the finished page could carry another department's logo and still make sense, it isn't art-directed, it's generated.
