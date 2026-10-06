<!-- Title: Growth agent: SEO fixes and state (running PR) -->
<!-- Bruce ships by merging growth-agent into dev and dev into main, so no PR is open. This file is the running summary instead. -->

Running summary of the growth agent's work. Bruce ships it by merging `growth-agent` into `dev` and `dev` into `main`.

## Live (on main, deployed 2026-10-06)

- Session 1: removed invented review ratings from comparison schema, retitled the ABCmouse vs Hooked on Phonics page and the silent-e guide, dropped stale 2024/2025 titles, added 20 magic-e sentences.
- Session 2: About page "Who built this" (AQ-005), four magic-e practice pages, the public guest analysis route and `/try/:slug` page with guide CTAs pointing at it, the digital-silence fix, and the try-page privacy line (AQ-011). Backend deployed 9583b5d; frontend in main 2e9d41a.

## On growth-agent, not on main yet (session 3, 2026-10-06)

| Commit | Change |
|---|---|
| `d819ec7` | b/d article title and description: "Child Confuses B and D? When It's Normal and How to Fix It" |
| `48f77d6` | Long-vowel guide title and description: "Long Vowel Sounds Practice: 200+ First Grade Words and Games" |
| `d864a4c` | sitemap-lastmod.json hashes after the build |
| `f51d6ad` | Free magic-e printable at `/printables/magic-e-sentences.pdf`, a download CTA on the silent-e guide, and a `printable_download` event. The inline CTA now renders a plain link for PDFs |
| `a05b4a0` and later | growth-agent/ files only (queue, listings, state, log, graphics). Not served |

Verified: `npm ci && npm run build` (158 pages prerendered, validation passed).

Pushed to origin 2026-10-06 once the Claude GitHub App was installed on the org.

## Waiting on Bruce

See `growth-agent/APPROVAL_QUEUE.md`:
- Approved and ready to send now that the try page is live: AQ-013/AQ-014 (Reddit, a day apart), AQ-017/AQ-020 (emails), AQ-019 (TeachersFirst, waiting on the reCAPTCHA tick). AQ-018 is already sent.
- Pending: AQ-021 to AQ-030 (outreach wave 2), AQ-031 (ISTE listing edit), AQ-032 (Free Homeschool Deals), AQ-033 (Product Hunt relaunch), AQ-034 to AQ-062 (wave 3).
- **AQ-036 first**: recordings go to Deepgram without its training opt-out, and the privacy page doesn't cover AI or deletion.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01SFrJ4DTLdLaNBSaNr8HLwV
