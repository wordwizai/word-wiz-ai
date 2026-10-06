# growth-agent/

Working files for the Word Wiz growth agent. These live on the `growth-agent`
branch only and are not part of the site.

- `STATE.md` - metrics history, what's working, ranked backlog, next actions
- `APPROVAL_QUEUE.md` - drafts waiting on Bruce (emails, posts, anything public or hard to undo)
- `RUN_LOG.md` - one entry per session
- `LISTINGS.md` - every directory submission, so nothing is submitted twice
- `data/` - dated metric snapshots copied out of Search Console

Not served: Vercel's Root Directory is `frontend/`, so nothing at the repo root
(including this folder) is uploaded or built. Vite only copies
`frontend/public/` into `dist/`.

Where the branch lives locally: a worktree at
`.claude/worktrees/growth-agent` (the main checkout stays on `dev`).
