# AI Design Intel — November 20, 2026

Sources scanned: X (**no usable index today** — four `site:x.com` phrasings returned profile pages and undated threads; the status IDs that did surface decoded to February–October 2026, all out of window. No X item judged. X-adjacent material arrived instead through Google News coverage of design threads, per the fallback). Reddit (**JSON API blocked on all six subs, seventh consecutive day** — `graphic_design`, `web_design`, `UI_Design`, `midjourney`, `StableDiffusion`, `FigmaDesign` each returned the same 190KB challenge page to one polite request with a browser UA. `web_search` fallback surfaced r/canva and r/technology threads that were reachable only as links inside the Canva coverage; no thread judged on its own). HN (**Algolia `search_by_date` worked; `hnrss` avoided** — newest 40 `design` stories read, plus the `last30days` aggregator's 8 HN hits. In-window: The Myth of the One Shot, Langfuse's designer essay, Launch HN: Onlook, Show HN: Klistra, Show HN: Vemlora, Frostbite, Design for Understandability). GitHub (REST `ai design created:>2026-11-13` — **1,872 results, top 12 read** — plus six topic searches: `typography` 127, `figma` 115, `design-tools` 88, `generative-art` 230, `image-generation` 310, `design-system` 340). Google News (four feeds, 146 items, ~20 in-window: `AI design tool` 66, `Figma when:7d` 27, `typography AI` 25, `designers AI craft` 28). Plus editorial index reads of Design Week, Creative Boom and Brand New. Candidates considered: 36 after date and duplicate filtering. Passed the bar: 7.

