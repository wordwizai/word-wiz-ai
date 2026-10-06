// Builds the free "Magic E Sentences" printable (2 pages, US Letter) from the
// sentences and word lists on the silent-e guide. Run from frontend/ (needs
// its puppeteer): node ../growth-agent/assets/printable-src/make-magic-e.mjs <outdir>
// qr.svg encodes https://wordwizai.com/try/a-e-magic-e (python-qrcode 8.0).
import { readFileSync, writeFileSync } from "fs";
import { createRequire } from "module";
const require = createRequire("/home/user/word-wiz-ai/frontend/package.json");
const puppeteer = require("puppeteer");
const out = process.argv[2];
const here = new URL(".", import.meta.url).pathname;
const qr = readFileSync(here + "qr.svg", "utf-8").replace(/<\?xml[^>]*>/, "");
const logo = readFileSync("/home/user/word-wiz-ai/frontend/public/wordwizIcon.svg", "utf-8");

const sets = [
  ["Long A", "a_e", ["Dave gave the cake to Jane.", "We made a game with a red cape.", "Kate can skate on the lake.", "The snake hid in the cave.", "Shane ate a grape on the plate."]],
  ["Long I", "i_e", ["Mike will ride his bike.", "I like the white kite.", "Nine kids hide in the vines.", "Tim has a fine time on the slide.", "Spike the dog can dive and swim."]],
  ["Long O", "o_e", ["The dog dug up a bone at home.", "I hope the stone is in the hole.", "Rose rode to the pond with Mom.", "We drove home in the fog.", "The mole dug a hole in the slope."]],
  ["Long U", "u_e", ["June has a cute pet mule.", "Luke can hum a tune.", "The cube is in the tube.", "Duke dug up a huge rock.", "We must use the rule."]],
];
const words = {
  a_e: "cake, make, take, bake, lake, wake, came, game, name, same, tame, cave, gave, save, wave, gate, late, rate, cape, tape",
  i_e: "bike, hike, like, five, dive, hive, hide, ride, side, wide, time, dime, line, nine, pine, vine, kite, bite, site",
  o_e: "bone, cone, home, hope, rope, nose, rose, code, mode, rode, hole, mole, pole, poke, joke, woke, zone",
  u_e: "cube, tube, cute, huge, mule, rule, dune, tune, duke, Luke, rude, dude",
};
const pairs = [["cap", "cape"], ["mad", "made"], ["kit", "kite"], ["pin", "pine"], ["hop", "hope"], ["rob", "robe"], ["cub", "cube"], ["tub", "tube"]];
// Bold the magic e words: vowel, one consonant, final e (plus plural s).
const bold = (s) => s.replace(/\b([A-Za-z]*[aeiou][b-df-hj-np-tv-z]es?)\b/g, (m) => (/^(the)$/i.test(m) ? m : `<b>${m}</b>`));

const footer = `
  <div class="foot">
    <div class="qr">${qr}</div>
    <div class="foot-text">
      <div class="foot-title">Want to hear which sounds your child misses?</div>
      <div>Scan the code (or go to <b>wordwizai.com/try</b>) and have them read three sentences out loud to Word Wiz AI. It shows which sounds came out wrong. It's free, there's no account needed, and nothing is saved.</div>
    </div>
  </div>`;
const brand = `<div class="brand"><span class="chip">${logo}</span><span>Word Wiz AI</span></div>`;

