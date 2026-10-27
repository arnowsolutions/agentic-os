# AI Design Intel — October 24, 2026
Sources scanned: X (available — `site:x.com` returned live post/article URLs across four phrasings; one in-window post is listed below, plus the caveat that most surfaced posts were undated), Reddit (JSON API **blocked — 403 on all six subs**, each returning the identical 190,240-byte HTML challenge page; `site:reddit.com` web_search fallback returned real threads — r/graphic_design "AI was supposed to replace designers", r/UI_Design "How do I make this look less like AI slop", "Do hero eyebrow labels improve clarity" — but all undated and conceptual, nothing in-window and craft-specific, so no Reddit item appears below), HN (hnrss `newest?q=AI+design` parsed; `generative+design` and `typography` feeds returned empty payloads — nothing in-window), GitHub (search API + 8 topic queries created since 2026-10-17: ai design, generative-art, typography, figma, image-generation, antislop, design-tools, brand identity, poster layout), Google News RSS (2 queries), last30days-pro aggregator, plus a direct editorial sweep of Creative Boom (RSS feed parsed) and It's Nice That. Candidates considered: 46. Passed the bar: 7.

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| Ideogram Vector 1.0 | Tool | 👀 Watch it | First mainstream model that outputs *native SVG paths* instead of pixels — real production files, but layer grouping is missing and every quality claim is still the vendor's own showcase |
| Apple Music "made by sound" identity | Technique | ✅ Adopt it | Months of in-camera physics and a custom SF Pro lowercase cut — the cleanest available argument for craft over generation, and a direct brief for our marketing photography |
| Generative Branding — the DIRECT framework | Idea | ✅ Adopt it | Six moves that put the designer back in charge of a generator: diagnose, intend, range, express, compose, transfer. Free Module 01 |
| dsh-swiss-grid | Tool | ✅ Adopt it | Müller-Brockmann's grid system as executable code: real 版心/column/baseline math, print-ready SVG→PDF, and a grid-overlay proof that can't be faked |
| logo-design-skill | Tool | ✅ Adopt it | Ten real logo tests (16px pixel, one-colour, reversed, squint, mirror, competitor shelf) + a 1,400-logo classified library — the discipline our marks never get |
| Desk Studio | Workflow | 👀 Watch it | A role-based studio in the CLI (three roughs, an art-director pick, polish, proof) — right shape, but its scores are self-graded and it only ships social cards so far |
| chromary | Tool | 👀 Watch it | Colour as engineering: OKLCH scales, WCAG/APCA contrast math, gradient recipes — fills a real gap, but it's a reading list plus six thin skills, not a finished tool |

---

### Ideogram Vector 1.0
**Link:** https://ideogram.ai/models/vector/
**Type:** Tool
**What it is:** Ideogram's first vector model, launched October 22 at noon ET, which outputs editable SVG paths rather than raster pixels — either from a text prompt ("text to vector") or by converting an uploaded image ("image to vector"). Live in the Ideogram app, through the API (`/v2/svg/generate/ideogram-vector-1`), and on fal.
**What's good about it:** This is the first time a mainstream AI image company has shipped a file format the production floor can actually use. Raster generation fails the moment artwork leaves a screen — print, embroidery, screen print, vinyl, laser cut. Every previous route was a lie dressed as one: Image Trace replicates pixel boundaries (jagged edges, redundant nodes, colour blobs no designer would draw). Ideogram is claiming native paths, and critically, it is claiming them from the company whose entire reputation was built on type rendering — so the claim that matters most is the testable one: *sharp typography*.

**Pros:**
- Native editable SVG is a structural change in the workflow, not a feature. Every shape lands as its own addressable element — recolour, move, rotate, resize one piece without wrecking the rest. That is the difference between a generated picture and a design asset.
- The image-to-vector endpoint at $0.10/image is the sleeper. Every ugly raster logo we've ever inherited — department lockups, old clinic marks, that one JPEG of a seal — becomes a clean scalable asset for less than a coffee. For a hospital department with fifteen years of accumulated bad logo files, that's an afternoon of real cleanup.
- Ideogram has genuine typographic authority. Its prior models hit roughly 90–95% text-rendering accuracy against 30–50% for general models, and "Design" style mode was purpose-tuned for typography-led images. If any vendor was going to ship a vector model that renders *letters* convincingly, it was this one.
- Pricing is unpunished: $0.13/$0.16/$0.20 per SVG (low/medium/high), $0.32 high with reference images. Cheap enough to test honestly rather than argue about.

