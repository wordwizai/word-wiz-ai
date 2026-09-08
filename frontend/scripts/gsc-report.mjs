#!/usr/bin/env node
/**
 * gsc-report.mjs — weekly Google Search Console opportunity report.
 *
 * Pulls the last N days (default 28) of query + page performance from the
 * Search Console API and writes a ranked "content improvement" opportunity
 * report to growth/gsc-opportunities.json and growth/gsc-opportunities.md.
 *
 * Two things get flagged:
 *
 *   1. "opportunities" — queries ranking at position 8-20 (page one is 1-10,
 *      so this band is "close but not quite") with meaningful impressions
 *      AND a click-through rate below what this site itself normally gets
 *      at that position. That combination means: Google already thinks the
 *      page is relevant, people are seeing it, and something (title, meta
 *      description, or the page's actual answer to the query) is stopping
 *      them from clicking or the page from ranking higher.
 *
 *   2. "ctrProblemPages" — whole pages with high impressions but an overall
 *      CTR well below the site average, regardless of position. This is a
 *      distinct signal: the page doesn't need new content, it needs a
 *      better title/meta description. Cheapest possible win.
 *
 * Setup: see growth/GSC_API_SETUP.md (credentials) and
 * implementation_guides/SEARCH_CONSOLE_SETUP.md (property + DNS, does this
 * FIRST). Playbook for acting on the report: growth/CONTENT_LOOP.md.
 *
 * Usage (from frontend/):
 *   node scripts/gsc-report.mjs
 *   node scripts/gsc-report.mjs --sample-data   # see below
 *
 * Required environment variables:
 *   GSC_SERVICE_ACCOUNT_KEY   Path to the service-account JSON key.
 *                             (falls back to GOOGLE_APPLICATION_CREDENTIALS)
 *   GSC_SITE_URL              The property as registered in Search Console,
 *                             e.g. "sc-domain:wordwizai.com" for a Domain
 *                             property (see growth/GSC_API_SETUP.md — a bare
 *                             domain like "wordwizai.com" is auto-prefixed).
 *
 * Optional environment variables (all have defaults, see CONFIG below):
 *   GSC_LOOKBACK_DAYS, GSC_LAG_DAYS, GSC_POSITION_MIN, GSC_POSITION_MAX,
 *   GSC_MIN_IMPRESSIONS, GSC_CTR_ANOMALY_FACTOR, GSC_PAGE_CTR_ANOMALY_FACTOR,
 *   GSC_MIN_BUCKET_SAMPLES, GSC_MAX_ROWS, GSC_REPORT_TOP_N, GSC_OUTPUT_DIR
 *
 * --sample-data: runs the exact same scoring/report pipeline against a small
 * hardcoded, obviously-fake dataset instead of calling the API. No
 * credentials needed. Useful for previewing the report's shape before GSC
 * has 28 days of real data. Output is written to *.sample.json / *.sample.md
 * — separate filenames, and every field is labeled synthetic — so it can
 * never be confused with a real report. It does not touch the real
 * gsc-opportunities.json/.md files.
 */

import { existsSync, mkdirSync, writeFileSync } from "fs";
import { dirname, join, resolve } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = join(__dirname, "..", "..");

const SCOPE = "https://www.googleapis.com/auth/webmasters.readonly";
const SETUP_DOC = "growth/GSC_API_SETUP.md";
const PLAYBOOK_DOC = "growth/CONTENT_LOOP.md";
const PROPERTY_DOC = "implementation_guides/SEARCH_CONSOLE_SETUP.md";

const SAMPLE_MODE = process.argv.includes("--sample-data");

// ---------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------

function intEnv(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === "") return fallback;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? n : fallback;
}

function floatEnv(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === "") return fallback;
  const n = parseFloat(raw);
  return Number.isFinite(n) ? n : fallback;
}

