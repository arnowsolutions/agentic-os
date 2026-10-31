# Arnow Solutions — Portfolio Report

*Last updated: October 30, 2026 at 04:44 PM*

**1 project tracked** · 1 fully documented · 0 voice notes on file

---

## Personal Tools

### ✔ The Listening Room

**Status:** live · **Built with:** Python, FastAPI, self-hosted transcription, scheduled agent pipeline · **Link:** https://audiobook.srv1738752.hstgr.cloud

**Why it was created**

I listen to audiobooks constantly, and I wanted the reading experience I have with a physical book — chapter navigation, knowing exactly where I am, being able to search back for a passage — but for audio. Commercial players give you a progress bar and not much else. I wanted my own library, my own rules, and word-level captions so I could read along while listening.

**What problem it solved**

Two problems, actually.

The first is the obvious one: off-the-shelf audiobook apps either lock you into a store, mangle your chapters, or charge a subscription for a library you already own. None of them show you the actual words. So I built a self-hosted player that streams my own files with proper byte-range seeking, honors the chapter marks embedded in the file, and transcribes every book on the machine so I can follow the text while it plays.

The second problem is the one I didn't expect it to solve. I don't have time to read research. Every week I want to know what happened in AI — the notable repos, the model releases, the funding, the conversations worth following — and every week it sat in a tab I never opened. So I pointed my agent at it. Every week a job researches the top developments, writes a brief, produces a two-host podcast episode, and files it into my library as a chaptered audiobook. I never go looking for the research. It shows up in the same place my books live, already spoken out loud, ready for the commute.

**What's cool about it**

The captions are word-level, not just sentence-level, so the text follows the audio word by word as it plays. Transcription runs entirely on the machine — my books never leave the server.

But the part I actually like is that it turned into a research machine. The weekly AI roundup is produced end to end without me touching it: an agent pulls real sources, produces a two-host conversation about the week, and ships it as a properly chaptered audiobook sitting next to Kevin Hart and 50 Cent. It runs on its own schedule, verifies its own file before releasing it — duration, chapter count, tags — and refuses to hand over a broken episode. It reports the failure instead of faking one.

There's also a live waveform on the seek bar drawn from the actual audio, so you can see where the loud parts are. Real per-user access control — an admin grants specific books to specific accounts rather than one shared password. And the whole thing runs behind a supervisor that restarts it if it dies, so the URL never serves a dead page.

The proof it works: a stack of weekly roundups is sitting in the library right now — October 5th, 12th, and 19th — each one researched, written, voiced, chaptered, and filed without me asking.