**Cons:**
- **The `group` parameter is documented but marked not yet available.** So image-to-vector arrives as a flat pile of paths, not organised layers. For an illustration that can mean 2,000+ paths with no hierarchy. You will be doing the layer organisation by hand — which is most of the work you hired the tool to remove.
- No brand style presets, no style locking, no custom style training. Recraft has all three. If you run any volume of mark-making, consistency across runs is exactly where Ideogram gives you nothing.
- **No editing capability at all** — which Ideogram frames as product design ("generate in 4.5, produce in Vector"), but in practice means every iteration is a fresh generation. No prompt-based refinement of the paths you just got.
- Every published sample is Ideogram's own showcase. Independent verification hasn't happened — one writeup that went looking for the API docs couldn't find vector endpoints in the API overview at all. Documentation is lagging the announcement.
- The open question is unresolved: does "sharp typography" mean live text objects you can retype, or text converted to outlines? Ideogram hasn't said. For wordmark work that distinction is everything.

**Should we...**
- 👀 **Watch it**
**Why:** The direction is unambiguously right and this is the first honest move in it — but the two things it can't do (group into layers, hold a brand style) are precisely the two things that separate *asset generation* from *design*. Vectorise something old and inspect the path count before you believe the pitch. Where it belongs in our work: the Urology Unified Platform icon system is already hand-built SVG and should stay hand-built — a generated icon family won't survive the optical corrections a 24px interface demands. But the accumulated-brand-debris cleanup at $0.10 a shot, and *rough* wordmark exploration that lands in Illustrator rather than in a PNG you then trace badly, is real value. Do not let it near the Montefiore mark itself.

---

### Apple Music — "made by sound"
**Link:** https://www.creativeboom.com/news/apple-musics-new-logo-was-shaped-by-fred-again-and-a-bath-of-mineral-oil/
**Type:** Technique
**What it is:** Apple Music's first rebrand in eleven years, built by TBWA\Media Arts Lab with producer Fred again.. and NEST Acoustics. They composed a piece of music, broke it into individual notes, played each through a transducer sitting in a shallow bath of mineral oil, and filmed the resulting ripples and refractions in camera. That footage became the new musical-note icon and the surrounding visual system. The wordmark pairs the Apple symbol with a custom bold lowercase cut of SF Pro; Plau did the type consultation and vector reconstruction.
**What's good about it:** This is the strongest counter-argument to AI aesthetics anyone has produced this year, and it is made of physics. The identity was made by *doing a thing over and over until the thing behaved* — months of tuning sound against image because too many notes, or notes pitched too high, made the oil move so much the image became unreadable. That's a constraint discovered in the real world and then obeyed. The mark is described by the team as "a physical record of music rather than a picture of what sound might look like." No prompt produces that distinction. You cannot generate the residue of an experiment you didn't run.

**Pros:**
- Sound-first, visual-second. Inverting the normal order (visuals now, sound later, if anyone remembers) is a system decision, not a styling decision — and it's why the same composition works as both the logo genesis and the sonic mnemonic. The brand looks and sounds as one object.
- Restraint on the type: they didn't commission a new typeface to signal newness. They cut a custom bold lowercase of their own SF Pro, keeping it explicitly in the family. Confidence, not novelty — and it protects the wider design system instead of fighting it.
- The whole identity stays inside Apple's Liquid Glass language while still being distinctive. That is the single hardest thing in identity work: being recognisable *as yourself* without being invisible.
- The process itself is the content. A behind-the-scenes film directed by Joe Jackson, with Optical Arts, Time Based Arts on VFX, Trafik on colour and Model Citizen on the mix — the making-of is a legitimate brand asset, not a vanity extra.