const config = {
  keyPath: process.env.GSC_SERVICE_ACCOUNT_KEY || process.env.GOOGLE_APPLICATION_CREDENTIALS || "",
  siteUrlRaw: process.env.GSC_SITE_URL || "",
  lookbackDays: intEnv("GSC_LOOKBACK_DAYS", 28),
  lagDays: intEnv("GSC_LAG_DAYS", 3),
  positionMin: intEnv("GSC_POSITION_MIN", 8),
  positionMax: intEnv("GSC_POSITION_MAX", 20),
  minImpressions: intEnv("GSC_MIN_IMPRESSIONS", 15),
  ctrAnomalyFactor: floatEnv("GSC_CTR_ANOMALY_FACTOR", 0.6),
  pageCtrAnomalyFactor: floatEnv("GSC_PAGE_CTR_ANOMALY_FACTOR", 0.5),
  minBucketSamples: intEnv("GSC_MIN_BUCKET_SAMPLES", 3),
  rowLimitPerPage: 25000, // API hard max for a single request
  maxRows: intEnv("GSC_MAX_ROWS", 100000),
  topN: intEnv("GSC_REPORT_TOP_N", 30),
  outputDir: process.env.GSC_OUTPUT_DIR ? resolve(process.env.GSC_OUTPUT_DIR) : join(repoRoot, "growth"),
};

// ---------------------------------------------------------------------
// Fail loudly but cleanly — no raw stack traces for expected setup gaps.
// ---------------------------------------------------------------------

function fail(message) {
  console.error("\n" + message.trim() + "\n");
  process.exit(1);
}

function missingSetupMessage() {
  const problems = [];
  if (!config.keyPath) {
    problems.push(
      "  - No service-account key path. Set GSC_SERVICE_ACCOUNT_KEY (or GOOGLE_APPLICATION_CREDENTIALS)."
    );
  } else if (!existsSync(config.keyPath)) {
    problems.push(`  - GSC_SERVICE_ACCOUNT_KEY points at "${config.keyPath}", which doesn't exist.`);
  }
  if (!config.siteUrlRaw) {
    problems.push('  - No site URL. Set GSC_SITE_URL (e.g. "sc-domain:wordwizai.com").');
  }

  return `
Google Search Console isn't wired up yet, so this report can't run.

${problems.join("\n")}

This is expected until credentials exist. Two things need to happen first:

  1. Create the Search Console property and verify DNS (one-time, ~20 min):
     ${PROPERTY_DOC}

  2. Create a service account, enable the API, and grant it read access:
     ${SETUP_DOC}

Once both are done and Search Console has accumulated data, set the env vars
this script needs and re-run it. In the meantime you can preview the report's
shape with synthetic data:

  node scripts/gsc-report.mjs --sample-data
`;
}

// ---------------------------------------------------------------------
// googleapis is deliberately not a dependency of this repo (see
// GSC_API_SETUP.md) — nothing else here needs it, and it's a sizeable
// package. Import it lazily and fail with the install command, not a
// "Cannot find module" stack trace, if it's missing.
// ---------------------------------------------------------------------

async function loadGoogleClient() {
  try {
    const mod = await import("googleapis");
    return mod.google;
  } catch (err) {
    fail(`
This script needs the "googleapis" package, which is not installed in
frontend/ (deliberately — it's kept out of the app bundle; see ${SETUP_DOC}).

Install it once:
  cd frontend
  npm install --save-dev googleapis

Then re-run:
  node scripts/gsc-report.mjs

(Underlying error: ${err.message})
`);
  }
}

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------

function normalizeSiteUrl(raw) {
  if (raw.startsWith("sc-domain:") || raw.startsWith("http://") || raw.startsWith("https://")) {
    return raw;
  }
  // A bare domain like "wordwizai.com" almost certainly means the Domain
  // property from SEARCH_CONSOLE_SETUP.md, which the API addresses as
  // "sc-domain:<domain>" rather than a URL.
  const normalized = `sc-domain:${raw.replace(/^www\./, "")}`;
  console.log(`GSC_SITE_URL="${raw}" has no scheme; treating it as a Domain property: ${normalized}`);
  return normalized;
}

function isoDate(d) {
  return d.toISOString().slice(0, 10);
}

function computeDateRange({ lookbackDays, lagDays }) {
  const end = new Date();
  end.setUTCDate(end.getUTCDate() - lagDays);
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - (lookbackDays - 1));
  return { startDate: isoDate(start), endDate: isoDate(end) };
}

