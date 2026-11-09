# AI Design Intel — November 8, 2026

Sources scanned: X (`site:x.com` returned ten results across three phrasings; I decoded every status ID against the snowflake epoch and the newest real post was **26 October** — the rest ran back to February, and the live-reading hits were recycled Claude Design and "AI design taste" threads. **No X item is judged today.**) Reddit (**JSON blocked on all six subs** — `graphic_design`, `web_design`, `UI_Design`, `midjourney`, `StableDiffusion`, `FigmaDesign` each returned the identical 190,240-byte HTML challenge page, one attempt each as expected from a datacenter IP; fell back to `site:reddit.com/r/graphic_design`, which surfaced ten real practitioner threads on AI slop and client submissions, **none with a verifiable date inside the window**, so the pattern is noted in Slop Radar and no Reddit item is judged). HN (`hnrss.org/newest` answered on all four queries — `AI design`, `generative design`, `typography`, `design tool` — and the Algolia `search_by_date` API over ~40 days returned 60 stories above 15 points; the only in-window design items were Grafista's anti-chat essay, already-covered territory, and a 36-point industrial-design history post). GitHub (search API, `created:>2026-11-01`, six queries — `ai design` 15,033 hits, `typography` 320, `image-generation` 548, `figma` 721, `generative-art` 142; the `topic:design-tools` query errored and was not retried). Google News (nine RSS queries, five with `when:7d`). Design press, where the craft was: Creative Boom (14), Design Week (19), Creative Review (12), PRINT (14), Dezeen (14); **It's Nice That's feed returned a JS shell rather than XML and Brand New's feed is 404-plus-login**, so neither is represented. Candidates considered: 47. Passed the bar: 6.

Previously covered and deliberately not re-judged: **Canva's refound and layoffs** (5 Nov — the 1,271-person cut, 22% of staff, six months' severance; the Fast Company analysis this week adds no new facts to the decision), **Grafista** (19 Oct tool, 30 Oct fingerprint test — the 6 Nov "skips the prompt" essay restates the Blueprints argument we already judged), **the AI flyer font / Comic Sans comparison** (5 and 7 Nov), **Munch "Connect the Lines"**, **Sixth Tone on Chinese typography**, **Design Week's "maxxing"**, **Nubank × Koto**, **Studio Cronica**, **Carling**, **impeccable**, **kubai-icons**. **GPT Image 2.6** appeared on 7 November only as the suffix of a star-farmed repo family; the release itself is judged here for the first time. Pulled after date verification: **New Yorker, "The A.I.-Design Aesthetic That's Taking Over the Internet"** (24 June — the best piece written on Claude Design's house style, and five months out of window), **Fast Company on AI and brand typography** (May), **Monotype × Kittl** (August), **Rubrik × Redscout** (the "Keep Going" campaign went live 17 August; this week's MediaPost item is a trade round-up re-report), **O'Reilly, "The Design System as the Control Plane"** (25 August), **Atlassian's design-system CLI** (September), **tldraw's hover-area study** (7 April), **Purple Garden / Mother Design** (launch 28 October; Creative Review's write-up on 3 November is a second pass, not a new artefact).

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| OpenAI Images 2.6 | Tool | ✅ Adopt it | Markup-guided editing in the API is the first mechanism that lets you art-direct an edit instead of re-rolling the dice — and SVG export finally lands output in a format the pipeline can use |
| Figma agent — vector illustrations and icons | Tool | ✅ Adopt it | Strokes, not fills, plus attachable style references: generation that produces an editable object with a weight property instead of a picture of one |
| The IMPACT framework — six constraint blocks | Technique | ✅ Adopt it | Turns "premium" into numbers — 3:1 hierarchy, 10% margins, 60/30/10 with roles — and its translation table is the best one page written on brief language this year |
| Prada, "Drawing Prada: Animated By Hand" | Idea | 👀 Watch it | The market has started auditing provenance; "not made by AI" is now a premium claim, and the only honest way to make it is a mark a model cannot produce |
| Tatiana Egoshina — "things you simply cannot Google" | Idea | 👀 Watch it | The clearest counter-programme to prompt-driven design: source material no model has seen, then generation only for composition |
| Affinity for iPad | Tool | ❌ Skip it | Correct architecture — one file, four disciplines — aimed at a platform our pipeline does not run on, with the model gated behind a consumer subscription |

---