**Cons:**
- Months of experimentation, a transducer rig, a producer, a sound studio, a VFX house, a colour house and a mix house. This is not a workflow. It's a budget line, and imitating the *form* of it (make something physically, film it) without the patience will produce affectation.
- The result is heavily dependent on Apple's existing equity. A bold lowercase SF Pro reads as confident because SF Pro is already everywhere; the same move from an unknown institution reads as an unmade decision.
- The oil-ripple vocabulary is now in circulation and will be copied badly within a quarter — frosted glass, ripples, light-caustic gradients over everything. The lesson to steal is the *method* (constrain physically, obey the constraint), not the *look*.
- The mark reads as abstract at small sizes and in monochrome; the system carries it, not the icon alone. That's a real deployment risk for anyone without Apple's surface area.

**Should we...**
- ✅ **Adopt it**
**Why:** Not the ripples — the discipline. Our marketing and social creative for the residency program is shot in actual rooms with actual people, and the temptation with an AI pipeline is to generate the "premium" version of a moment rather than photograph a real one. Apple just demonstrated, at maximum expense, that the thing that reads as premium is the *evidence of an experiment*: a constraint obeyed, a process visible, an artefact that could only exist because someone put something real in a tank. Concretely: for the Sub-I welcome materials and the residency campaign photography direction, write the constraint down before anyone opens a generator — what physical material, what light, what limit — and then let the shoot obey it. And for the Unified Platform brand layer: resist commissioning novelty. Extend the system we have, the way Apple extended SF Pro. The single most cited error in AI-assisted brand work is inventing a new look to signal that work happened.

---

### Generative Branding — the DIRECT framework (Carolina Gonzalez / carolletta, with Noe Golomb)
**Link:** https://x.com/i/article/2111798103628022118
**Type:** Idea
**What it is:** A course, written by an AI art director with twenty years of product design and design systems experience and an independent identity-studio founder, built around a six-move method called DIRECT — Diagnose, Intend, Range, Express, Compose, Transfer. Module 01 (Research & Brainstorming) is out and free; modules 02–03 will append to the same download. It follows one real brand from brief to guidelines using Adobe Express and Firefly.
**What's good about it:** The diagnosis is the most precise statement of our actual problem that I've read: "Ask any AI tool for logo ideas and you'll have forty in under a minute. A few will be good, many will be fine, and none of them will feel like the same brand." That is *cohesion*, and no model provides it. The framework's answer — a fixed division of labour where you write the decisions, the machine widens the options, and you narrow them again, always returning to cohesion — is not a prompt trick. It's an editorial process, which is exactly what a design director's job actually is. The line worth pinning above the desk: **"AI is the studio, not the author. You brief, you select, you refuse, and you lock what holds together."**

**Pros:**
- It starts from a structured brief with a written positioning, values, and — crucially — a *never-do list*, instead of a blank chat window. A never-do list is the single most useful artefact in brand work and almost nobody writes one for AI.
- The loop is revisitable rather than a ladder. You can enter at any stage and return to cohesion, which matches how identity work really moves (backwards, repeatedly, with the client in the room).
- Module 01 covers the stage where nothing visual is locked yet — the stage where AI does the most damage undirected. Putting the free module there is a considered choice, not a funnel.
- Co-authored with an identity studio founder rather than a prompt influencer, and the worked example (Flow Works, a retro men's yoga-gear brand treated as utility rather than spiritual performance) is a real positioning exercise with a defensible point of view.

**Cons:**
- **It is a paid partnership with Adobe** — the author is an Adobe Express/Firefly brand ambassador, the course is built around those two tools, and the disclosure is explicit in the article. The method is transferable; the tooling recommendations are not neutral.
- Only Module 01 exists. The parts that would most help us — logo construction, colour and type rules, imagery direction — are "coming soon," with no dates.
- The DIRECT acronym is syllabus-shaped. Six sequential English verbs described as a "loop, not a ladder" is a tension the framework doesn't fully resolve on the page.
- It's a course, not a document. There's no downloadable checklist or spec you can hand an agent — you get the pedagogy and then have to write your own machine-readable version.

**Should we...**
- ✅ **Adopt it**
**Why:** Because we already have an AI pipeline and do not have a written standard for when to stop it. This is the missing half of Hermes' design work: the copy desk has a QA gate, but image and identity generation has no *never-do list* and no cohesion test. The highest-value act this week isn't reading the course — it's stealing its structure and writing the two artefacts it implies for Big Reef and for the Montefiore Urology surfaces: a short positioning document (who it's for, what it promises, what it refuses), and an explicit never-do list for generated creative (no purple-blue gradients, no chrome, no liquid blobs, no fabricated clinical imagery, no invented patients). Then every generation gets judged against the list before it gets shown. That's the "taste is the split" argument made operational, and it costs nothing.

