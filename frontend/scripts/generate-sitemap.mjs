import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DOMAIN = "https://wordwizai.com";

// All routes to include in sitemap
const routes = [
  { path: "/", priority: 1.0, changefreq: "weekly" },
  { path: "/about", priority: 0.8, changefreq: "monthly" },
  { path: "/contact", priority: 0.7, changefreq: "monthly" },
  { path: "/privacy", priority: 0.5, changefreq: "yearly" },

  // Comparison pages
  {
    path: "/comparisons/wordly-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/reading-eggs-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/starfall-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/abcmouse-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/raz-kids-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/hooked-on-phonics-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/epic-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/lexia-core5-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/iready-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/teach-your-monster-to-read-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/comparisons/fundations-vs-word-wiz-ai",
    priority: 0.9,
    changefreq: "monthly",
  },

  // Article pages
  {
    path: "/articles/best-phonics-apps-kids-2025",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/articles/dyslexia-reading-apps",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/articles/how-ai-personalizes-reading-instruction",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/articles/phonemic-awareness-activities-for-struggling-readers",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/articles/science-of-reading-explained",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/articles/structured-literacy-vs-balanced-literacy",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/articles/teaching-reading-at-home-parent-guide",
    priority: 0.9,
    changefreq: "monthly",
  },

  // Guide pages
  {
    path: "/guides/cvc-words-complete-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/decodable-books-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/decodable-texts-educators-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/five-minute-reading-practice-activities-kids",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/high-frequency-words-complete-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/how-to-help-child-learn-read",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/orton-gillingham-approach-complete-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/phoneme-awareness-complete-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/phoneme-segmentation-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/phonics-rules-patterns-complete-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/guides/reading-fluency-complete-guide",
    priority: 0.9,
    changefreq: "monthly",
  },
  { path: "/guides/sight-words-guide", priority: 0.9, changefreq: "monthly" },
];

function generateSitemap() {
  const now = new Date().toISOString();

  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

  routes.forEach(({ path, priority, changefreq }) => {
    // Point to regular app URLs - React app handles them with react-helmet-async
    xml += "  <url>\n";
    xml += `    <loc>${DOMAIN}${path}</loc>\n`;
    xml += `    <lastmod>${now}</lastmod>\n`;
    xml += `    <changefreq>${changefreq}</changefreq>\n`;
    xml += `    <priority>${priority}</priority>\n`;
    xml += "  </url>\n";
  });

  xml += "</urlset>";

  return xml;
}

// Write sitemap to public directory
const publicDir = path.join(__dirname, "..", "public");
const sitemapPath = path.join(publicDir, "sitemap.xml");

const sitemap = generateSitemap();
fs.writeFileSync(sitemapPath, sitemap, "utf-8");

console.log(`✅ Generated sitemap with ${routes.length} URLs`);
console.log(`📝 Written to: ${sitemapPath}`);
