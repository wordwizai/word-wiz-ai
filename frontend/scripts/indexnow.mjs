/**
 * Push changed URLs to IndexNow.
 *
 * IndexNow is an instant-notification protocol: instead of waiting to be
 * crawled, you POST a URL list and participating engines fetch them. Bing,
 * Yandex, Seznam and Naver consume it — Google does not. Bing matters
 * disproportionately here because its index is what ChatGPT search reads.
 *
 * Unlike Search Console's ~10-12/day manual quota, IndexNow accepts up to
 * 10,000 URLs per request, so the whole site goes in one call.
 *
 * Run AFTER deploying, never during the build — the build produces files that
 * are not live yet, and submitting URLs that 404 gets a host de-trusted.
 *
 *   npm run indexnow                    # every URL in the live sitemap
 *   npm run indexnow -- --since 3       # only URLs with lastmod in last 3 days
 *   npm run indexnow -- --dry-run       # print what would be sent
 *
 * The key is self-generated (the protocol allows this — no account needed) and
 * hosted at /<key>.txt, which is how engines verify you own the host.
 */

import { readdirSync, readFileSync } from "fs";
import { join } from "path";

const ORIGIN = "https://wordwizai.com";
const HOST = "wordwizai.com";
const ENDPOINT = "https://api.indexnow.org/indexnow";
const PUBLIC_DIR = join(new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"), "public");

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const sinceIndex = args.indexOf("--since");
const sinceDays = sinceIndex !== -1 ? Number(args[sinceIndex + 1]) : null;

/** The key file in public/ is the source of truth — it's what engines fetch. */
function findKey() {
  const candidates = readdirSync(PUBLIC_DIR).filter((f) =>
    /^[a-f0-9]{16,128}\.txt$/i.test(f)
  );

  if (candidates.length === 0) {
    console.error(
      `No IndexNow key file found in ${PUBLIC_DIR}.\n` +
        "Expected a file like <key>.txt whose contents are exactly the key.\n" +
        "Generate one with:\n" +
        "  node -e \"const k=require('crypto').randomBytes(16).toString('hex');" +
        'require("fs").writeFileSync(`public/${k}.txt`,k);console.log(k)"'
    );
    process.exit(1);
  }

  if (candidates.length > 1) {
    console.error(
      `Multiple IndexNow key files in public/: ${candidates.join(", ")}\n` +
        "Keep exactly one so it's unambiguous which key is authoritative."
    );
    process.exit(1);
  }

  const file = candidates[0];
  const key = readFileSync(join(PUBLIC_DIR, file), "utf-8").trim();
  const expected = file.replace(/\.txt$/i, "");

  if (key !== expected) {
    console.error(
      `Key mismatch: ${file} contains "${key}".\n` +
        "The file's contents must exactly equal its filename minus .txt, or " +
        "engines reject the submission."
    );
    process.exit(1);
  }

  return key;
}

/**
 * Read the live sitemap, not the local build. What matters is the URLs that
 * are actually deployed — submitting a URL that 404s damages host trust.
 */
async function liveSitemapUrls() {
  const response = await fetch(`${ORIGIN}/sitemap.xml`, {
    headers: { "user-agent": "word-wiz-indexnow" },
  });

  if (!response.ok) {
    console.error(`Could not fetch ${ORIGIN}/sitemap.xml — HTTP ${response.status}`);
    process.exit(1);
  }

  const xml = await response.text();

  if (xml.includes('<div id="root"')) {
    console.error(
      "sitemap.xml returned the SPA shell rather than XML. The deploy that " +
        "generates it hasn't landed — run npm run verify:live first."
    );
    process.exit(1);
  }

  const entries = [...xml.matchAll(/<url>([\s\S]*?)<\/url>/g)].map((block) => ({
    loc: block[1].match(/<loc>([^<]+)<\/loc>/)?.[1],
    lastmod: block[1].match(/<lastmod>([^<]+)<\/lastmod>/)?.[1],
  }));

  return entries.filter((e) => e.loc);
}

// Wrapped in a function so success paths can return rather than call
// process.exit(), which on Windows trips a libuv assertion when fetch's
// keep-alive sockets are still closing.
async function main() {
const key = findKey();
console.log(`IndexNow key: ${key}`);
console.log(`Key location: ${ORIGIN}/${key}.txt\n`);

// Verify the key file is actually reachable before submitting. If engines
// can't fetch it, every URL in the batch is rejected.
if (!dryRun) {
  const keyCheck = await fetch(`${ORIGIN}/${key}.txt`, {
    headers: { "user-agent": "word-wiz-indexnow" },
  });
  const keyBody = (await keyCheck.text()).trim();

  if (!keyCheck.ok || keyBody !== key) {
    console.error(
      `Key file is not live at ${ORIGIN}/${key}.txt (HTTP ${keyCheck.status}).\n` +
        "Deploy first — engines fetch this file to verify you own the host."
    );
    process.exit(1);
  }
  console.log("Key file verified live.\n");
}

let entries = await liveSitemapUrls();
const total = entries.length;

if (sinceDays !== null && !Number.isNaN(sinceDays)) {
  const cutoff = new Date(Date.now() - sinceDays * 86400000);
  entries = entries.filter((e) => e.lastmod && new Date(e.lastmod) >= cutoff);
  console.log(
    `Filtered to ${entries.length} of ${total} URLs with lastmod in the last ${sinceDays} day(s).`
  );
}

const urlList = entries.map((e) => e.loc);

if (urlList.length === 0) {
  console.log("Nothing to submit.");
  return;
}

console.log(`Submitting ${urlList.length} URL(s).`);
console.log(`  e.g. ${urlList.slice(0, 3).join("\n       ")}`);
if (urlList.length > 3) console.log(`       ... and ${urlList.length - 3} more`);

if (dryRun) {
  console.log("\n--dry-run: nothing sent.");
  return;
}

// The protocol caps a single request at 10,000 URLs.
const BATCH = 10000;
for (let i = 0; i < urlList.length; i += BATCH) {
  const batch = urlList.slice(i, i + BATCH);

  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: { "content-type": "application/json; charset=utf-8" },
    body: JSON.stringify({
      host: HOST,
      key,
      keyLocation: `${ORIGIN}/${key}.txt`,
      urlList: batch,
    }),
  });

  const explain =
    {
      200: "accepted",
      202: "accepted — key validation pending",
      400: "bad request (malformed URL list)",
      403: "key rejected — the key file could not be verified",
      422: "URLs do not match the declared host, or the key is invalid for them",
      429: "rate limited — too many requests, try again later",
    }[response.status] ?? "unexpected response";

  console.log(`\nHTTP ${response.status} — ${explain}`);

  if (response.status >= 400) {
    const body = await response.text();
    if (body) console.error(body.slice(0, 400));
    process.exitCode = 1;
    return;
  }
}

console.log(
  "\nDone. Bing typically reflects this within hours; there is no per-URL\n" +
    "confirmation, so check coverage in Bing Webmaster Tools rather than here."
);
}

await main();