---

### dsh-swiss-grid
**Link:** https://github.com/summersummer-liu/dsh-swiss-grid
**Type:** Tool
**What it is:** A plugin that gives a coding agent the Swiss grid design system as executable code: it computes the page grid (版心/live area, columns, baseline, type scale), then builds print-ready **SVG → PDF** posters, book spreads, magazine pages and exhibition graphics — and outputs a **grid-overlay proof** alongside the artwork showing the layout actually snaps to the grid. Built as a distilled, executable summary of Josef Müller-Brockmann's *Grid Systems in Graphic Design* (1961/1981): a method reference, parameter tables, and a small rendering toolchain.
**What's good about it:** Every element must snap to a column line, row line, or baseline multiple. A unit cell is an integer number of body lines; the baseline derives from the cell (default cell ÷ 6); type sizes stay as multiples of the baseline. Margins follow print convention (head 1 : inner 1 : outer 2 : foot 3 for books). Captions and images occupy whole lines and cells — never half. And the delivery is always the pair: **artwork + grid diagram.** That last rule is the whole thing. It makes the invisible structure an artefact you have to hand over, which means it can be inspected, and therefore can fail.

**Pros:**
- It encodes *why*, not decoration. Baseline multiples and cell-derived x-heights are the actual mechanics of Swiss layout; almost every "Swiss style" skill pack is a mood board with Helvetica as the punchline.
- Real print production: parametric A-series poster builder with bleed, crop marks, TrimBox/BleedBox finalisation, and a verifier that checks page size = trim + 2×bleed, real Type0 (not Type3) glyphs, and crop marks. That's prepress discipline, not a mockup.
- The grid-overlay proof is a genuine QA gate — the layout either snaps or it visibly doesn't. Compare with a screenshot review, where misalignment hides behind anti-aliasing.
- Zero-dependency Python tools plus SVG/HTML sources, so output is editable rather than locked in a proprietary file. The tools also accept open-source CJK TrueType fonts, and the author explicitly warns about proprietary font licensing.
- Honest attribution: Milan-style credit to Müller-Brockmann and the Niggli edition, explicit "independent summary, not endorsed, no pages or scans redistributed" disclaimer.

**Cons:**
- It is a **DeepSeek Harness plugin first**; the plain-skill path (copy the folder into a skills directory) works, but PDF output requires Microsoft Edge or Chromium in a standard location, plus Python 3.10+ — a dependency chain that will break silently on some machines.
- Narrow by design. Posters, book spreads, magazine pages, exhibition graphics. It has nothing to say about interfaces, motion, or screen-based systems — which is most of what we actually ship.
- Eight stars, one release, created October 20. Effectively unproven, and one person's interpretation of a canonical book.
- The grid-overlay "proof" proves snap-to-grid, not good hierarchy. A layout can be perfectly on the grid and still be badly composed. The tool validates the floor, not the ceiling.
- Chinese-first documentation (README in both languages, but parameter tables and the 版心 terminology are primary-source CJK), and the poster builder requires you to edit a TEXTS/ART/colours block in Python — usable, but not a designer's interface.

**Should we...**
- ✅ **Adopt it**
**Why:** Because the absence of a grid is the exact reason AI-generated layouts look like AI-generated layouts. Generated design fails not on colour or font choice but on *increment* — nothing sits on anything, spacing is eyeballed into plausibility, and there is no structural promise to break. This tool makes the promise explicit and falsifiable. Where it lands immediately: residency recruitment posters and program announcements, where a real A-series poster with real bleed and crop marks delivered as artwork-plus-grid-diagram reads as institutional and considered rather than as a social tile blown up to A2. Second, as a discipline transfer — even for the Unified Platform, the rule "every element lands on a column line or baseline multiple" is a reviewable standard, and the grid-diagram-as-deliverable habit is one our interface reviews should adopt. Print capability we have never had in the pipeline at all.