function safeDiv(a, b) {
  return b > 0 ? a / b : 0;
}

function round(n, places) {
  const f = 10 ** places;
  return Math.round(n * f) / f;
}

function percentile(sortedAscending, p) {
  if (sortedAscending.length === 0) return 0;
  const idx = Math.min(sortedAscending.length - 1, Math.floor(p * sortedAscending.length));
  return sortedAscending[idx];
}

// Buckets by whole-number position, 1-20 individually, then "21-30" / "31+".
// Fine granularity in the 1-20 range is what lets us compare a given
// position-8-20 query against a same-position baseline instead of a vague
// site-wide average.
function positionBucketKey(position) {
  const p = Math.round(position);
  if (p <= 20) return String(Math.max(p, 1));
  if (p <= 30) return "21-30";
  return "31+";
}

// ---------------------------------------------------------------------
// Fetching (real mode)
// ---------------------------------------------------------------------

async function fetchAllRows(searchconsole, siteUrl, requestBodyBase) {
  const rows = [];
  let startRow = 0;
  for (;;) {
    let res;
    try {
      res = await searchconsole.searchanalytics.query({
        siteUrl,
        requestBody: { ...requestBodyBase, rowLimit: config.rowLimitPerPage, startRow },
      });
    } catch (err) {
      throw new ApiError(err);
    }
    const batch = res.data.rows || [];
    rows.push(...batch);
    if (batch.length < config.rowLimitPerPage || rows.length >= config.maxRows) break;
    startRow += config.rowLimitPerPage;
  }
  if (rows.length >= config.maxRows) {
    console.warn(
      `Hit GSC_MAX_ROWS=${config.maxRows} rows; results may be truncated. Raise GSC_MAX_ROWS if this site has more query/page combinations than that.`
    );
  }
  return rows;
}

class ApiError extends Error {
  constructor(original) {
    super(original.message);
    this.original = original;
  }
}

function explainApiError(err) {
  const status = err.original?.code || err.original?.response?.status;
  const apiMessage = err.original?.errors?.[0]?.message || err.original?.response?.data?.error?.message || err.message;

  if (status === 403) {
    return `
Search Console API returned 403 (permission denied): ${apiMessage}

The most common cause: the service account's email hasn't been added as a
user on this Search Console property yet. Fix:
  Search Console → Settings → Users and permissions → Add user
  → paste the service account's email (ends in .iam.gserviceaccount.com)
  → Restricted permission is enough (read-only).

Full steps: ${SETUP_DOC}
`;
  }
  if (status === 404) {
    return `
Search Console API returned 404 (not found): ${apiMessage}

GSC_SITE_URL="${config.siteUrlRaw}" probably doesn't match how the property
is registered. For a Domain property (recommended in ${PROPERTY_DOC}), it
must be exactly "sc-domain:wordwizai.com" — not the https:// URL.
`;
  }
  return `
Search Console API request failed: ${apiMessage}

If this persists, check the API is enabled and the key file is a valid
service-account key. Full steps: ${SETUP_DOC}
`;
}

