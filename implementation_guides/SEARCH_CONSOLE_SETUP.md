# Search Console + Bing Webmaster Setup

Tier 0 item #3. This is the one part of Tier 0 that can't be done from the
repo — it needs your Google account and access to the domain's DNS.

Budget: ~20 minutes, once.

**Do this after the prerender fix is deployed**, not before. All 44 pages
changed their title, description and canonical in that deploy, so you want
Search Console watching from the moment the corrected HTML is live.

---

## 1. Google Search Console

### Create the property

Go to https://search.google.com/search-console → **Add property**.

Choose **Domain** (the left-hand option), not URL prefix. Enter `wordwizai.com`.

Why Domain: it covers `http://`, `https://`, `www.`, and every subdomain under
one property. A URL-prefix property would treat `https://wordwizai.com` and
`https://www.wordwizai.com` as separate sites and split the data.

### Verify via DNS

Google will show a TXT record like `google-site-verification=abc123...`.

DNS for this domain is served by **Cloudflare** (confirmed from the response
headers — `Server: cloudflare` in front of the Vercel origin). So:

1. Cloudflare dashboard → select `wordwizai.com` → **DNS** → **Records**
2. **Add record**: Type `TXT`, Name `@`, Content = the full
   `google-site-verification=...` string
3. Proxy status is irrelevant for TXT records; leave defaults
4. Save, then click **Verify** in Search Console

Cloudflare propagates in seconds, but if it fails, wait a few minutes and retry
rather than adding a second record.

### Submit the sitemap

Search Console → **Sitemaps** → enter `sitemap.xml` → Submit.

There is only one sitemap now. `sitemap-comparisons.xml` was deleted during
Tier 0 — every one of its five URLs was already in `sitemap.xml`, and nothing
referenced it.

### Force a recrawl of the fixed pages

This deploy materially changed what every page serves. Don't wait for Google to
rediscover it on its own schedule.

Use **URL Inspection** (top search bar) → paste a URL → **Request Indexing**.

There's a daily quota of roughly 10–12 manual requests, so spend it on the
pages that already rank. Suggested first batch:

1. `https://wordwizai.com/`
2. `https://wordwizai.com/guides/how-to-teach-cvc-words-to-struggling-readers`
3. `https://wordwizai.com/guides/phonics-activities-5-year-old-struggling-reader`
4. `https://wordwizai.com/comparisons/best-free-reading-apps`
5. `https://wordwizai.com/comparisons/hooked-on-phonics-vs-word-wiz-ai`

Do the rest over the following days, or just let the sitemap handle them.

While you're in URL Inspection, click **View Crawled Page** on one of them and
confirm the HTML now shows that page's own title and canonical. If it still
shows the homepage's, the deploy didn't take.

---

## 2. Bing Webmaster Tools

Worth doing even though Bing's direct search share is small: **Bing's index is
what ChatGPT search reads from**. This is the cheapest path to being cited by
an LLM.

Go to https://www.bing.com/webmasters → sign in → **Import from Google Search
Console**. That copies the property and the verification across in about a
minute, so do GSC first.

If the import path gives you trouble, add the site manually and verify with a
second Cloudflare TXT record.

Then submit `https://wordwizai.com/sitemap.xml` under **Sitemaps**.

---

## 3. Optional, 5 minutes: IndexNow

Bing (and Yandex, and increasingly others) support IndexNow, which pushes URL
changes instead of waiting to be crawled.

Bing Webmaster Tools → **IndexNow** → generate a key. It gives you a key file
to host at `https://wordwizai.com/<key>.txt`.

Drop that file in `frontend/public/` and it deploys with the site. After that,
a single HTTPS GET announces changed URLs. Worth wiring into the build later;
not urgent.

---

## What you get once this is live

Search Console is the data source for Tier 1 item #7 — the weekly loop that
finds queries ranking in positions 8–20 and improves those pages. That loop
can't run at all until this property exists and has accumulated ~28 days of
data, so setting it up now starts the clock.

Give it two weeks before drawing conclusions. Search Console data lags by
2–3 days, and re-indexing 44 changed pages takes a while.