---

### logo-design-skill (kaankiziltug)
**Link:** https://github.com/kaankiziltug/logo-design-skill
**Type:** Tool
**What it is:** An agent skill that turns Claude, Gemini CLI, Codex CLI, Cursor or Copilot into a disciplined identity designer — discovery and briefs, word mapping, mark-type selection, concepting, geometric construction, optical corrections, colour, typography, lockups, testing, presentation, delivery. Ships with a library of 1,400+ real-world SVG logos classified by mark type, technique, geometry, subject, typography, mood and industry, plus dependency-free Python tools that audit an SVG against logo principles and generate test sheets. Actively pushed — 4,376 stars and a commit on October 20.
**What's good about it:** The test sheets. A 16px pixel test, a one-colour test, a reversed test, a squint test, a mirror test, context mockups, and a competitor shelf test — that is the shortlist you are supposed to run before you show a mark to anyone, and it is exactly the list that gets skipped when the mark arrives from a generator in nine seconds. The skill also **stops at a checkpoint**: it shows concepts as one overview image with a recommendation and produces nothing further until you pick a direction, "because the kit is most of the work and only makes sense for an approved idea." That's a refusal to over-produce, which is the rarest behaviour in an AI tool. Optical corrections are named explicitly — overshoot, the bone effect, irradiation — which is the vocabulary that separates people who draw letters from people who arrange them.

**Pros:**
- Real craft knowledge encoded: geometric construction and optical correction are the two things diffusion models cannot reason about, and the skill makes them explicit steps rather than hoped-for outcomes.
- The competitor shelf test forces category awareness — you can't ship a mark that reads as a knockoff if you've had to place it next to the six marks already in the room. The reference library is classified for exactly this purpose, and explicitly framed as "study construction, map conventions, avoid look-alikes — never to copy."
- Full delivery discipline: concept overview sheets, client presentation boards with industry mockups, PNG renders, and a complete favicon / app-icon / web-manifest export set. That last one is a chore nobody does properly.
- Tested and maintained: CI workflow, five releases, evals directory, MIT licensed with a separate TRADEMARKS.md that correctly notes the bundled logo files are not covered by the license.

**Cons:**
- It makes logos by writing SVG code, which means the output quality collapses to the model's ability to reason about Bézier curves in text. Expect competent geometry, occasional beautiful accidents, and frequent "close but the spacing is wrong" — you will correct by hand.
- The 1,400-logo library skews toward tech/startup marks. Hospital-department and academic-institution conventions (seals, lockups, co-branding with a health system) are thin, and those are our actual category.
- Enormous surface area for one skill: 40,000+ characters of README, ~1,200 brands, tools, templates, evals. In practice you'll use maybe 20% of it, and the bulk makes it harder to audit before installing.
- Self-directed: nothing forces an actual client brief, so unattended it will happily invent a fictional brand. The value is entirely in what you put in front of it.
- Skills run with your coding agent's permissions — a real supply-chain consideration for anything touching the department's real brand files.

**Should we...**
- ✅ **Adopt it**
**Why:** Not because we need AI to design a logo — we don't, and the Montefiore mark is not up for redesign. Because it is the first skill I've seen in this category that encodes the *testing* rather than the *generating*, and testing is what our creative work never gets to do. The 16px pixel test alone would have caught most of the generated marks I've seen shipped this year. Concrete use here: run the existing Urology Unified Platform interface icons through the one-colour, reversed and 16px tests as a QA pass (SVG in, audit out, no model needed for that step); use the competitor-shelf framing when we next commission anything that has to sit beside other health-system marks; and use the concept-overview-then-checkpoint rhythm as the template for how any generative exploration gets presented to Shareef — one overview image with a recommendation, not a folder of forty. That is a governance change as much as a design one.

---