### OpenAI Images 2.6
**Link:** https://openai.com/index/introducing-images-2-6/ · published **4 November 2026** · API models `gpt-image-2.6-flare`, `gpt-image-2.6-sunburst`; live in ChatGPT, Codex and the API
**Type:** Tool
**What it is:** OpenAI's image-model refresh, shipped as two API variants with a speed/quality split: **Flare** trades detail for latency (six seconds at low quality), **Sunburst** holds detail and — the claim that matters — character, product and brand consistency across repeated edits. Three real capabilities sit underneath the speed story: **image markup** comes to the API (a transparent comment layer marks the only region an edit may touch), **SVG export**, and a new **complexity parameter** that separates how much the model plans from how much fidelity it renders.

**What's good about it:** The markup layer is the most designer-shaped feature OpenAI has shipped. Asking for a change used to mean re-describing the whole image and hoping the model preserved the rest; now you draw on a transparent overlay and the edit is confined to what you marked — the same gesture as redlining a comp, and the same guarantee. The complexity parameter is a correct separation of concerns that almost nobody else exposes: a quick crop-and-clean should not re-reason the entire scene, and a multi-element brand composition should. And consistency across edit rounds is the property that turns an image model from a poster machine into something that can hold a campaign together across ten assets — a resident's face, a scrub colour, a department's navy staying put while the layout changes around them. SVG export, GIF output and C2PA credentials on generated files (confirmed by an independent test this week) also mean the output lands in formats the rest of the pipeline already speaks.

**Pros:**
- Markup-guided editing is *local* and reviewable. That is the difference between directing and gambling, and it is the first mechanism here that maps onto how a designer actually gives notes.
- Complexity as a dial, not a mystery. Fast iteration and careful composition become two settings rather than two tools.
- Brand and product consistency across edits is the single most requested property for institutional work — one department, one look, forty assets.
- GIF and SVG output plus content credentials remove two of the three friction points between generation and publishing (the third is type, below).

**Cons:**
- **SVG export is almost certainly vectorisation, not authorship.** Expect thousands of nodes, no named layers and no type objects — a traced picture, not a Figma file. Nobody has published a real test yet, and "ready for print" is doing a lot of work in that sentence.
- **"Flare also improves layout quality for posters" is the vendor shipping the category we banned.** A model composing a poster means a model setting lettering, and lettering without metrics is a likeness of type. Better poster layout is not the same as typesetting.
- Text rendering improved; type logic did not. No optical sizes, no kerning, no tabular figures, no hierarchy roles — the Sixth Tone diagnosis still applies in full.
- GIF timing, frame count and resolution are undocumented in the launch material, so its use is social-only until proven otherwise, and file weight rules it out of email and print.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** Nothing here changes the Unified Platform or the Chapter Player — both are hand-built and stay that way. It changes residency and Sub-I creative, because markup editing converts our one good rule ("generate the image with no text, set every word afterwards") from a prohibition into a workflow: generate the plate, mark the exact region that is wrong, change only that, export, then set Inter on top in the real layout. Run it on one real deliverable before believing the rest — a Sub-I welcome cover: plate with no letters, one markup pass to fix the light, SVG export, type set in the platform's own scale. If the SVG comes back as a usable object tree it becomes a genuine asset; if it comes back as a trace, we have lost an hour and learned to ignore one line of a launch page. The other thing worth taking is the complexity dial as a discipline: low complexity for everything routine, and planning tokens spent only where there is a composition to plan. What none of this fixes is taste — every capability above makes it cheaper to produce the same average image faster, and the constraint list is still the only thing standing between us and that.

---

### Figma agent — agent-generated vector illustrations and icons
**Link:** https://www.figma.com/release-notes/?title=improvements-agent-generated-vector · shipped **5 November 2026** · help: https://help.figma.com/hc/en-us/articles/38031452710807-Convert-static-images-to-vector-layers
**Type:** Tool
**What it is:** An update to Figma's in-canvas agent: it now generates vector illustrations and icons that arrive as editable objects — independent layers grouped by function, line work built on **strokes rather than fills**, style references you can attach so a set is generated *from* your existing artwork, and clean enough structure that Figma Motion can animate it without retracing.