async function fetchRealData(google) {
  if (!config.keyPath || !existsSync(config.keyPath) || !config.siteUrlRaw) {
    fail(missingSetupMessage());
  }

  const siteUrl = normalizeSiteUrl(config.siteUrlRaw);
  const { startDate, endDate } = computeDateRange(config);

  let auth, authClient;
  try {
    auth = new google.auth.GoogleAuth({ keyFile: config.keyPath, scopes: [SCOPE] });
    authClient = await auth.getClient();
  } catch (err) {
    fail(`
Couldn't authenticate with the service-account key at "${config.keyPath}".

${err.message}

Make sure this is the JSON key downloaded for the service account (Keys tab,
"Create new key" → JSON), not some other credentials file. See ${SETUP_DOC}.
`);
  }

  const searchconsole = google.searchconsole({ version: "v1", auth: authClient });

  console.log(`Site: ${siteUrl}`);
  console.log(`Date range: ${startDate} to ${endDate} (${config.lookbackDays} days, ${config.lagDays}-day lag)\n`);

  let queryPageRows, pageRows;
  try {
    console.log("Fetching query + page data...");
    queryPageRows = await fetchAllRows(searchconsole, siteUrl, {
      startDate,
      endDate,
      dimensions: ["query", "page"],
    });
    console.log(`  ${queryPageRows.length} rows\n`);

    console.log("Fetching page-level data...");
    pageRows = await fetchAllRows(searchconsole, siteUrl, {
      startDate,
      endDate,
      dimensions: ["page"],
    });
    console.log(`  ${pageRows.length} rows\n`);
  } catch (err) {
    if (err instanceof ApiError) fail(explainApiError(err));
    throw err;
  }

  return {
    siteUrl,
    dateRange: { startDate, endDate },
    queryPageRows: queryPageRows.map((r) => ({
      query: r.keys[0],
      page: r.keys[1],
      clicks: r.clicks,
      impressions: r.impressions,
      ctr: r.ctr,
      position: r.position,
    })),
    pageRows: pageRows.map((r) => ({
      page: r.keys[0],
      clicks: r.clicks,
      impressions: r.impressions,
      ctr: r.ctr,
      position: r.position,
    })),
  };
}

// ---------------------------------------------------------------------
// Synthetic sample data (--sample-data) — clearly fake, clearly labeled.
// Numbers are round/implausible on purpose so nobody mistakes this for a
// real report.
// ---------------------------------------------------------------------

function sampleData() {
  const { startDate, endDate } = computeDateRange(config);
  const queryPageRows = [
    // A genuine "improve the existing page" case: decent site-normal CTR
    // elsewhere at this position, this row is well below it.
    { query: "SAMPLE: how to teach cvc words", page: "https://wordwizai.com/guides/how-to-teach-cvc-words-to-struggling-readers", clicks: 4, impressions: 900, ctr: 4 / 900, position: 9.2 },
    { query: "SAMPLE: cvc words worksheet free", page: "https://wordwizai.com/guides/how-to-teach-cvc-words-to-struggling-readers", clicks: 2, impressions: 400, ctr: 2 / 400, position: 11.4 },
    // A "different intent, write a new page" case: comparison-shaped query
    // landing on a generic guide.
    { query: "SAMPLE: word wiz ai vs hooked on phonics", page: "https://wordwizai.com/guides/teaching-phonics-at-home", clicks: 3, impressions: 500, ctr: 3 / 500, position: 14.1 },
    // A well-performing row in the same band, used to establish a
    // realistic site-normal baseline so the anomalies above look anomalous.
    { query: "SAMPLE: phonics activities five year old", page: "https://wordwizai.com/guides/phonics-activities-5-year-old-struggling-reader", clicks: 60, impressions: 700, ctr: 60 / 700, position: 8.6 },
    { query: "SAMPLE: short vowel sounds practice", page: "https://wordwizai.com/guides/short-vowel-sounds-practice", clicks: 45, impressions: 650, ctr: 45 / 650, position: 10.9 },
    { query: "SAMPLE: silent e words list", page: "https://wordwizai.com/guides/silent-e-words-practice", clicks: 30, impressions: 550, ctr: 30 / 550, position: 12.3 },
    // Outside the 8-20 band entirely — should be excluded from opportunities.
    { query: "SAMPLE: word wiz ai reviews", page: "https://wordwizai.com/", clicks: 120, impressions: 300, ctr: 120 / 300, position: 2.1 },
  ];

  const pageRows = [
    // High impressions, terrible CTR relative to the rest of the site —
    // the page-level "title/meta problem" flag.
    { page: "https://wordwizai.com/comparisons/best-free-reading-apps", clicks: 8, impressions: 4000, ctr: 8 / 4000, position: 6.5 },
    { page: "https://wordwizai.com/guides/how-to-teach-cvc-words-to-struggling-readers", clicks: 25, impressions: 1500, ctr: 25 / 1500, position: 9.8 },
    { page: "https://wordwizai.com/guides/phonics-activities-5-year-old-struggling-reader", clicks: 60, impressions: 700, ctr: 60 / 700, position: 8.6 },
    { page: "https://wordwizai.com/guides/short-vowel-sounds-practice", clicks: 45, impressions: 650, ctr: 45 / 650, position: 10.9 },
    { page: "https://wordwizai.com/guides/silent-e-words-practice", clicks: 30, impressions: 550, ctr: 30 / 550, position: 12.3 },
    { page: "https://wordwizai.com/guides/teaching-phonics-at-home", clicks: 15, impressions: 900, ctr: 15 / 900, position: 13.5 },
    { page: "https://wordwizai.com/", clicks: 120, impressions: 300, ctr: 120 / 300, position: 2.1 },
  ];

  return {
    siteUrl: "sc-domain:wordwizai.com (SYNTHETIC — not a real query)",
    dateRange: { startDate, endDate },
    queryPageRows,
    pageRows,
  };
}