### Desk Studio
**Link:** https://github.com/adityareddy-dev/deskstudio
**Type:** Workflow
**What it is:** A set of role-based "desks" that run inside the coding agent you already use — three roughs generated on Sonnet, the art-director pick on Opus, polish on Haiku, a proof step with no model at all, then the sign-off. Installs as a Claude Code plugin or via `npx deskstudio add` for Codex, Cursor, Gemini CLI, Copilot, Windsurf and OpenCode. Files land in `.desk/out/<job>/` with a note on who did what, the scores and the cost. Runs locally; only model calls leave the machine. Created October 20, actively pushed October 24.
**What's good about it:** The division of labour is right. Cheap model for volume, expensive model for judgement, cheapest model for polish, and a **model-free proof gate** that can actually fail the job. Most agent design pipelines use one model for everything and then congratulate themselves. Splitting "generate three, pick one" into two different models with different appetites is a real editorial structure — it's how a studio works. The proof step having no model in it is the most interesting decision: some checks should not be a matter of opinion.

**Pros:**
- The role model is legible and auditable — the run note records who did what, the score, and the cost per job, which is the difference between a pipeline you can bill against and a magic box.
- Local-first with a 127.0.0.1-only dashboard and an event log that records names, numbers and paths but never prompt text. For anything touching clinical or patient-adjacent material, that's the right default.
- Agent-agnostic installation with a marked block in the instruction file that preserves your own text outside the markers and doesn't clobber edited desk briefs unless forced.
- It has actually shipped work: 17 signed-off pieces across four fictional brands plus one real site whose brand it derived from the project, with published scores and costs.

**Cons:**
- **The scores come from the studio's own model reviewers** — the README says so plainly ("they are not independent benchmarks"). An eight-axis average graded by the same system that made the work is a self-assessment, and a self-assessment is not a gate.
- The runner only takes `design` — social cards, for now. Everything else in the gallery is Claude Code skills, not the pipeline. So the impressive breadth is a shop window, not a product.
- Cost is real: $11.60 for one brand kit at list price. For a department doing unpaid internal marketing, that's an awkward number to defend, and the cheaper models in the chain may not hold up.
- Four made-up brands and one site is a thin evidence base, and 41 stars in four days means no one has stress-tested it against a hostile brief.
- Adds a whole `.desk/` directory, instruction-file blocks and a plugin surface to the agent stack. The maintenance cost of that on top of everything else we run is not nothing.

**Should we...**
- 👀 **Watch it**
**Why:** The architecture is the thing worth stealing even if the package isn't ready: three roughs, a separate judgement pass, a mechanical proof gate, an auditable cost. We can adopt that rhythm today by hand — for any generative exploration, produce three genuinely different directions, run an explicit selection pass against the never-do list, then a proof pass that checks the mechanical things (contrast, grid, 16px legibility, colour values) with no model involved. Where the tool itself would fit if it matures: the marketing/social creative for the residency program is repetitive, template-shaped, and currently hand-built — exactly what a `design` runner is for. But not while the only quality signal is a model grading its own homework.

---

### chromary
**Link:** https://github.com/izynu/chromary
**Type:** Tool
**What it is:** A colour-engineering toolkit for humans and agents: 16 deep-dive guides (OKLCH/OKLab and perceptual colour spaces, WCAG/APCA contrast math, design-system scales, colormaps, CSS gradients, print and physical standards), six installable agent skills (`palette-generator`, `contrast-auditor`, `theme-builder`, `dataviz-colormaps`, `gradient-smith`, `image-palette`), a working MCP server, nine tested recipes, and a zero-dependency playground. MIT, created October 21.
**What's good about it:** It treats colour as a specification problem rather than a vibe. Perceptual scales in OKLCH, Tailwind-grade and Radix 12-step and Material 3 HCT systems side by side, APCA/WCAG 3 contrast with auto-fix strategies, and — the detail that suggests someone who has actually shipped — a guide to gradients that never go gray, via perceptual interpolation in OKLab. The "gray dead zone" is not a thing you learn from a Canva tutorial. The organising principle is also right: agents shouldn't memorise hex codes, they should *compute* them. That's the difference between an agent that picks a colour and an agent that derives one and can defend it.