**What's good about it:** The stroke-versus-fill decision is the tell that somebody who draws was in the room. Fill-based line art is a dead object: you cannot change weight, caps or joins, and "make the lines thicker" means regenerate the picture. Stroke-based line art has a property you can edit, which is what a vector *is*. Attaching references is the second correct decision, because it turns generation into a system move — one approved sheet becomes the grammar, and everything after it is an extension of that grammar rather than a new opinion. Functional layer grouping is the third: independent, sensibly named layers mean the output can be art-directed after it exists, which is the only kind of generated asset worth having. For a platform whose icon set is one of the few places a clinical UI shows its hand, this is the first generation feature that does not force us to abandon the system to use it.

**Pros:**
- Strokes, not fills — weight and caps stay editable, so a generated icon can be corrected to the grid instead of redrawn.
- Style references let one approved set define the next twenty. That is controlled, repeatable generation, which is the whole premium criterion.
- Layer structure survives into Figma Motion, so the same object can animate without a second pipeline.
- It lives in the canvas where the design system already is, not in a separate web app with an export step.

**Cons:**
- Icons are where AI slop hides best: the rounded-square container, the uniform 2px stroke, the generic glyph that means nothing. Generating at scale reliably produces forty icons that are 80% consistent, and the 20% is exactly what a design director sees in one glance.
- No documented grid or optical constraints — nothing enforces a 24px keyline, a matched stroke weight or consistent terminal treatment across a set.
- The output inherits Figma's defaults and the model's averages, not your icon grammar, unless you have already written the grammar down somewhere it can read.
- "On-brand icons at scale" is also the mechanism by which a system becomes wallpaper. Volume is not the goal; a consistent set is.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** The Unified Platform runs on SVG icons and a single accent, and its icon set is small enough that inconsistency is visible immediately — which is precisely why generation has been the wrong tool until now. The correct sequence is the reverse of how most people will use this: hand-draw six anchors covering the shapes the platform actually needs (person, calendar, alert, document, clock, chevron), approve them, then attach that set as the reference and generate only the extensions — the long tail of specialist glyphs nobody wants to draw by hand. That is a system with a director, not a slot machine with a brand prompt. The test before anything ships is one screenshot at 100% on the 24px grid, because the failure mode here is not ugliness, it is drift: a set that is 90% right reads as amateur from across the room, and no amount of generation hides the four icons that are wrong.

---

### The IMPACT framework — six constraint blocks for design prompts
**Link:** https://hackernoon.com/the-impact-framework-six-rules-for-better-ai-generated-designs · published **5 November 2026** · James Shehan, 30+ years in design, author of *Prompt Like a Designer*
**Type:** Technique
**What it is:** A working method for turning a design brief into a generation spec, built on the claim that "clean", "modern", "premium" and "bold" are not instructions — they are the coordinates of the statistical middle. Six labelled blocks replace them: **I**mportance (explicit reading order plus a size ratio), **M**argins (a percentage of width, with tighter spacing inside groups than between them), **P**alette (three colours maximum, each given a role at roughly 60/30/10, only the accent saturated), **A**lignment (one rule, everything on one grid), **C**ontrast (one dominant element, dark-on-light or light-on-dark, never mid-on-mid), **T**ypography (two typefaces maximum). A seventh, unlabelled block is non-negotiable: four to eight named exclusions. It ships with a translation table, a system prompt, and a small Python/JS builder that throws if you specify more than three colours or two typefaces.

**What's good about it:** The diagnosis is the most useful sentence published on this subject all week: *"the model's resting state is 'add more'"* — gradients, glow, drop shadows, texture, stock people, full-saturation colour, each defensible alone and noise together — and restraint is never a default, it has to be asked for by name, every time. The translation table then does the work nobody else does: "premium / luxury" becomes *fewer elements, more whitespace, quieter colour* (with the aside that asking for luxury gets you gold gradients); "modern" becomes a named era instead of a mood; "make it pop" becomes "the only saturated element". Those substitutions are not prompt tricks, they are what a senior designer actually says in a crit, written down. And making the constraint set fail fast in code — three colours, two typefaces, raise an error — is the right instinct: a spec that cannot be violated is worth more than a guideline that can.

**Pros:**
- Converts adjectives into countable things. A 3:1 headline-to-subhead ratio and a 10% margin are checkable; "clean and modern" is not.
- The translation table is portable beyond generation — it is a brief-writing tool for a human designer, a copywriter or a vendor.
- Palette-with-roles (anchor/support/accent, only the accent saturated) is the same logic the platform already uses by policy, stated in a form a model can follow.
- The code builder enforces the constraints structurally rather than hoping the prompt survives contact with the model.

