/**
 * Post-deploy check: is the deployed site actually serving prerendered HTML?
 *
 * The build produces one static index.html per route, but whether the host
 * serves those files (rather than falling through to the SPA shell) can only
 * be confirmed against the real deployment. Run this after every deploy.
 *
 *   node scripts/verify-live.mjs
 *   node scripts/verify-live.mjs https://staging.example.com
 *
 * Exits non-zero if any checked page returns the homepage's title or canonical,
 * which is the signature of prerendering not being served.
 */

const origin = (process.argv[2] || "https://wordwizai.com").replace(/\/$/, "");

// A spread across every page family, plus the generated text files.
const ROUTES = [
  "/",
  "/about",
  "/guides/how-to-teach-cvc-words-to-struggling-readers",
  "/comparisons/best-free-reading-apps",
  "/articles/why-child-hates-reading",
  "/practice-words",
  "/practice-words/at-family",
];

// Checking status alone is useless here: the catch-all rewrite returns the SPA
// shell with a 200 for any path that has no file, so a missing llms.txt looks
// like a healthy response. Each entry asserts a content signature instead.
const FILES = [
  { path: "/llms.txt", mustContain: "# Word Wiz AI" },
  { path: "/llms-full.txt", mustContain: "# Word Wiz AI" },
  { path: "/sitemap.xml", mustContain: "<urlset" },
  { path: "/robots.txt", mustContain: "User-agent:" },
];

const strip = (html) => html.replace(/<!--[\s\S]*?-->/g, "");
const titleOf = (html) =>
  strip(html)
    .match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]
    ?.trim()
    .replace(/\s+/g, " ") ?? null;
const canonicalOf = (html) =>
  strip(html).match(/<link[^>]*rel="canonical"[^>]*href="([^"]*)"/i)?.[1] ?? null;

// Googlebot executes JavaScript; most other crawlers (Bing, GPTBot, ClaudeBot,
// PerplexityBot, social unfurlers) do not. Fetching as a plain client is the
// honest test of what those crawlers receive.
const fetchPage = async (path) => {
  const response = await fetch(`${origin}${path}`, {
    headers: { "user-agent": "word-wiz-prerender-check" },
    redirect: "follow",
  });
  return { status: response.status, body: await response.text() };
};

let failures = 0;
const fail = (msg) => {
  console.log(`  FAIL  ${msg}`);
  failures += 1;
};

console.log(`Checking ${origin}\n`);

const home = await fetchPage("/");
const homeTitle = titleOf(home.body);
console.log(`Homepage title: ${homeTitle}\n`);

for (const route of ROUTES) {
  const { status, body } = await fetchPage(route);
  const title = titleOf(body);
  const canonical = canonicalOf(body);
  const expected = route === "/" ? `${origin}/` : `${origin}${route}`;

  console.log(`${route}`);

  if (status !== 200) {
    fail(`HTTP ${status}`);
    continue;
  }
  if (!title) {
    fail("no <title>");
  } else if (route !== "/" && title === homeTitle) {
    fail(`title is the homepage's — this page is NOT being served prerendered`);
  } else {
    console.log(`  ok    title: ${title}`);
  }

  if (!canonical) {
    fail("no canonical");
  } else if (canonical.replace(/\/$/, "") !== expected.replace(/\/$/, "")) {
    fail(`canonical is ${canonical}, expected ${expected}`);
  } else {
    console.log(`  ok    canonical`);
  }
}

console.log("");
for (const { path, mustContain } of FILES) {
  const { status, body } = await fetchPage(path);
  console.log(path);

  if (status !== 200) {
    fail(`HTTP ${status}`);
  } else if (body.includes("<div id=\"root\"")) {
    fail("served the SPA shell — this file is not in the deployed output");
  } else if (!body.includes(mustContain)) {
    fail(`missing expected content ${JSON.stringify(mustContain)}`);
  } else {
    console.log(`  ok    ${body.length} bytes`);
  }
}

console.log("");
if (failures > 0) {
  console.log(
    `${failures} check(s) failed. If titles match the homepage, the host is\n` +
      `serving the SPA shell instead of the prerendered files — confirm the\n` +
      `build command runs "npm run build" (which includes prerendering) and\n` +
      `that the deploy actually picked up a new build.`
  );
  process.exit(1);
}

console.log("All checks passed — prerendered HTML is being served.");