// ---------------------------------------------------------------------
// Scoring
// ---------------------------------------------------------------------

function buildPositionStats(queryPageRows) {
  const perPosition = new Map(); // bucketKey -> {clicks, impressions, count}
  let bandClicks = 0, bandImpressions = 0, bandCount = 0;
  let totalClicks = 0, totalImpressions = 0, totalCount = 0;

  for (const r of queryPageRows) {
    const key = positionBucketKey(r.position);
    const b = perPosition.get(key) || { clicks: 0, impressions: 0, count: 0 };
    b.clicks += r.clicks;
    b.impressions += r.impressions;
    b.count += 1;
    perPosition.set(key, b);

    if (r.position >= config.positionMin && r.position <= config.positionMax) {
      bandClicks += r.clicks;
      bandImpressions += r.impressions;
      bandCount += 1;
    }
    totalClicks += r.clicks;
    totalImpressions += r.impressions;
    totalCount += 1;
  }

  return {
    perPosition,
    band: { clicks: bandClicks, impressions: bandImpressions, count: bandCount, ctr: safeDiv(bandClicks, bandImpressions) },
    overall: { clicks: totalClicks, impressions: totalImpressions, count: totalCount, ctr: safeDiv(totalClicks, totalImpressions) },
  };
}

// Expected CTR is deliberately derived from this site's OWN data, not an
// external "average CTR by position" table. Those tables vary wildly by
// query type and are easy to misquote; a real, if small, same-site baseline
// is more honest and doesn't require asserting an unverifiable benchmark.
function expectedCtrFor(position, stats) {
  const exact = stats.perPosition.get(positionBucketKey(position));
  if (exact && exact.count >= config.minBucketSamples && exact.impressions > 0) {
    return { value: exact.clicks / exact.impressions, basis: `this site's own avg CTR at position ~${positionBucketKey(position)} (n=${exact.count})` };
  }
  if (stats.band.count >= config.minBucketSamples && stats.band.impressions > 0) {
    return { value: stats.band.ctr, basis: `this site's own avg CTR across positions ${config.positionMin}-${config.positionMax} (n=${stats.band.count})` };
  }
  if (stats.overall.impressions > 0) {
    return { value: stats.overall.ctr, basis: `this site's own overall avg CTR (n=${stats.overall.count}) — not enough position-specific data yet, treat as directional` };
  }
  return { value: null, basis: "insufficient data" };
}

function computeOpportunities(queryPageRows, stats) {
  const inBand = [];
  const opportunities = [];

  for (const r of queryPageRows) {
    if (r.position < config.positionMin || r.position > config.positionMax) continue;
    inBand.push(r);
    if (r.impressions < config.minImpressions) continue;

    const expected = expectedCtrFor(r.position, stats);
    if (expected.value == null) continue;

    const isLowCtr = r.ctr < expected.value * config.ctrAnomalyFactor;
    if (!isLowCtr) continue;

    opportunities.push({
      query: r.query,
      page: r.page,
      clicks: r.clicks,
      impressions: r.impressions,
      ctr: round(r.ctr, 4),
      position: round(r.position, 1),
      expectedCtr: round(expected.value, 4),
      expectedCtrBasis: expected.basis,
      estimatedClicksLeftOnTable: round(Math.max(expected.value - r.ctr, 0) * r.impressions, 1),
    });
  }

  opportunities.sort((a, b) => b.estimatedClicksLeftOnTable - a.estimatedClicksLeftOnTable);
  return { opportunities, queriesInBand: inBand.length };
}

