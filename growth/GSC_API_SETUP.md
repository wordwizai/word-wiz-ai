# Search Console API credentials

This covers exactly one thing: getting `frontend/scripts/gsc-report.mjs` a
service-account credential that can read Search Console data via the API.

**Do this after, not instead of,** [`implementation_guides/SEARCH_CONSOLE_SETUP.md`](../implementation_guides/SEARCH_CONSOLE_SETUP.md) —
that doc creates the Search Console property itself, verifies it via a
Cloudflare DNS TXT record, submits the sitemap, and covers Bing/IndexNow.
None of that is repeated here. This doc assumes the property already exists
and is verified.

Also wait for data to accumulate: Search Console back-fills a property with
roughly 16 months of history once it's verified, but the report script pulls
a rolling 28-day window, so give it **at least two weeks post-verification**
before the numbers are dense enough to be useful. Budget ~15 minutes for the
steps below, once.

---

## 1. Create (or pick) a Google Cloud project

Go to https://console.cloud.google.com/projectcreate

- Project name: something recognizable, e.g. `word-wiz-ai-seo`
- Organization/location: default is fine
- Click **Create**, then make sure the new project is selected in the
  top project switcher before continuing.

This is a free-tier project — the Search Console API has no billing
associated with it (see quotas/cost note at the bottom of this doc), so no
billing account needs to be attached.

## 2. Enable the Search Console API

With the project selected, go to:
https://console.cloud.google.com/apis/library/searchconsole.googleapis.com

Click **Enable**. (If that direct link 404s because it's been renamed again,
go to **APIs & Services → Library** and search "Search Console API".)

## 3. Create a service account

**IAM & Admin → Service Accounts** → https://console.cloud.google.com/iam-admin/serviceaccounts

1. **Create Service Account**
2. Name: `gsc-report-bot` (anything works; this becomes part of its email)
3. Skip granting it any project-level IAM role — it doesn't need one. Access
   to Search Console data is granted separately, in step 5.
4. **Done**

Copy the service account's email address once it's created — it looks like
`gsc-report-bot@word-wiz-ai-seo.iam.gserviceaccount.com`. You'll need it in
step 5.

## 4. Create and download a JSON key

Still in **IAM & Admin → Service Accounts**:

1. Click the service account you just made
2. **Keys** tab → **Add Key** → **Create new key**
3. Type: **JSON** → **Create**

A file downloads automatically (something like
`word-wiz-ai-seo-a1b2c3d4e5f6.json`). This file is a credential — treat it
like a password. There is no way to view it again after this step; if you
lose it, delete the key in this same UI and create a new one.

**Do not commit this file.** See "Where to put the key" below.

## 5. Add the service account as a Search Console user

Go to https://search.google.com/search-console, select the `wordwizai.com`
property, then:

**Settings → Users and permissions → Add user**

- Email: paste the service account email from step 3
  (`...@....iam.gserviceaccount.com`)
- Permission: **Restricted** is enough — the script only calls the
  read-only Search Analytics query method, never anything that changes
  settings.
- **Add**