**Cons:**
- **It is aimed at letting a model compose whole layouts, type included — which contradicts the rule we adopted on 7 November.** Its typography block tells you to *describe the character of the type* to an image model, and describing type to a model is exactly how you get lettering that resembles type. For images, our rule stands: no text at all.
- No published evidence. "Tested against vague prompts on the same model" with no sample size, no rubric, no blind comparison, on a platform where the author is selling a book about the method.
- Hex values are a weak steer to an image model, which the author half-admits — so the palette block is strongest for HTML/CSS output and weakest exactly where the piece spends its examples.
- The exclusion list it defaults to (no gradients, no glow, no texture, no stock people) is one house style presented as a universal clean-up, and applied to a brand that has chosen texture deliberately it produces confident, wrong corrections.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** Adopt the six blocks and the translation table, and use them where they are exact rather than where they are fashionable. The strongest use is not poster prompting at all — it is the brief that precedes any generation: write the reading order, the ratio, the three roles, the one alignment and the two typefaces *before* anything is generated, in a file, once per surface. For the Unified Platform that file already half-exists as a design system, so the work is writing the missing half — the reading order and the ratio rules for the command centre and the call-out log — in the same words a model or a new hire could follow. For residency and Sub-I creative, the translation table is the immediate win: every graphic brief from now gets "quieter colour, fewer elements, more whitespace, one accent" instead of "premium", and the exclusions get named aloud rather than hoped for. What it does not do is make the decision that matters. Constraints remove the noise; they cannot supply the one strong idea, and the piece says so itself in the paragraph most people will skip.

---

### Prada — "Drawing Prada: Animated By Hand"
**Link:** https://www.euronews.com/2026/11/02/prada-champions-the-human-touch-and-not-ai-slop-for-their-new-christmas-campaign · published **2 November 2026** · campaign creative direction Miuccia Prada and Raf Simons; campaign creative direction Ferdinando Verderi; photography Glen Luchford; animation led by John Pomeroy
**Type:** Idea
**What it is:** Prada's Christmas campaign pairs live-action photography with hand-drawn animation — every frame drawn by a team led by John Pomeroy, the Disney and Don Bluth veteran whose credits run from *Winnie the Pooh and Tigger Too* to *The Land Before Time*. It arrived into a market where Coca-Cola has been criticised two years running for AI-generated Christmas ads, and it was received, explicitly, as the antidote.

**What's good about it:** The supply chain is the message, and Prada made the supply chain legible: a named animator, a named photographer, a named team, a behind-the-scenes film in which Pomeroy says he learned "with pencil and paper, through traditional, analogue drawing". That is a claim a viewer can audit, which is more than most brand craft claims offer. The reception is the evidence worth reading — "Love it when ads go AI free", "such a breath of fresh air seeing something with soul again" — because it establishes a market fact rather than an aesthetic preference: **provenance has become a purchase signal**. And the underlying craft argument is sound. Hand-drawn animation has a texture that is not a filter: line boil, imperfect registration, a hand that varies across frames. Those artefacts are the proof of labour, and labour is the thing a generated image cannot counterfeit at scale.

**Pros:**
- A named, checkable production chain — the opposite of a brand saying "craft" and showing a filter.
- The audience response is quotation-grade evidence that "not AI" now reads as premium in a category the public already associates with AI cheapness.
- Pomeroy's own framing is the transferable line: there is "a very distinct and purposeful reason to do hand-drawn animation… to see that there's value in it."
- It shows the difference between effort signalling that is real (a team, months, a technique) and effort signalling that is a costume.

**Cons:**
- Press-release shaped: one quote, no budget, no timeline, no measurement of whether it sold anything. The backlash framing is the journalist's, not data.
- Prada can hire a Disney veteran; a department with a content calendar and no budget cannot, and the article offers no scaled-down version of the idea.
- The logic is thinner than it looks — "hand-drawn means human" flatters a brand with a global supply chain, and hand-drawn-over-live-action is itself a well-worn look, not an invention.
- Nobody has shown that the AI-free claim survives contact with the rest of the campaign's production. Provenance claims are easy to make and rarely audited.

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Watch the market signal, adopt the cheap half of the method. What this campaign proves is not that AI is over — it is that audiences have started asking where an image came from, and that the fastest way to answer honestly is a human artefact that could not have been generated: a real photograph of the actual room, a hand-lettered name, a scan of a real document, a signature. Shareef already owns the scarcest asset in this category — 28 faculty interview clips, real OR photography, real residents, a real building in the Bronx — and none of it is in any model's training set. The move this week is not to commission animation; it is to stop treating those assets as b-roll and start treating them as the provenance layer under every AI-assisted piece: real faces and real places photographed, generated material confined to light, crop, extension and cleanup. Then, when the residency campaign says "our people", it is making a claim that can be audited — which is the only kind of premium claim that survives being checked.

