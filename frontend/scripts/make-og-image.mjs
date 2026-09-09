/**
 * Render public/og-image.png (1200x630), the social preview card.
 *
 * Regenerate with:  npm run og:image
 *
 * Deliberately flat: one solid brand purple ground, no gradients, no
 * decorative flourishes. The colour comes from the logo's own hexes, the
 * type is the app's Poppins, and the phoneme chips use the app's Charis SIL.
 * The only "designed" element is the analysis card, because that is the one
 * thing about this product a generic screenshot would not convey.
 */

import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = join(__dirname, "..", "public");
const outputPath = join(publicDir, "og-image.png");

// Inlined rather than <img src> so the SVG renders without a file:// fetch.
const logoSvg = readFileSync(join(publicDir, "wordwizIcon.svg"), "utf-8");

const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Charis+SIL:wght@400;700&display=swap">
<style>
  :root {
    /* Literal hexes from wordwizIcon.svg. */
    --purple-deep: #602195;
    --purple: #7A32B3;
    --gold: #F0B44A;
    --gold-light: #F8CA68;
    --ink: #1c1020;
    --slate: #5c5566;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    width: 1200px; height: 630px;
    font-family: "Poppins", system-ui, sans-serif;
    background: var(--purple-deep);
    display: flex; flex-direction: column;
    position: relative;
  }

  /* A single flat gold rule, the one accent on the card. */
  .rule { height: 8px; background: var(--gold); }

  .brand {
    position: absolute; top: 52px; left: 76px;
    display: flex; align-items: center; gap: 16px;
  }
  .chip {
    width: 68px; height: 68px; border-radius: 18px; background: #ffffff;
    display: flex; align-items: center; justify-content: center;
  }
  .chip svg { width: 46px; height: 40px; display: block; }
  .brand-name {
    font-size: 29px; font-weight: 600; letter-spacing: -0.01em; color: #ffffff;
  }

  .body {
    flex: 1; padding: 150px 76px 0;
    display: flex; flex-direction: column; justify-content: center;
  }

  h1 {
    font-weight: 700; font-size: 56px; line-height: 1.12;
    letter-spacing: -0.03em; color: #ffffff; max-width: 620px;
  }
  h1 em { font-style: normal; color: var(--gold-light); }

  .sub {
    margin-top: 22px; font-size: 23px; font-weight: 400; line-height: 1.45;
    color: #d6c6e8; max-width: 580px;
  }

  .demo {
    position: absolute; right: 76px; top: 50%; transform: translateY(-44%);
    width: 350px; padding: 30px 32px;
    border-radius: 22px; background: #ffffff;
  }
  .demo-label {
    font-size: 12px; font-weight: 600; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--purple); margin-bottom: 16px;
  }
  .demo-word {
    font-size: 42px; font-weight: 600; color: var(--ink);
    margin-bottom: 18px; letter-spacing: -0.01em;
  }
  .phonemes { display: flex; gap: 9px; }
  .ph {
    font-family: "Charis SIL", Georgia, serif; font-size: 24px;
    padding: 9px 15px; border-radius: 10px;
    background: #f1edf6; color: var(--purple-deep);
  }
  .ph.wrong { background: var(--gold); color: #4a3000; font-weight: 700; }
  .demo-note {
    margin-top: 18px; font-size: 16px; color: var(--slate); line-height: 1.45;
  }
  .demo-note b {
    font-family: "Charis SIL", Georgia, serif;
    color: var(--purple-deep); font-weight: 700;
  }

  .footer {
    padding: 0 76px 50px;
    display: flex; align-items: baseline; gap: 14px;
    font-size: 19px; color: #c3b0d8;
  }
  .footer .dot { color: #8e6fb0; }
  .url { margin-left: auto; font-weight: 600; color: #ffffff; }
</style>
</head>
<body>
  <div class="rule"></div>

  <div class="brand">
    <span class="chip">${logoSvg}</span>
    <span class="brand-name">Word Wiz AI</span>
  </div>

  <div class="body">
    <h1>A reading tutor that hears <em>every sound</em></h1>
    <p class="sub">Your child reads out loud. It finds the exact sound they missed.</p>
  </div>

  <div class="demo">
    <div class="demo-label">Phoneme analysis</div>
    <div class="demo-word">think</div>
    <div class="phonemes">
      <span class="ph wrong">f</span>
      <span class="ph">ɪ</span>
      <span class="ph">ŋ</span>
      <span class="ph">k</span>
    </div>
    <div class="demo-note">The <b>/θ/</b> came out as <b>/f/</b></div>
  </div>

  <div class="footer">
    <span>Free forever</span>
    <span class="dot">·</span>
    <span>No ads</span>
    <span class="dot">·</span>
    <span>Ages 5–8</span>
    <span class="url">wordwizai.com</span>
  </div>
</body>
</html>`;

const { default: puppeteer } = await import("puppeteer");

const browser = await puppeteer.launch({
  headless: "new",
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
await page.setContent(html, { waitUntil: "networkidle0" });

// Webfonts load over the network; without this the card can silently render
// in a fallback face.
await page.evaluateHandle("document.fonts.ready");

const png = await page.screenshot({ type: "png" });
writeFileSync(outputPath, png);

await browser.close();

console.log(`Wrote ${outputPath} (${(png.length / 1024).toFixed(1)}kb, 1200x630)`);