const html = `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Andika:wght@400;700&display=swap">
<style>
@page { size: Letter; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --purple: #602195; --purple-2: #7A32B3; --gold: #F0B44A; --soft: #f3eefa; --ink: #1c1020; --slate: #5c5566; }
body { font-family: "Poppins", system-ui, sans-serif; color: var(--ink); }
.page { width: 8.5in; height: 11in; padding: 0.55in 0.6in 0.5in; display: flex; flex-direction: column; page-break-after: always; position: relative; }
.page:last-child { page-break-after: auto; }
.top { display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid var(--gold); padding-bottom: 10px; }
.brand { display: flex; align-items: center; gap: 8px; font-weight: 600; color: var(--purple); font-size: 14px; }
.chip { width: 30px; height: 30px; border-radius: 8px; background: var(--soft); display: flex; align-items: center; justify-content: center; }
.chip svg { width: 22px; height: 19px; }
.name { font-size: 12px; color: var(--slate); }
h1 { margin-top: 18px; font-size: 34px; line-height: 1.1; color: var(--purple); letter-spacing: -0.02em; }
.sub { margin-top: 6px; font-size: 14px; color: var(--slate); line-height: 1.45; }
.sets { margin-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; flex: 1; align-content: start; }
.set { border: 2px solid #e4dcf0; border-radius: 14px; padding: 12px 12px; }
.set h2 { font-size: 16px; color: var(--purple); display: flex; justify-content: space-between; align-items: baseline; }
.set h2 span { font-family: "Andika", sans-serif; font-size: 15px; background: var(--gold); color: #3a2400; border-radius: 6px; padding: 1px 8px; }
ol { margin-top: 8px; list-style: none; counter-reset: n; }
li { font-family: "Andika", "Comic Sans MS", sans-serif; font-size: 17px; line-height: 1.35; padding: 13px 0 13px 28px; position: relative; counter-increment: n; border-bottom: 1px dashed #e4dcf0; }
li:last-child { border-bottom: none; }
li::before { content: ""; position: absolute; left: 2px; top: 16px; width: 15px; height: 15px; border: 2px solid var(--purple-2); border-radius: 4px; }
li b { color: var(--purple); }
.foot { margin-top: 14px; display: flex; gap: 14px; align-items: center; background: var(--soft); border-radius: 14px; padding: 12px 14px; }
.qr { width: 1.05in; height: 1.05in; background: #fff; padding: 4px; border-radius: 8px; flex: none; }
.qr svg { width: 100%; height: 100%; display: block; }
.foot-text { font-size: 12.5px; line-height: 1.45; color: var(--ink); }
.foot-title { font-weight: 700; color: var(--purple); font-size: 14px; margin-bottom: 2px; }
.cols { margin-top: 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.wl { border: 2px solid #e4dcf0; border-radius: 14px; padding: 10px 14px; }
.wl h3 { font-size: 14px; color: var(--purple); }
.wl p { font-family: "Andika", sans-serif; font-size: 17.5px; line-height: 1.65; margin-top: 4px; }
.pairs { margin-top: 14px; border: 2px solid #e4dcf0; border-radius: 14px; padding: 10px 14px; }
.pairs h3 { font-size: 14px; color: var(--purple); }
.pair-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px 10px; margin-top: 6px; font-family: "Andika", sans-serif; font-size: 18px; }
.pair-grid div b { color: var(--purple); }
.how { margin-top: 22px; }
.how h3 { font-size: 14px; color: var(--purple); }
.how ol li { font-family: "Poppins", sans-serif; font-size: 13px; line-height: 1.45; padding: 3px 0 3px 26px; border: none; }
.how ol li::before { content: counter(n); border: none; background: var(--gold); color: #3a2400; border-radius: 50%; width: 18px; height: 18px; top: 4px; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.spacer { flex: 1; }
.small { margin-top: 8px; font-size: 10.5px; color: var(--slate); text-align: center; }
</style></head><body>
<section class="page">
  <div class="top">${brand}<div class="name">Name ____________________</div></div>
  <h1>Magic E Sentences</h1>
  <p class="sub">20 sentences to read out loud, one long vowel at a time. Each set sticks to one vowel, and apart from the magic e words (in bold), every word is a short-vowel word or a common sight word like the, a, to, is, I or we. Check the box after each one.</p>
  <div class="sets">
    ${sets.map(([title, pat, ss]) => `<div class="set"><h2>${title} <span>${pat}</span></h2><ol>${ss.map((s) => `<li>${bold(s)}</li>`).join("")}</ol></div>`).join("")}
  </div>
  ${footer}
</section>
<section class="page">
  <div class="top">${brand}<div class="name">Magic E Sentences, page 2</div></div>
  <h1>Warm-up words</h1>
  <p class="sub">Read the words for one vowel before its sentences.</p>
  <div class="pairs">
    <h3>Add the magic e</h3>
    <div class="pair-grid">${pairs.map(([a, b]) => `<div>${a} &rarr; <b>${b}</b></div>`).join("")}</div>
  </div>
  <div class="cols">
    ${sets.map(([title, pat]) => `<div class="wl"><h3>${title} (${pat})</h3><p>${words[pat]}</p></div>`).join("")}
  </div>
  <div class="how">
    <h3>How to use this sheet</h3>
    <ol>
      <li>Pick one vowel. Have your child read its warm-up words, then its five sentences.</li>
      <li>If they read a magic e word with a short vowel (like "cap" for "cape"), point to the e at the end and have them try it again.</li>
      <li>Stay on one vowel a day until it feels easy, then mix the sets.</li>
    </ol>
  </div>
  <div class="spacer"></div>
  ${footer}
  <p class="small">Free to print and share. Made by Word Wiz AI, a free reading tutor built by a high school student. More magic e words at wordwizai.com/guides/silent-e-words-practice-for-kids</p>
</section>
</body></html>`;

writeFileSync(out + "/magic-e-sentences.html", html);
const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox", "--disable-setuid-sandbox"] });
const page = await browser.newPage();
await page.setViewport({ width: 816, height: 1056, deviceScaleFactor: 1.5 });
await page.setContent(html, { waitUntil: "networkidle0", timeout: 60000 });
await page.evaluateHandle("document.fonts.ready");
await page.pdf({ path: out + "/magic-e-sentences.pdf", format: "Letter", printBackground: true });
const pages = await page.$$("section.page");
for (let i = 0; i < pages.length; i++) await pages[i].screenshot({ path: `${out}/preview-${i + 1}.png` });
const overflow = await page.evaluate(() => [...document.querySelectorAll("section.page")].map((p) => p.scrollHeight - p.clientHeight));
console.log("overflow px per page:", overflow.join(", "));
await browser.close();