---

### Tatiana Egoshina — "things you simply cannot Google"
**Link:** https://www.creativeboom.com/inspiration/tatiana-egoshina-finds-beauty-in-bad-typography-italian-folklore-and-happy-accidents/ · published **5 November 2026**
**Type:** Idea
**What it is:** A profile of the Milan-based designer — Moscow training under Anna Kulachek, years at Strelka, identities for IndieLisboa, posters in black, white and one extra colour — anchored on a project made by spending a week at a table in Castelmezzano, a village of a few hundred people in the Dolomiti Lucane, collecting local legends from a hundred-year-old woman, then projecting the result onto the cliffs as a videomapping piece with sound artist Livia Borzetti.

**What's good about it:** The method is stated in six words and it is the entire argument: *"These are things you simply cannot Google."* A model's output is by definition an average of what it has already seen; the only material that escapes that average is material that has not been published, which means it has to be collected — at a table, in a village, from a person, over a week, with pasta. The craft discipline around it is equally usable: black, white and one extra colour, usually red, learned as a constraint rather than a palette; typography "refined to the millimetre"; colour understood as something felt in Palermo — sky, sea, fruit, fresco — rather than specified as a hex. And the work itself refuses the tell of AI-era design: the Strelka posters are loud, awkward, specific and unmistakably drawn by a person with opinions, which is precisely the quality that no amount of style reference reproduces.

**Pros:**
- Supplies the missing half of every anti-slop argument: it is not enough to specify better, you have to source better.
- The constraint habit — two neutrals and one colour — is a portable rule that produces distinctive work with cheap inputs.
- A named, real body of work to study for poster composition that is neither minimal-Swiss nor gradient-modern: Strelka, IndieLisboa, FABRICA.
- It treats local, unglamorous, un-Googleable material as the asset, which is exactly the position an in-house department with real people and a real place is in.

**Cons:**
- A profile, not a method paper: no process detail, no failures, and the "beauty in bad typography" premise in the headline is barely argued in the body.
- Almost all the work predates the AI question, so the connection to our problem is inference, not reportage — the article never mentions AI at all.
- The fieldwork model is expensive and does not scale to a monthly content calendar; a week in a village per campaign is not available to a department of one.
- Images are web crops with no CMYK, no stock, no print specs — useless as production reference, useful only as direction.

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Watch the practitioner, adopt the sourcing rule. The practical version for Shareef is a single question asked at the top of every project: *what is in this piece that no model has seen?* If the answer is nothing, the piece will look like everything else no matter which model made it — that is the mechanism behind every "AI look" complaint in this brief, and it is not fixed by better prompts. The department's answer is unusually strong: a Bronx hospital, named faculty, residents who are actual people, a programme with a history, and 28 interview clips nobody else has. Turn one of those into a source shoot each month — a real room, a real face, a real document, shot badly on a phone if that is what is available — and let generation do only what it is good at: extending, cleaning, composing around the real thing. The Egoshina constraint comes free with it: pick two neutrals and one accent, and refuse to add a fourth colour. That single rule does more for a residency flyer than any style reference.

---

### Affinity for iPad
**Link:** https://www.creativeboom.com/news/behold-affinity-for-ipad-the-app-that-wants-to-retire-your-four-other-apps/ · published **2 November 2026** · Design Week's take: https://www.designweek.co.uk/canvas-free-affinity-arrives-on-the-ipad/ · 3 November 2026
**Type:** Tool
**What it is:** Canva shipped Affinity for iPad as one application covering sketch, vector, photo and layout in a single `.af` file — no exporting between disciplines — free for individuals with a Canva account. The AI features sit behind Canva Premium: Generative Expand, upscaling, motion blur and noise reduction, and **Decompose Layer**, which splits a flat image into editable layers.