function computeCtrProblemPages(pageRows) {
  const totalClicks = pageRows.reduce((s, r) => s + r.clicks, 0);
  const totalImpressions = pageRows.reduce((s, r) => s + r.impressions, 0);
  const siteCtr = safeDiv(totalClicks, totalImpressions);

  const impressionsSorted = pageRows.map((r) => r.impressions).sort((a, b) => a - b);
  const highImpressionThreshold = Math.max(percentile(impressionsSorted, 0.75), config.minImpressions);

  const flagged = [];
  if (siteCtr > 0) {
    for (const r of pageRows) {
      if (r.impressions < highImpressionThreshold) continue;
      if (r.ctr < siteCtr * config.pageCtrAnomalyFactor) {
        flagged.push({
          page: r.page,
          impressions: r.impressions,
          clicks: r.clicks,
          ctr: round(r.ctr, 4),
          avgPosition: round(r.position, 1),
          siteAvgCtr: round(siteCtr, 4),
          highImpressionThreshold: Math.round(highImpressionThreshold),
        });
      }
    }
  }

  flagged.sort((a, b) => b.impressions - a.impressions);
  return { flagged, siteCtr: round(siteCtr, 4), highImpressionThreshold: Math.round(highImpressionThreshold) };
}

// ---------------------------------------------------------------------
// Report writing
// ---------------------------------------------------------------------

function pct(n) {
  return `${round(n * 100, 2)}%`;
}

function buildReport({ siteUrl, dateRange, queryPageRows, pageRows }, synthetic) {
  const stats = buildPositionStats(queryPageRows);
  const { opportunities, queriesInBand } = computeOpportunities(queryPageRows, stats);
  const { flagged: ctrProblemPages, siteCtr, highImpressionThreshold } = computeCtrProblemPages(pageRows);

  const json = {
    generatedAt: new Date().toISOString(),
    synthetic,
    siteUrl,
    dateRange: { ...dateRange, lookbackDays: config.lookbackDays, lagDays: config.lagDays },
    config: {
      positionMin: config.positionMin,
      positionMax: config.positionMax,
      minImpressions: config.minImpressions,
      ctrAnomalyFactor: config.ctrAnomalyFactor,
      pageCtrAnomalyFactor: config.pageCtrAnomalyFactor,
      minBucketSamples: config.minBucketSamples,
    },
    summary: {
      totalQueryPageRows: queryPageRows.length,
      totalPageRows: pageRows.length,
      queriesInPositionBand: queriesInBand,
      opportunityCount: opportunities.length,
      ctrProblemPageCount: ctrProblemPages.length,
      siteAvgCtr: siteCtr,
      highImpressionThreshold,
    },
    opportunities,
    ctrProblemPages,
  };

  const md = renderMarkdown(json);
  return { json, md };
}