**Screened and dropped, with reasons:** *Nubank × Koto and in-house* (Brand New, 19 Nov, **Reviewed** — the week's biggest identity and I could not read it: paywalled past the images, so not judged on a headline, same rule as PHS last week); *J&J Dairy × M/OTG* and *TABB × M—N Associates* (Brand New, 18 and 17 Nov, both Reviewed, both behind the same wall); *Studio Kiln × Reset "Ester"* (Creative Boom, 16 Nov — a faceless block character that communicates only through motion, genuinely good, **already judged on 18 Nov**); *Turner Duckworth × Maker's Mark* (19 Nov — previously covered and dropped 18 Nov); *&Walsh × Insomnia Cookies* (19 Nov — indexed, not read in full); *shadcn-labs/goeist-font* (195★, a soft rounded Geist, created 11 Nov and pushed 16 Nov — nine days at creation, outside the window; noted for the file); *Langfuse, "Comfortable with being uncomfortable"* (19 Nov — the first designer at an engineering-first company, one real sentence: *"When building is cheap, intentional design is what makes a product feel substantial instead of shallow"* — but it is a careers post with a hiring link at the bottom); *"Design for Understandability"* (HN, 19 Nov — software architecture, not visual); *Frostbite* (HN, 20 Nov, 123 points — a CPU architecture designed by AI, which is a different discipline and a different brief); *Kling Image 4.0 vs Ideogram 4.5* (18–19 Nov — two model spec sheets with native 8K claims; judging that is reading marketing, and the poster problem is not resolution); *Figma MotionGraphicsBench* (14 Nov — a benchmark, not an artifact); *Figma 3D layer editing* (16 Nov — headline only, from one Korean design outlet, unverified); *AI Is Making "Good Enough" the Enemy of Great Design* (DesignRush, 17 Nov — URL 404s on fetch, so unread); *walking-block* (49★, a Soviet apartment block in three.js with no 3D assets — beautiful, no transferable method); *mona-lisa-js* (10★, 62,430 brush strokes in one file — charming, not actionable); *openpixel* (42★, 31 pixel experiments, a teaching set); *phasyn-studio* (99★, self-hosted AI filmmaking); *EggLab* (61★, local image gen for Windows); *html-ppt-generator* (153★, template farm); *canva-ai-content-studio* (93★) with *Adobe-InDesign-AI-Latest* (86★), *adobe-express-merveora* (63★), *Inventor-2026-Full* (83★), *Rhino-8-Full* (81★) and *SketchUp-Professional-Install* (78★) — six repos whose entire content is a product name in the title, star-farmed into the `design-tools` and `typography` topic feeds; nothing to read inside any of them; and previously covered and deliberately not re-judged: craft, Duoasa, editorial-taste, suzhe-ui, material-expressive-skill, SalkarsaUI, punchcutter, fontroom, inrond, resocket-pixeljury, logo-design-skill, lemo-animi, gpucanvas, artboards, Underlay, Ester, Alpha Bank, BrandOpus × Hg, Mercury Builder Mode, nakkash, PosterProof, ui-design-minimal, ui-design-minimal's audit.

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| Alex Van de Sande — "The myth of the One Shot" | Idea / Technique | ✅ Adopt it | He got the one-shot result in four hours, called it amazing, and refused to ship it because it wasn't his — then logged the 75 hours that were |
| Lifehacker — the hidden design brief inside every AI poster | Technique | ✅ Adopt it | The purple is a decision made in a sub-prompt you never see; you can make the model print the brief and edit it before anything renders |
| Canva AI Controls | Idea / Tool | ✅ Adopt it | Canva drew the line at "generates something new" — and tied it to metadata that follows the file to social |
| Klistra | Tool | 👀 Watch it | "Designed, not generated" is the correct thesis for motion: real type, exact files, deterministic re-render — and 2 points on HN |
| Onlook 2.0 | Tool | 👀 Watch it | Design on your actual repo, in your own agent, with the folder left untouched — Mercury's Builder Mode, shipped as a product |
| Kern | Tool | 👀 Watch it | A free type playground whose real export is a shareable URL and a dampened clamp() scale — the maths is the takeaway |
| Vemlora | Tool | ❌ Skip it | Retyping a flattened poster produces type that is almost ours, which is worse than type that is obviously not |

---

### Alex Van de Sande — "The myth of the One Shot"
**Link:** https://blog.vandesande.design/every-one-shot-is-slop · published **20 November 2026** · the project it defends: https://isometric.earth (live, verified 200)
**Type:** Idea / Technique (a process diary with an argument inside it)

**What it is:** A designer's account of building Isometric Earth — every isometric city map he could find, from Isometric NYC to tiny.london, placed on one continuous isometric planet rendered as pixel-art hexagonal prisms. He launched it, got three kinds of feedback ("this is cute", "my town is not right", "This AI slop and I hate it"), and wrote the post to answer the third. The answer is not a defence of AI. It is an argument about **what effort looks like when the tool makes effort cheap**: *"slop is anything that is low effort, often mass fabricated… when a tool makes something easy, then that simply becomes the standard of low effort."* His precedent chain is the whole thesis: hand-writing HTML in the late nineties, then blogs, then WordPress — *"a basic wordpress template, much like a word document using Calibri, or a default presentation in Keynote, becomes the hallmark of low effort content."* Each tool lowered the floor, so the floor moved up.

**What's good about it:** The middle third, which is a genuine production log and the reason this is the week's best item. He tried the one-shot on purpose. He gave Fable 5.2 the brief — *"Go crazy, play around, try anything. What about I give you 12 full hours?"* — left it looping, came back four hours later, and got something that by his own description *"was amazing: it had regenerated the whole world in these 3d prisms, with a tilt shift effect, animation, railroads, city labels a search. Just a few years ago I would need a full team to build that over months."* And then: *"I could have stopped there and released it. But it still didn't feel right. It didn't feel… **mine**."* Everything after that sentence is craft — pixel splats (3D point clouds rather than polygons) so the pixel art has real internal structure; a mountain that stops looking like *"a forest of spires"*; changing the whole hex grid from 1:7 to 1:4 because √7 steps cannot land on integer pixels and 2× can; and the tile law, stated in eight words that matter more than the rest of the post: *"image generated images… might look nice in isolation but used as a tile, they're often inconsistent."*

**Pros:**
- **It separates effort from tool use, with a number attached.** 39,000+ words dictated and typed in two weeks, 30,000 tiles he never painted, 75+ hours. That is a defence of AI assistance that a sceptic cannot dismiss as hype, because the sceptic's own metric — hours — is the evidence.
- **The one-shot refusal is the most useful thing in the piece.** He had a shippable, impressive, four-hour artifact and withheld it because it wasn't his. That is a taste decision made *after* the tool succeeded, which is precisely the faculty this brief keeps saying is the job.
- **The tile-consistency law is directly transferable to us.** Any generated image used as a *component* — a card background, an icon set, a series of 12 social frames — fails not because each image is bad but because they are inconsistent with each other. That is a design-system problem, not an image problem, and he names it from experience.
- The shadow bug is the best small anecdote in any design post this month: Claude generated three tiles per lighting setting, and when a cloud *and* an aeroplane cast shadows the two merged and darkened the same pixels twice — *"which is not how shadows are supposed to work."* The fix, three images per tile (base illustration, bitmap shadow mask, height layer), is a real compositing decision that a prompt cannot infer.
- **"When working with AI tools you need to continuously remind of rules you had already set long ago"** — said flatly, in passing, by someone 75 hours in. That is the whole maintenance cost of agentic design, in one line.

**Cons:**
- **It is one designer, one project, one taste.** The argument that "a project made with care takes many long hours" is true of his project; it is not evidence about anyone else's, and the post never tests the claim against the one-shot map he actually got.
- **He never shows the rejected four-hour version.** A side-by-side of the one-shot render and the shipped one is the single image that would settle the argument, and it is absent. We are asked to trust the taste call rather than see it.
- The chronology is hard to follow — 2023 Gosper-hexagon experiments, a 2024 Bridges paper, a 2026 Codex rewrite, then a second project layered on top — and the post assumes you know the earlier work.
- **The definition of slop is doing a lot of work and can be read uncharitably:** "low effort, often mass fabricated" makes effort the test, and effort is not quality. He concedes this in a parenthesis (*"you can spend an afternoon in the kitchen and still make unedible dinner"*) and then proceeds as if he hadn't.
- No licence, no repo, no statement of how much of the final site is hand-authored versus generated — which matters if anyone is meant to learn the pipeline rather than admire it.

**Should we...**
- ✅ **Adopt it** — the tile law and the "not mine" test, both this week.
**Why:** The residency programme's biggest unexamined risk is series work: twelve social frames from the same campaign, six Grand Rounds cards a season, a set of Sub-I welcome pages. Every one of those is a *tile set*, and Van de Sande names the exact failure — each frame looks good alone and the set looks assembled, because a model has no memory of the frame before it. The fix costs nothing and is the most useful thing in today's brief: generate **one** master element and derive the set from it by rule (same crop logic, same type position, same colour order), rather than generating twelve siblings. The second thing to take is the refusal. His four-hour result was better than most of what we ship and he still didn't release it, and the reason — *it didn't feel mine* — is the only quality gate that has ever worked. Applied to the Unified Platform: when a generated screen looks right and you cannot say why, that is the four-hour version, and the honest move is to keep going rather than ship. It is also the argument to hand anyone in the health system who says AI makes design easy: the tool removed the vector labour, and the 75 hours were the part that made it a place.

---

### Lifehacker — the hidden design brief inside every AI poster
**Link:** https://au.lifehacker.com/ai/120155/why-do-ai-posters-all-look-like-that · published **17 November 2026** · Lifehacker (also syndicated via Yahoo Tech)
**Type:** Technique (an explanation that hands you a control)

**What it is:** A reported explanation of why AI posters converge on one look — uncanny figures, buildings that are subtly wrong, and always that one brush-stroke font. The mechanism is not the image model. It is the **thinking model**: before rendering, the chat model writes a set of sub-prompts, and in the poster case one of them is effectively *"create a design brief for a poster."* That invisible brief is where the aesthetic decisions are made. The author forced ChatGPT to print its own briefs and found the same vocabulary every time: nightclub posters specified *"electric purple," "electric yellow," "electric pink"*; the concept was always *"high-energy"* and *"futuristic"*; imagery was always the *"silhouette"* of a DJ or a dancing crowd; all type had to be *"bold"* and *"futuristic."* In one test the model even rendered the explanation of the brief into the bottom half of the poster.

**What's good about it:** The font theory, which is the most specific piece of slop forensics I have read. *"Brush lettering"* is a design term meaning handwritten-looking lettering; the model takes it literally and asks the image generator for letters made by an actual paint brush — which is why every AI poster has the same brush-script display type. And then the detail that proves the mechanism: **the letters are not a font at all.** Identical letters come out with slight variations, because the renderer is a diffusion model and cannot set a vector glyph. So the "font choice" everyone is imitating is not a choice, it is a misreading compounded by a medium that cannot set type. Second good thing: the honesty about the boundary — *"even that could be different from what was actually sent to the image generator"* — the brief you can see may not be the brief that ran. Third: it names the other house styles in passing, including the one we live next door to — Claude-built sites with *"tiny text, buttons with rounded corners, and tile-based layouts."*

**Pros:**
- **It converts a vibe into a two-stage pipeline with a review gate.** Ask for the brief, read it, correct it, then render. One extra turn, and you have replaced a slot machine with a decision you can see and edit.
- The specific tells are immediately usable as a checklist: "electric" anything, "futuristic", "high-energy", silhouettes, "bold" as the only type instruction, brush script.
- It explains *why* adding detail helps without mystifying it: the model fills gaps with the statistically obvious answer, so the gap is the problem, not the model's taste.
- It distinguishes per-model house styles rather than treating "AI" as one aesthetic, which is the correct level of analysis for tool selection.
- No product, no affiliate angle, no vendor quote — a reporter testing a claim and showing the working.

**Cons:**
- **Everything here is ChatGPT, one author, one afternoon, no counts.** The claim that nightclub prompts *"almost invariably"* produced electric purple is the strongest evidence offered and it is unquantified.
- The causal chain has a hole the article admits: the displayed "brief" may be a post-hoc rationalisation, not the text that was sent. If so, editing the brief might not change the render — and there is no test of that here.
- It stops at diagnosis. There is no worked example of a corrected brief producing a better poster, which would have doubled the value in one image.
- The brush-font theory is marked as speculative by the author, correctly, and then reads as settled by the end of the section.
- It is about posters specifically, and the leap to "any AI-generated content" is asserted rather than shown.

**Should we...**
- ✅ **Adopt it** — make the brief a deliverable, starting with the next poster.
**Why:** This is the cheapest quality upgrade available to the marketing programme and it requires no new tool. Every AI-assisted flyer, poster, social card and Sub-I cover we make currently runs prompt → image → judgement, which means the design thinking happens somewhere we cannot see and cannot correct. The fix is one instruction: *"write the design brief first, in full, and stop."* Then we read it the way we would read a junior's rationale — what is the concept, what is the type, what are the colours, what is the image, what is the hierarchy — and we change the things that are obviously borrowed. For Montefiore that means the brief has to start from our facts, not the category's: navy, Inter, a real photograph of a real faculty member, a date and a room number that are correct. The electric-purple problem is not that purple is bad; it is that purple was chosen before anyone knew what the event was. And the tile-level tell he identifies — identical letters with slight variations — is the reason generated type should never appear at large scale in our work: a brush script that cannot repeat a letter is a signature that cannot be trusted.

---

### Canva AI Controls — the line is "generates something new"
**Link:** https://www.canva.com/newsroom/news/ai-controls-canva/ (announcement, **19 November 2026**) · coverage: https://www.theverge.com/ai-artificial-intelligence/1037126/canva-ai-features-off-button
**Type:** Idea / Tool (a platform publishing its own taxonomy)

**What it is:** Two controls, free and Pro, no extra cost. A **Generative AI Control** that hides Canva's generative features across the product — Magic Write, Magic Design, Magic Layers, Magic Edit, Magic Expand, Dream Lab, Canva Code, AI Shapes, and image generation inside the chatbot. And an **AI-Generated Content Control** that reduces AI-made templates and elements in library search and recommendations. Canva's stated reason: *"It's not our place to tell anyone how to create."* What makes it more than a settings toggle is the exception it carved out and explained.

**What's good about it:** The taxonomy, in one sentence from the announcement: *"we also have assistive editing tools that make everyday tasks faster without generating anything new."* Background Remover and Magic Grab stay on when generative AI is off, and the reason given is the one a design director would give — they *edit existing content* rather than author new content. Then the consequence, which is the part almost every coverage missed: *"Since these tools only edit existing content rather than generate anything new, using them won't trigger an AI-generated content label. This means Canva won't add metadata identifying your design as AI-generated, so social platforms that read this information won't label your work as AI-generated simply because you've used tools like Background Remover."* A platform has just published an operational definition of the assistive/generative line **and wired it into metadata that travels with the file to Instagram and X.** Second good thing: the honesty about the library — AI assets are tagged in metadata, and search can be told to prefer human work. Third: the scale disclosure, **38 billion uses** of its AI tools, which is what makes "we're adding an off switch" a strategic statement rather than a retreat.

**Pros:**
- **It gives us a rule we can put in a brand document:** retouch freely, generate deliberately. The test is not "was AI involved" but "did any pixel arrive from nowhere" — and that test is now enforceable in practice because the label follows the metadata.
- The metadata consequence is a real operational fact for a hospital's social channel: an unlabelled assistive edit and a labelled generated image are now different products, with different platform treatment.
- The AI-content control (prefer human-made templates) is the correct answer to a library drowning in generated assets, and it is a model any internal design library should copy.
- It concedes the obvious thing most platforms won't: *"we don't believe they should be the only way to bring your ideas to life."*
- Admin-level controls already existed for Business/Enterprise/Education, so this extends governance down to individuals rather than inventing it.

**Cons:**
- **It does not turn off everything,** and the exclusions are not principled in every case — the toggles are a product compromise as much as a philosophy.
- It is still an advertisement. The framing ("your creativity, your call") positions the off switch as generosity while the 38-billion-uses number does the real work of saying *this is not going away*.
- The generative/assistive binary breaks at the edges: is Magic Expand "generating" when it invents pixels that were never photographed? Canva says yes; a careful art director might say the output is still fabricated and should be labelled.
- The label depends entirely on downstream platforms honouring metadata, which they do inconsistently and can change.
- Nothing here improves the *quality* of what anyone makes. It improves the honesty of the record, which is a different and smaller good.

**Should we...**
- ✅ **Adopt it** — the taxonomy, as the marketing programme's standing rule.
**Why:** Every asset the residency programme publishes now passes through tools that can fabricate, and until this week there was no shared definition of where fabrication starts. Canva has supplied one that a non-designer can apply: **assistive edits (remove a background, move an object, straighten a crop) are retouching; generative edits (extend the frame, invent a person, replace a sky) are authorship.** That distinction belongs in the voice-and-visual document next to the navy and the Inter rule, because it decides two practical things at once — what we are willing to do to a photograph of a real faculty member, and what we are willing to upload with a label on it. The second use is defensive: when a resident or attending asks why a department poster can't just have the background removed, the answer is yes, and here is why that one is allowed. The third is a warning worth filing: the metadata travels. Anything generated in Canva can arrive on Instagram already tagged as AI-generated, which in a clinical setting is not a neutral fact — it invites the reader to discount the whole artifact, correct date and all.

---

### Klistra — "Designed, not generated"
**Link:** https://klistra.ai/ · Show HN, **18 November 2026** (2 points, 0 comments — the launch went unnoticed)
**Type:** Tool (a motion/video studio with a spec at the centre)

**What it is:** A browser studio for short video and stills that positions itself explicitly against diffusion. You bring media, say what you want, and Klistra writes a **plan with you, scene by scene, timed to your sound**; every frame is then *built from parts* — real type, your exact files, placed on purpose. The landing page runs the comparison as a table: a diffusion generator *"paints every frame from noise… your media, redrawn from memory… one change, a whole new video… faces and products drift from shot to shot."* Klistra: *"your words, set as real type… one change, only that changes… render again, the same video… no limits on length, resolution or fps… consistent across the whole project."* Everything is generated in every size from one plan, and the showcase includes a print-ready label at 219 × 138 mm alongside the 9:16s and 1:1s.

**What's good about it:** **Determinism is the feature, and almost nobody ships it.** "Render again, the same video" and "one change, only that changes" are the two properties that make motion usable inside a brand system, because a brand system is a set of things that must stay the same while one thing changes. A generator that re-guesses the whole frame when you fix a date is not a design tool, it is a slot machine with a timeline. Second: **real type.** Text set as type rather than painted as pixels is the difference between a title card we can defend in a review and one that has to be squinted at. Third: the print-size output implies a vector/type pipeline underneath, which is the only way a 219 × 138 mm label can be anything but mush. Fourth, and quietly important: the **plan comes before the render**, which is the same insight as today's Lifehacker item arrived at from the other direction.

**Pros:**
- The thesis is the correct thesis for this exact moment: the industry's motion problem is not realism, it is control and repetition.
- One plan, every aspect ratio, is the real social-media problem solved structurally rather than by re-prompting four times and hoping the crop holds.
- Deterministic re-render makes review possible: a stakeholder note ("change the price") produces a diff, not a new film.
- Print-spec output in the same tool as 9:16 is unusual and points at a type-and-layout engine, not an image generator with a video wrapper.
- The comparison table is unusually well aimed — it names the failure modes of the alternative instead of claiming superiority in the abstract.

**Cons:**
- **Two points on Hacker News and zero comments.** This is an unlaunched product with a marketing page; there is no independent evidence that any of it works as described.
- Every showcase frame is self-selected and self-hosted, and a still cannot demonstrate the one claim that matters — that a re-render is identical. Only a file hash and two renders would.
- "Spec-driven" moves the difficulty rather than removing it: you must be able to write the plan, which is exactly the skill that most people outsourcing to AI do not have.
- The aesthetic in the showcase is coherent and slightly dated — the same sans-on-gradient launch-film look the ecosystem already has. Control does not guarantee taste.
- Pricing is subscription and opaque from the landing page, and generated media can be mixed into scenes, which quietly reopens the drift problem the table promised to solve.

**Should we...**
- 👀 **Watch it** — but run the one test that decides it.
**Why:** The residency programme's motion work has one genuine bottleneck: 28 filmed faculty interviews, and a social output that has to come out in 9:16, 1:1 and 16:9 with the same title and the same name card. Today that is done by re-exporting and re-fixing type four times, which is why the series never quite looks like one series. Klistra's claim — one plan, every size, deterministic re-render, real type — is precisely the missing capability, and it is worth one hour to test rather than an afternoon to argue about. The test: take one real clip and one real faculty name, ask for a 9:16 and a 16:9, then check three things a screenshot cannot tell you — is the title the same typeface at both sizes, does the name card sit on the same optical line, and does a second render produce an identical file. If all three pass, this is the first motion tool in a fortnight that solves a problem we actually have. If any fail, we have learned that "designed, not generated" is a positioning line and we go back to building the motion grammar by hand.

---

### Onlook 2.0 — design on the real repo, in your own agent
**Link:** https://github.com/onlook-dev/onlook · **v2.0.0 replaced the entire tree on 17 November 2026** · Launch HN **19 November** (120 points, 83 comments) · Apache-2.0 · 27,536★, 1,645 commits, 171 tags
**Type:** Tool (an agent-native design canvas, now a desktop app)
**Previously covered, new:** judged 14 September (v1 web editor, adopted) and 18 September (watch, for design-system depth). This is not the same product — v2.0.0 is a full rewrite as a local-first desktop app that works on your own repository, which is the capability the September notes said was missing.

**What it is:** Onlook v1 was a web editor. On 17 November the repo's whole tree was replaced: v1 is preserved on a `v1` branch and `v1-final` tag, and the new thing is **a local-first desktop app for designing on your own codebase with an AI agent.** It opens any Git repository on your machine and runs your own dev server, so the canvas shows the real app, not a mock. You bring your own Claude Code or ChatGPT/Codex plan — Onlook ships no model. The canvas holds mobile, tablet and desktop frames side by side; the agent can arrange variations, states and flows; work happens in a **safe worktree copy so your folder is never touched**; artifacts export as self-contained HTML, PNG, JPEG or PDF; and there is a one-press path from checks to pull request.

**What's good about it:** The two decisions that matter are both structural. **"Works on your real repo"** — the design surface is the product, which removes the rebuild step that every mockup creates and that Figma's own research has been complaining about for years. And **"bring your own agent"** — no proprietary model, no cloud keys, no account needed for a source build, so the quality ceiling is the model you already pay for and the context is the code you already have. Second good thing, and a surprise: the repo ships governance documents — `ANTIPATTERNS.md`, `GLOSSARY.md`, `WRITING.md`, plus a doctor config and a security policy. A design tool whose repository contains an explicit list of things not to do is a design tool built by someone who has watched agents do them. Third: the 2.0 rewrite is documented honestly in the commit — v1 kept, licence unchanged, one snapshot, build-from-source instructions — which is rarer than it should be.

**Pros:**
- Real code, real dev server, side-by-side breakpoints: the review surface and the shipped surface are the same artifact.
- The worktree copy is the right safety model — you can let an agent loose on a page without risking the working tree.
- Bring-your-own-agent means the tool improves when the models do, and it works offline with a local model if you want.
- Export to self-contained HTML and PDF is the unglamorous feature that makes a design tool usable for review with people who do not have the repo.
- Apache-2.0 with 27.5k stars, six contributors-plus, and a real YC company behind it — this is not a weekend.

**Cons:**
- **An infinite canvas plus an agent is the strongest slot machine yet built.** "Agent arranges the canvas for you (variations, states, flows)" is exactly the volume metric this brief distrusts; 40 variations is not 40 ideas.
- A desktop app on a hospital-managed machine is an IT conversation, not a download — and the app that would benefit most (the Unified Platform) is the one least likely to be allowed to run a local dev server with write access.
- It has no design-system awareness. It will produce our navy and our Inter only because they are in the repo, and it will drift them the moment a page is generated fresh.
- The prototype runs against your real data layer, so the states that matter most — empty, error, permission-denied — still do not appear unless someone writes fixtures (the Mercury lesson, unlearned).
- 83 HN comments is the highest-signal review of this launch and I have not read them; the README is the vendor's own account.

**Should we...**
- 👀 **Watch it** — and take the worktree idea now, without the app.
**Why:** The Unified Platform is exactly the case Onlook is aimed at, and exactly the case where the installer is the obstacle: React, real components, a token layer, and a design surface that lives on a VPS rather than in a designer's folder. So the software is a Watch on practical grounds, not on merit. What is available today, for free, is the *method* the app encodes: let an agent work on a **copy** of the branch, render the real components, review at three widths, and throw the copy away if it is wrong. That is a discipline, not a product, and it is the difference between exploring on production and exploring next to it. The thing to be careful about is the canvas itself. A surface that can hold forty variations will get forty variations, and the last fortnight of this brief has been one long argument that the number of variants is not the measure — which one survived review is.

---

### Kern — a type playground whose export is a URL
**Link:** https://kern.sammii.dev · written up **18 November 2026**, HackerNoon, by the author (Sam)
**Type:** Tool (free, browser-only, no backend)

**What it is:** A typography explorer with three views: a **specimen sheet**, a **playground** that exposes every axis of a variable font as a slider, and a **type-scale generator** that writes fluid `clamp()` values as `:root` CSS variables. Six fonts ship with it — Inter, Fraunces, Recursive, Roboto Flex, Playfair Display, Source Serif 4 — each declaring its axes explicitly *including the custom ones* (Recursive's `CASL`, `CRSV`, `MONO`; Roboto Flex's `GRAD`; Fraunces' `SOFT` and `WONK`), with real min/max/default pulled from the font binary. Compare mode runs two independent panels side by side, at the same size, in the same paragraph. Every piece of state lives in the query string: *"There is no backend, no database, no sign-in. The URL is the document."*

**What's good about it:** The **dampened minimum**, which is a small piece of taste encoded as maths and the reason this is an item rather than a link. In the clamp generator the minimum size's exponent is multiplied by 0.75: *"If the ratio is a Perfect Fourth (1.333), a naive min-size scale will drop headings on mobile way too aggressively, because the ratio compounds at every step… Dampening the min exponent pulls the small end back toward readable. It is a taste call. I lifted it from looking at what actual shipped sites do and reverse-engineering the slope."* That is the rarest thing in a design tool: an opinion, stated as an opinion, with its reasoning and its provenance. Second: **URL-as-document** is the same principle as the decision trail — a screenshot cannot carry a slider position, and a link can, so a type review becomes something two people can actually have. Third: the output is a token layer, not a picture — `clamp(0.8646rem, 0.7188rem + 0.3889vw, 0.9375rem)` pasted into `:root`.

**Pros:**
- Inter is in the font set, so the Unified Platform's own type scale can be generated and exported rather than argued about.
- Exposing custom axes is the difference between using a variable font and owning one; most UIs never surface them.
- The 0.75 dampening is a genuinely good default that fixes the most common fluid-type mistake — headlines that are enormous on desktop and unreadable on a phone.
- Shareable state with zero infrastructure is how a design decision gets reviewed by a non-designer: send the link.
- Free, no account, no upload; it runs entirely in the browser, which is the only category of tool a health system approves without a meeting.

**Cons:**
- **It is one person's weekend project** — no tests, no repository mentioned, six hard-coded fonts, and a Pro tier already announced for the features that would make it a system input (Style Dictionary tokens, Tailwind snippets, saved presets).
- The clamp output rounds to four decimal places, which produces fractional rem values that will fight a strict 4/8 spacing grid and look wrong to anyone who wants a clean scale.
- A scale generated from a base size, a ratio and two viewports is **a system, not a decision** — it will be internally consistent and completely generic unless someone chooses the display sizes by eye afterwards.
- No optical-size handling, no measure (line-length) guidance, no vertical rhythm — the three things that separate a type system from a type scale.
- The write-up is the author explaining his own tool, with the maths foregrounded and no before/after of a real page.

**Should we...**
- 👀 **Watch it** — and steal the 0.75 before Friday.
**Why:** The Unified Platform's type scale is one of the few things in it that is genuinely decided rather than inherited, and it has never been expressed as fluid values — every size is a fixed number that has to be re-chosen at each breakpoint. Kern's clamp generator is a fifteen-minute job that produces the token layer: base 16, a ratio we choose deliberately, 375 to 1440, and the dampened minimum so the schedule grid's headings do not collapse on a phone. That is free, reversible, and it writes CSS we can read. What to resist is the tool's frame: picking a ratio from a dropdown is not choosing a type system. The decisions that make type look designed — where the display cut lives, how tight the tracking goes at size, how long a line of body copy runs — are not in the generator, and a scale that arrives fully formed from four numbers is the typographic version of a preset. Use it to *compute*, then set the specimen by eye at 96px, 32px and 16px, exactly as the Gemini 4 Hydrogen note argued yesterday.

---

### Vemlora — retyping a flattened poster, one almost-right letter at a time
**Link:** https://vemlora.io · Show HN, **20 November 2026** · pricing $6 per 2,500 credits, 35 free credits on sign-up
**Type:** Tool (an image editor that repaints text in place)

**What it is:** A browser tool for changing words in a finished image without the source file. Upload a PNG, JPEG, WebP, HEIC or HEIF up to 20MB, draw a box around the words — or type the original text to match — enter the replacement, generate, and compare *"the lettering, spacing, and background before downloading."* The use cases are named precisely and they are all real: a poster date that changed, a price on a product photo, a label in a screenshot. No PSD, no font file, no Photoshop. Its own FAQ is honest about the limits: *"Results can differ in lettering or small details. Check the downloaded image before publishing."*

**What's good about it:** The problem is genuinely common and the tool is aimed at the right moment — the Tuesday afternoon when someone needs last year's flyer with this year's date and there is no source file because the freelancer kept it. And the interface makes the correct demand: it asks you to **compare lettering and spacing before you download**, which is more self-awareness than most generative tools show. The format support (HEIC, HEIF) and the local-first setup step are sensible for a phone-photographed poster.

**Pros:**
- Solves the specific, frequent, low-glamour task of updating one string in a flattened asset.
- Asks the user to verify lettering and spacing rather than promising a match — the right posture for a repaint.
- Browser-based with a no-sign-in preparation step; predictable per-credit pricing rather than a subscription.
- Credits are returned when a generation fails, which is unusually fair for this category.

**Cons:**
- **The output is a near-miss, which is the most dangerous kind of artifact.** A repainted date in a typeface that is almost ours, at tracking that is almost right, survives review precisely because it looks close — and then the poster goes out with two slightly different kinds of type on it and nobody can say why it looks cheap.
- It exists because a process failed. The correct fix is that the department owns a template and the source file; a tool that makes losing them painless makes losing them normal.
- No font matching against an actual typeface — it is a diffusion repaint, so repeated letters will not agree with each other, which is the exact tell Lifehacker identified today.
- Nothing about a hospital's version control: no record of what changed, no way to prove the approved copy is the approved copy.
- Marketing copy promises a match the FAQ then disclaims, and the pricing is per-generation rather than per-approved-asset, so a near-miss costs money twice.

**Should we...**
- ❌ **Skip it** — and fix the cause instead.
**Why:** Posters, flyers and Sub-I materials should always have a source file in the department's own hands, and the moment a tool makes it easy to avoid that, the template rots. The failure Vemlora solves is real, but the failure it *creates* is worse for us: a date repainted into a flattened JPEG is text that a proofreader cannot check against approved copy, that the print shop cannot reliably reproduce at A2, and that quietly introduces a second typeface into a brand system that has exactly one. There is a correct cheap alternative we already have — rebuild the flyer in the platform's own type stack, 20 minutes, output that is correct at any size and diffable against last year's. Keep Vemlora in the file for one narrow case only: an image where the words are incidental, the asset is a photograph rather than a designed artifact, and nobody will ever need it at print size.

---

## Slop Radar
- **The "one shot" is a claim made by people with an interest in it.** Van de Sande's line is the sharpest version: the people claiming a one-shot result *"often want to sell you their model, or they hate AI precisely for making it easy."* Both need the claim; neither shows the 75 hours.
- **The discovery layer is now half counterfeit software.** Today's GitHub `design-tools` and `typography` topic feeds returned *Inventor 2026 Full*, *Rhino-8-Full*, *SketchUp-Professional-Install*, *Adobe InDesign AI Latest* — six repos with a product name in the title, 60–90 stars each, and nothing inside. Judge by author and commit history; star count is now a farmable number.
- **The brush-stroke font.** A named, checkable tell: it comes from a chat model reading the word "brush lettering" literally, and the letters have slight variations because a diffusion model cannot set a glyph. If a poster has it, the brief was invented by a machine.
- **Near-miss type as the new slop.** Slop used to fail loudly — wrong typeface, wrong spacing, obviously wrong. Retyping a flattened poster produces the opposite: type that is nearly right, which passes review and ships. The next quality problem is not the artifact that looks generated; it is the artifact nobody can tell was.

## Overall Assessment
Today's finds all point at the same object: **the hidden intermediate document.** Van de Sande's 39,000 words of direction, the design brief a thinking model writes before it renders anything, Klistra's scene plan, Kern's URL, Canva's metadata label, Onlook's worktree — every one of them is something that sits *between* intent and output, and every one is only as good as whether a human can see and edit it. That is the week's real lesson and it is more useful than any tool: the difference between a slot machine and a design process is not the model, it is whether the decision is inspectable before it becomes pixels. The highest-leverage move for Shareef this week is accordingly small, free and immediate: for the next poster, flyer or social card, require the brief first — concept, type, palette, image, hierarchy, and the two facts that must be correct — read it the way you would read a junior's rationale, then render. Keep the brief. It is the one artifact that explains the work a year later, and it is the only one the model cannot quietly overwrite.

-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-11-20.md — verified written
Email: Email sent: AI Design Intel — November 20, 2026
Vault: Vault: added 6 item(s) → 1956 total (2026-11-20). (Onlook 2.0 refused as already filed — covered 14 & 18 Sept; v2.0 rewrite noted in the item.)