**What's good about it:** The file format is the actual design decision, and it is the correct one: one document that holds a sketch, its vector outcome, the photograph underneath and the page it sits on means the work stops being a relay race between four apps. Sketch Studio picking up Apple Pencil pressure and tilt, Sketch to Shapes converting hand-drawn forms into clean vectors, and a mask tool that follows a drawn edge are all craft-respecting features — they accelerate a hand, not replace it. Decompose Layer is the one AI feature in the release that serves craft rather than substituting for it: turning a flat image into editable layers is the difference between having a reference and having material. And the pricing is a strategic fact worth naming: professional creative tools are being driven to zero to feed a subscription model.

**Pros:**
- One file, four disciplines — the strongest argument against app-switching anyone has shipped this year.
- Free for individuals is a genuine change to what a solo designer or a small department can afford.
- Decompose Layer, Generative Expand and upscaling are exactly the right three AI features for print-adjacent work: they operate on existing material rather than inventing new material.
- Built for touch from scratch rather than shrunk from desktop, with a mask tool that follows a stroke.

**Cons:**
- **iPad-only.** No Windows, no Android, no browser. Shareef's pipeline is browser plus a Linux VPS, so nothing here is reachable today.
- The model is inside a consumer subscription: AI features need Canva Premium, which raises the licensing and data questions an institutional user has to ask before putting patient-adjacent or faculty material through it.
- Decompose Layer's real-world quality is unverified — flat images with complex lighting decompose into messy, half-useful layers, and no independent test exists yet.
- "Free" is a strategy, not a gift: Canva has just cut 22% of its workforce and taken a valuation writedown on AI costs. The pricing will move.

**Should we...**
- ❌ **Skip it** — slop-adjacent, hype, or redundant
**Why:** Skip it for anything on the critical path. It is a good release aimed at a platform we do not run, and recommending a workflow change onto hardware nobody in this pipeline owns would be exactly the kind of enthusiasm that wastes a week. The reason to keep the tab open is one feature and one principle. The feature is Decompose Layer: if a Mac or iPad ever lands on the desk, the first thing worth doing is running a flat AI-generated poster through it to see whether the resulting layers are usable — because that would convert a lot of reference material into editable material, and it is the only path from "I like this image" to "I can work with this image". The principle is architectural and applies immediately to our own tools: a single document that holds sketch, vector, photo and layout beats four files that have to be reconciled, and the Chapter Player and the platform's asset flow should be judged against that standard whenever the next build happens.

---

## Slop Radar

- **"Better poster layouts" is now a model feature, not a warning.** OpenAI shipping improved layout quality for posters and professional visuals is the vendor legitimising exactly the output we banned: a model composing a page means a model drawing lettering that merely resembles type. Expect the café-wall AI flyer to move into brand decks over the next quarter, wearing a better layout.
- **Process as proof.** Séance-led rebrands, chakra-reading creative development, "we spent a week with a hundred-year-old woman" — the method has become the press release. It can be genuine and it can be theatre; the tell is whether the artefact is stronger for it, and the only way to judge is to ask to see what shipped, not how it was conceived.
- **Free professional tools are a funnel.** Affinity free, AI behind a paid tier; Canva cutting a fifth of its staff while giving the craft app away. When a pro tool costs nothing, the model inside it is the product — check where the AI sits and under which licence before standardising on it.
- **The "no AI" badge is about to be worn by everyone.** Prada earned real goodwill by naming its animators. Within a month there will be brands claiming the same with an AI filter and a hand-drawn typeface. Provenance claims need receipts: a named person, a real photograph, a document that exists.

## Overall Assessment

The tool layer finally caught up with the thing we have been asking for since this brief started: control. In one week, markup-guided editing arrived in an API, stroke-based vectors arrived in Figma with attachable style references, and SVG and GIF became output formats rather than exports you fight for. That shifts the bottleneck decisively away from the instrument and onto the two things no vendor can ship: the **spec** and the **source**. Which is why the highest-leverage move this week is not a new tool — it is writing the spec down once. Take the IMPACT blocks, fill them with the platform's real values (the navy, the Inter scale, the three colour roles, the one accent), and make that block the opening context for every generation and every hand-off, so that "premium" is never typed again. Then run the Egoshina test on each brief before anything is made: what is in this piece that no model has seen? If the answer is nothing, the fix is not a better prompt, it is a photograph of the actual room.