function renderMarkdown(report) {
  const lines = [];
  const banner = report.synthetic
    ? [
        "# ⚠️ SYNTHETIC SAMPLE DATA — NOT A REAL REPORT ⚠️",
        "",
        "Every row below was generated by `--sample-data` to preview the report's",
        "shape. None of it came from Search Console. Do not act on it, and do not",
        "paste it anywhere as if it were real traffic data.",
        "",
        "---",
        "",
      ]
    : [];

  lines.push(...banner);
  lines.push("# Search Console opportunity report", "");
  lines.push(`Generated: ${report.generatedAt}`);
  lines.push(`Site: ${report.siteUrl}`);
  lines.push(
    `Date range: ${report.dateRange.startDate} to ${report.dateRange.endDate} (${report.dateRange.lookbackDays} days, ${report.dateRange.lagDays}-day lag)`
  );
  lines.push("");
  lines.push("## Summary", "");
  lines.push(`- Query/page rows pulled: ${report.summary.totalQueryPageRows}`);
  lines.push(`- Page rows pulled: ${report.summary.totalPageRows}`);
  lines.push(
    `- Queries ranking at position ${report.config.positionMin}-${report.config.positionMax}: ${report.summary.queriesInPositionBand}`
  );
  lines.push(`- Of those, flagged as low-CTR opportunities: ${report.summary.opportunityCount}`);
  lines.push(`- Pages flagged as CTR problems (title/meta): ${report.summary.ctrProblemPageCount}`);
  lines.push(`- Site average CTR (all pages, full window): ${pct(report.summary.siteAvgCtr)}`);
  lines.push("");
  lines.push(
    `See growth/CONTENT_LOOP.md for how to act on this. Thresholds used: min impressions ${report.config.minImpressions}, ` +
      `CTR anomaly factor ${report.config.ctrAnomalyFactor} (query-level), ${report.config.pageCtrAnomalyFactor} (page-level).`
  );
  lines.push("");

  lines.push(
    `## Opportunities: queries at position ${report.config.positionMin}-${report.config.positionMax} with low CTR`,
    ""
  );
  if (report.opportunities.length === 0) {
    lines.push(
      "None found with the current thresholds. Either there isn't enough data yet, or nothing in this band is underperforming its own position's baseline right now — both are fine outcomes."
    );
  } else {
    lines.push(
      "| Query | Page | Position | Impressions | CTR | Expected CTR | Est. clicks left on table |",
      "|---|---|---|---|---|---|---|"
    );
    for (const o of report.opportunities.slice(0, config.topN)) {
      lines.push(
        `| ${o.query} | ${o.page} | ${o.position} | ${o.impressions} | ${pct(o.ctr)} | ${pct(o.expectedCtr)} | ${o.estimatedClicksLeftOnTable} |`
      );
    }
    if (report.opportunities.length > config.topN) {
      lines.push("", `_(${report.opportunities.length - config.topN} more in gsc-opportunities.json)_`);
    }
  }
  lines.push("");

  lines.push("## CTR problem pages (title/description rewrite candidates)", "");
  if (report.ctrProblemPages.length === 0) {
    lines.push("None found — no page's CTR is anomalously below the site average right now.");
  } else {
    lines.push(
      "| Page | Impressions | Clicks | CTR | Avg position | Site avg CTR |",
      "|---|---|---|---|---|---|"
    );
    for (const p of report.ctrProblemPages.slice(0, config.topN)) {
      lines.push(`| ${p.page} | ${p.impressions} | ${p.clicks} | ${pct(p.ctr)} | ${p.avgPosition} | ${pct(p.siteAvgCtr)} |`);
    }
  }
  lines.push("");

  return lines.join("\n");
}

// ---------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------

async function main() {
  let raw, synthetic;

  if (SAMPLE_MODE) {
    console.log("--sample-data: using synthetic data, no API calls, no credentials needed.\n");
    raw = sampleData();
    synthetic = true;
  } else {
    const google = await loadGoogleClient();
    raw = await fetchRealData(google);
    synthetic = false;
  }

  const { json, md } = buildReport(raw, synthetic);

  mkdirSync(config.outputDir, { recursive: true });
  const jsonName = synthetic ? "gsc-opportunities.sample.json" : "gsc-opportunities.json";
  const mdName = synthetic ? "gsc-opportunities.sample.md" : "gsc-opportunities.md";
  const jsonPath = join(config.outputDir, jsonName);
  const mdPath = join(config.outputDir, mdName);

  writeFileSync(jsonPath, JSON.stringify(json, null, 2) + "\n", "utf-8");
  writeFileSync(mdPath, md, "utf-8");

  console.log(`Wrote ${jsonPath}`);
  console.log(`Wrote ${mdPath}`);
  console.log(
    `\n${json.summary.opportunityCount} opportunities, ${json.summary.ctrProblemPageCount} CTR-problem pages. See ${PLAYBOOK_DOC} for next steps.`
  );
}

main().catch((err) => {
  if (process.env.DEBUG) {
    console.error(err);
  } else {
    console.error(`\ngsc-report.mjs failed: ${err.message}\n(Re-run with DEBUG=1 for the full stack trace.)\n`);
  }
  process.exit(1);
});