**Pros:**
- Contrast is handled as math with an auditor skill, not as a guess. For anything clinical or patient-facing, an automated APCA/WCAG pass is not a nicety — it's the difference between shipped and not shipped.
- Nine copy-paste recipes with claimed testing (a Tailwind-grade OKLCH scale in ~10 lines using culori), plus a zero-dependency playground — so you can verify before you adopt.
- Genuinely useful reference material: print and physical standards (Pantone/RAL matching), data-viz colormap guidance including when *not* to reach for a rainbow map, and a vocabulary glossary.
- Correct layer of abstraction: skills in the open SKILL.md format plus an MCP server, so it plugs into the agent stack without inventing a new runtime.

**Cons:**
- It's mostly a *reading list*. 16 guides, 200+ hand-picked resources — the actual tooling is six skills and a starter MCP server, and the repo has two stars and no releases. Right now it's a well-organised bibliography with a shop attached.
- Six skills is the whole toolkit, and the ones that matter most (`brand-auditor`, `token-linter`, `print-matcher`, `cvd-simulator`) are all on the v1.1 roadmap, not shipped.
- Colour alone doesn't fix slop. A palette can be perfectly OKLCH-correct and the layout still look generated — the failure mode is almost never the hex values, it's the hierarchy, spacing and type.
- No Figma plugin, no design-tool integration at all. It runs in code and in agents, which means it helps the Hermes side of our work and not the design side.
- Written by one person with an unmistakable "most complete on GitHub" banner energy — the confidence runs ahead of the two-star evidence.

**Should we...**
- 👀 **Watch it**
**Why:** The problem it addresses is real and permanent: the Unified Platform's single-accent discipline and the light marketing palette both break the moment a generated asset arrives with its own idea of navy. A token linter and a brand auditor that compute contrast and catch off-palette drift would be genuinely useful governance. But the pieces worth having are all roadmap, and today it's an excellent reading list — read guide 03 (perceptual colour spaces) and 04 (accessibility), lift the OKLCH scale recipe, and skip the rest until v1.1 ships. Do not confuse a well-sourced bibliography for a working gate.

---

## Slop Radar
- **Ripple/caustic gradients are now a brand-vocabulary cliché in waiting.** Apple's mineral-oil system will be copied without the experiment that generated it — frosted-glass blobs, light caustics, "sound wave" curves pasted over nothing. Steal the constraint, never the texture.
- **Vector output will be sold as quality.** Native SVG says nothing about drawing quality. A traced garbage mark and a generated garbage mark are both garbage; one just scales. Judge the path logic, not the format.
- **Self-graded pipelines.** Tools whose eight-axis "quality score" comes from their own model reviewers are being presented as gates. A model assessing its own output is a mirror, not a review. Watch for this framing everywhere in agent tooling.
- **"1,400 references" as a proxy for taste.** Reference libraries are becoming the headline feature of design skills. Volume of lookalikes is not craft knowledge; the tests and optical corrections are what matters. Read the test list, not the logo count.
- **Sponsorship-shaped frameworks.** A method can be sound and its tooling still be a funnel. Check the disclosure line before adopting any workflow built around one vendor's app.

## Overall Assessment
The interesting movement this week is not in generation — it's in **verification and constraint**. Every strong find shares one property: it makes something falsifiable. A grid overlay that proves the layout snaps. A 16px pixel test that fails a mark. Physically derived imagery that could only exist because someone ran the experiment. Contrast math an agent has to compute rather than guess. Meanwhile the biggest tool news of the week, a first mainstream vector model, is interesting precisely because it produces a *file you can inspect* rather than a picture you have to trust. That is the real direction of travel: away from "make me something beautiful" and toward "prove this is correct." For Shareef, the highest-leverage move this week is small and structural — write the two governance artefacts the Generative Branding framework implies but does not hand you: a one-page never-do list for generated creative (no gradient chrome, no fabricated clinical imagery, no new look to signal newness), and a fixed selection gate (three roughs, a written pick, a model-free proof pass, a grid and 16px check before anything is shown to anyone). Then run one real residency poster through the Swiss grid tool, end to end, and bring the artwork *and* the grid diagram to the next review. One artefact that proves its own structure is worth more than forty that don't.
