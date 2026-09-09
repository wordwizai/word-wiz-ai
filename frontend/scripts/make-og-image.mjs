/**
 * Render public/og-image.png (1200x630), the social preview card.
 *
 * Regenerate with:  npm run og:image
 *
 * Built from the real design system rather than an invented one:
 *   - Poppins, the app's --font-heading / --font-body
 *   - Charis SIL, the app's --font-ipa, used for the phoneme chips
 *   - The oklch tokens from src/index.css, written as oklch() directly since
 *     this renders in Chrome
 *   - public/wordwizIcon.svg, read from disk so the logo can never drift
 *   - Card treatment from STYLE_GUIDELINES.md: rounded-3xl, white-to-purple
 *     gradient, 2px purple border, soft shadow
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
    /* Tokens copied from src/index.css (light mode). */
    --background: oklch(0.98 0.01 280);
    --foreground: oklch(0.2 0.02 280);
    --primary: oklch(0.55 0.18 280);
    --muted-foreground: oklch(0.45 0.02 280);
    --pastel-purple: oklch(0.95 0.05 280);
    --pastel-pink: oklch(0.95 0.05 340);

    /* Literal hexes from wordwizIcon.svg, so the card matches the mark. */
    --logo-purple-deep: #602195;
    --logo-purple: #7A32B3;
    --logo-gold: #F0B44A;
    --logo-gold-light: #F8CA68;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    width: 1200px; height: 630px;
    font-family: "Poppins", system-ui, sans-serif;
    background:
      radial-gradient(900px 520px at 88% 8%, var(--pastel-pink) 0%, transparent 62%),
      linear-gradient(135deg, #ffffff 0%, var(--pastel-purple) 100%);
    position: relative; overflow: hidden;
    display: flex; flex-direction: column;
  }

  /* Gold sparkles echoing the four stars in the logo. */
  .sparkle { position: absolute; color: var(--logo-gold-light); line-height: 1; }
  .s1 { top: 58px;  right: 322px; font-size: 26px; opacity: .85; }
  .s2 { top: 470px; right: 92px;  font-size: 34px; opacity: .55; }
  .s3 { bottom: 84px; left: 560px; font-size: 20px; opacity: .5; }

  .brand {
    position: absolute; top: 48px; left: 72px;
    display: flex; align-items: center; gap: 16px;
  }
  .brand svg { width: 62px; height: 54px; display: block; }
  .brand-name {
    font-size: 30px; font-weight: 700; letter-spacing: -0.02em;
    color: var(--logo-purple-deep);
  }

  .body {
    flex: 1; padding: 132px 72px 0;
    display: flex; flex-direction: column; justify-content: center;
  }

  h1 {
    font-weight: 700; font-size: 56px; line-height: 1.12;
    letter-spacing: -0.03em; color: var(--foreground); max-width: 640px;
  }
  /* The gradient-text treatment used on the app's own headings. */
  h1 em {
    font-style: normal;
    background: linear-gradient(90deg, var(--primary) 0%, var(--logo-purple) 55%, oklch(0.62 0.19 340) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }

  .sub {
    margin-top: 20px; font-size: 23px; font-weight: 400; line-height: 1.45;
    color: var(--muted-foreground); max-width: 600px;
  }

  /* Card treatment straight from STYLE_GUIDELINES.md. */
  .demo {
    position: absolute; right: 72px; top: 50%; transform: translateY(-44%);
    width: 348px; padding: 30px 32px;
    border-radius: 30px;
    background: linear-gradient(to bottom right, #ffffff, color-mix(in oklab, var(--pastel-purple) 60%, white));
    border: 2px solid color-mix(in oklab, var(--primary) 18%, white);
    box-shadow: 0 22px 45px -14px color-mix(in oklab, var(--primary) 32%, transparent);
  }
  .demo-label {
    font-size: 12px; font-weight: 600; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--primary); margin-bottom: 16px;
  }
  .demo-word {
    font-size: 42px; font-weight: 600; color: var(--foreground);
    margin-bottom: 18px; letter-spacing: -0.01em;
  }
  .phonemes { display: flex; gap: 9px; }
  .ph {
    font-family: "Charis SIL", Georgia, serif; font-size: 24px;
    padding: 9px 15px; border-radius: 14px;
    background: color-mix(in oklab, var(--pastel-purple) 80%, white);
    color: var(--logo-purple-deep);
  }
  .ph.wrong {
    background: color-mix(in oklab, var(--logo-gold) 26%, white);
    border: 2px solid var(--logo-gold);
    color: #8a5a08;
  }
  .demo-note {
    margin-top: 18px; font-size: 16px; color: var(--muted-foreground); line-height: 1.45;
  }
  .demo-note b { font-family: "Charis SIL", Georgia, serif; color: var(--logo-purple-deep); font-weight: 700; }

  .footer { padding: 0 72px 48px; display: flex; align-items: center; gap: 12px; }
  .pill {
    font-size: 17px; font-weight: 500; padding: 10px 20px; border-radius: 999px;
    background: color-mix(in oklab, var(--primary) 12%, white);
    color: var(--primary);
  }
  .pill.gold {
    background: color-mix(in oklab, var(--logo-gold) 24%, white);
    color: #8a5a08;
  }
  .url {
    margin-left: auto; font-size: 20px; font-weight: 600;
    color: color-mix(in oklab, var(--primary) 70%, white);
  }
</style>
</head>
<body>
  <span class="sparkle s1">✦</span>
  <span class="sparkle s2">✦</span>
  <span class="sparkle s3">✦</span>

  <div class="brand">
    ${logoSvg}
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
    <span class="pill">Free forever</span>
    <span class="pill">No ads</span>
    <span class="pill gold">Ages 5–8</span>
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