If you skip this step, the script's API calls come back `403 Permission
denied` — it says so directly and points back here.

## 6. Where to put the key

Preferred: store it **outside the repo entirely** — e.g.
`~/secrets/wordwizai-gsc-key.json` (macOS/Linux) or
`C:\Users\<you>\secrets\wordwizai-gsc-key.json` (Windows). Nothing about
this key needs to live inside `word-wiz-ai/`.

If you'd rather keep it in-repo for convenience (e.g. so a scheduled job on
the same machine can find it by a relative path), name it so it matches the
patterns already added to the root `.gitignore`:

```
gsc-service-account*.json
*gsc*key*.json
growth/*credentials*.json
growth/*service-account*.json
```

e.g. `growth/gsc-service-account-key.json` — that path is gitignored, but
double-check with `git status` after adding it that it really shows as
untracked/ignored, not staged, before you ever `git add`.

## 7. Install the API client and set environment variables

The script deliberately does **not** ship `googleapis` as a dependency —
it's a sizeable package and nothing else in this repo needs it. Install it
once, locally:

```bash
cd frontend
npm install --save-dev googleapis
```

Then set the two required environment variables (however you normally set
env vars for local scripts — a `.env` you source, your shell profile, or
inline):

```bash
export GSC_SERVICE_ACCOUNT_KEY="/absolute/path/to/wordwizai-gsc-key.json"
export GSC_SITE_URL="sc-domain:wordwizai.com"
```

`GOOGLE_APPLICATION_CREDENTIALS` also works in place of
`GSC_SERVICE_ACCOUNT_KEY` if you already use that name for other Google
tooling — the script checks `GSC_SERVICE_ACCOUNT_KEY` first, then falls back
to it.

**On `GSC_SITE_URL`:** because `SEARCH_CONSOLE_SETUP.md` has you create a
**Domain** property (not a URL-prefix one), the API identifies it as
`sc-domain:wordwizai.com` — not `https://wordwizai.com/`. If you set
`GSC_SITE_URL=wordwizai.com` (no scheme), the script auto-prefixes it to
`sc-domain:wordwizai.com` and logs that it did so; it's called out here so
the auto-correction doesn't come as a surprise. If you ever switch to a
URL-prefix property instead, use the full `https://wordwizai.com/` form.

## 8. Run it

```bash
cd frontend
node scripts/gsc-report.mjs
```

Output: `growth/gsc-opportunities.json` and `growth/gsc-opportunities.md`.

To preview the report's shape before credentials exist (no API calls, no
key needed, obviously-fake data), run:

```bash
node scripts/gsc-report.mjs --sample-data
```

That writes `growth/gsc-opportunities.sample.json` /
`.sample.md` instead — separate filenames so a synthetic run can never be
mistaken for a real one. Delete those two files once you've looked at them;
they're not meant to be a permanent part of the repo.

---

## Quota and cost

Verified against Google's current published limits
(`developers.google.com/webmaster-tools/limits` and the
`searchanalytics.query` API reference) as of this writing:

- **The API itself is free.** There is no billing tier for Search Console
  API calls — enabling it does not require a billing account, and there is
  no per-call cost.
- **Rate limits:** 1,200 queries per minute per site, 1,200 per minute per
  user, 30,000,000 per day per project. A weekly run of this script makes
  2 API calls (one `["query","page"]` request, one `["page"]` request), plus
  one more per additional 25,000-row page if a query ever returns a full
  page (`rowLimit` maxes out at 25,000 rows per request; the script pages
  automatically via `startRow` and warns if it hits the configurable
  `GSC_MAX_ROWS` safety cap, default 100,000). For a site this size, that's
  nowhere close to any published limit — you would need to run this dozens
  of times a minute to notice a quota at all.
- **Search Console's own UI quota** (the ~10-12/day manual "Request
  Indexing" actions mentioned in `SEARCH_CONSOLE_SETUP.md`) is unrelated —
  that's a UI-only limit on the URL Inspection tool, not the API this
  script uses.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "needs the googleapis package" | Not installed | `npm install --save-dev googleapis` in `frontend/` |
| "isn't wired up yet" | Missing env var, or key file path is wrong | Check `GSC_SERVICE_ACCOUNT_KEY`/`GOOGLE_APPLICATION_CREDENTIALS` and `GSC_SITE_URL` are actually exported in the shell running the script |
| "Couldn't authenticate with the service-account key" | Downloaded the wrong file, or it's corrupted | Re-download from Service Accounts → Keys (step 4) |
| 403 Permission denied | Service account not added as a Search Console user | Step 5 above |
| 404 Not found | `GSC_SITE_URL` doesn't match the property | Confirm it's exactly `sc-domain:wordwizai.com` for a Domain property |
| Report exists but every table is empty | Property verified less than ~28 days ago, or too few clicks yet | Wait — this is expected early on, not a bug |
