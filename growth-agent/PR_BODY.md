<!-- Title: Growth agent: SEO fixes and state (running PR) -->
<!-- Open at: https://github.com/wordwizai/word-wiz-ai/compare/main...growth-agent?expand=1 and paste everything below. The agent keeps this file current each session. -->

Running summary of the growth agent's work. Bruce currently ships it by merging `growth-agent` into `dev` and `dev` into `main`.

## Live (merged to main 2026-10-05, deployed 2026-10-06)

Session 1: removed invented review ratings from comparison schema, retitled the ABCmouse vs Hooked on Phonics page and the silent-e guide, dropped stale 2024/2025 titles, added 20 magic-e sentences.

## In dev, not yet on main (session 2, 2026-10-06)

**Deploy the backend before merging dev into main.** The guides' new "Try it out loud" buttons call `/guest/analyze-audio`; until it exists the try page shows a "not available right now" screen with a signup button.

| Commit | Change |
|---|---|
| `9c84b9a` | About page "Who built this" (approved, AQ-005) |
| `895cbdd` | Four magic-e practice pages (a_e, i_e, o_e, u_e) |
| `47c92d1`, `e4a6965` | Public guest analysis route (no account, no DB writes, nothing saved, rate-limited) |
| `50e1a11` | Fix: recordings with digital silence failed the whole pipeline, for signed-in users too |
| `46a50ce` | `/try/:slug` page; guide and practice-page CTAs point to it; try-funnel analytics |

Verified: backend test suite, an end-to-end run of the guest route on the real model, and a full frontend build with prerender.

## Waiting on Bruce

See `growth-agent/APPROVAL_QUEUE.md`: AQ-011 (privacy line), AQ-012 (production quality-gate flag), AQ-013 to AQ-020 (outreach batch, send after the try page is live).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
