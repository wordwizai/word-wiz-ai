import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import puppeteer from "puppeteer";
import { createServer } from "vite";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// SEO routes to prerender for bots
const routes = [
  // Core pages
  "/",
  "/about",
  "/contact",
  "/privacy",

  // Comparison pages (11)
  "/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai",
  "/comparisons/reading-eggs-vs-starfall-vs-word-wiz-ai",
  "/comparisons/homer-vs-khan-academy-kids-vs-word-wiz-ai",
  "/comparisons/hooked-on-phonics-vs-word-wiz-ai",
  "/comparisons/best-free-reading-apps",
  "/comparisons/lexia-vs-raz-kids-vs-word-wiz-ai",
  "/comparisons/teach-your-monster-vs-abcya-vs-word-wiz-ai",
  "/comparisons/ixl-vs-duolingo-abc-vs-word-wiz-ai",
  "/comparisons/reading-tutor-vs-reading-app",
  "/comparisons/ai-reading-app-vs-traditional-phonics-program",
  "/comparisons/free-phonics-apps-vs-paid-reading-programs",

  // Article pages (7)
  "/articles/why-child-hates-reading",
  "/articles/child-pronounces-words-wrong",
  "/articles/decodable-books-vs-leveled-readers",
  "/articles/child-cant-blend-sounds-into-words",
  "/articles/kindergartener-guesses-words-instead-sounding-out",
  "/articles/child-reads-slowly-struggles-with-fluency",
  "/articles/first-grader-skips-words-when-reading-aloud",

  // Guide pages (12)
  "/guides/how-to-choose-reading-app",
  "/guides/how-to-teach-phonics-at-home",
  "/guides/is-teacher-teaching-enough-phonics",
  "/guides/phoneme-awareness-complete-guide",
  "/guides/how-to-teach-cvc-words-to-struggling-readers",
  "/guides/teaching-consonant-blends-kindergarten-at-home",
  "/guides/daily-phonics-practice-routine-kindergarten-at-home",
  "/guides/short-vowel-sounds-exercises-beginning-readers",
  "/guides/decodable-sentences-for-beginning-readers",
  "/guides/five-minute-reading-practice-activities-kids",
  "/guides/r-controlled-vowels-teaching-strategies-parents",
  "/guides/phonics-practice-without-worksheets-kindergarten",
];

const seoPath = join(__dirname, "..", "public", "seo");

// Extract text content and meta tags for SEO
async function extractSEOContent(page) {
  return await page.evaluate(() => {
    // Get meta tags
    const getMetaContent = (selector) => {
      const meta = document.querySelector(selector);
      return meta ? meta.getAttribute("content") || "" : "";
    };

    const title = document.title || "";
    const description = getMetaContent('meta[name="description"]');
    const ogTitle = getMetaContent('meta[property="og:title"]') || title;
    const ogDescription =
      getMetaContent('meta[property="og:description"]') || description;
    const ogImage = getMetaContent('meta[property="og:image"]');
    const ogUrl = getMetaContent('meta[property="og:url"]');
    const canonical =
      document.querySelector('link[rel="canonical"]')?.getAttribute("href") ||
      ogUrl;

    // Extract ALL links for crawlability (header, nav, footer, sidebar, main content)
    const allLinks = [];
    document.querySelectorAll("a[href]").forEach((link) => {
      const href = link.getAttribute("href");
      const text = link.textContent.trim();
      // Only include internal links
      if (href && text && (href.startsWith("/") || href.startsWith("#"))) {
        allLinks.push({ href, text });
      }
    });

    // Get full HTML structure from body for better content extraction
    const bodyContent = document.body.cloneNode(true);

    // Remove scripts, styles, and hidden elements
    bodyContent
      .querySelectorAll(
        'script, style, [style*="display: none"], [style*="display:none"], .hidden'
      )
      .forEach((el) => el.remove());

    // Extract structured content from main
    const mainElement = document.querySelector("main") || document.body;
    const h1 = mainElement.querySelector("h1");
    const heading = h1 ? h1.textContent.trim() : title;

    // Get all meaningful content with structure preserved
    const contentElements = [];
    mainElement
      .querySelectorAll(
        "h1, h2, h3, h4, p, li, a, blockquote, table, strong, em"
      )
      .forEach((el) => {
        const text = el.textContent.trim();
        const tag = el.tagName.toLowerCase();

        if (text.length > 0) {
          const data = { tag, text };

          // Preserve link hrefs
          if (tag === "a") {
            const href = el.getAttribute("href");
            if (href) data.href = href;
          }

          contentElements.push(data);
        }
      });

    return {
      title,
      description,
      ogTitle,
      ogDescription,
      ogImage,
      ogUrl,
      canonical,
      heading,
      contentElements,
      allLinks, // All links from entire page for crawlability
    };
  });
}

function createSEOHTML(data) {
  // Deduplicate all links
  const uniqueLinks = [
    ...new Map(data.allLinks.map((l) => [l.href, l])).values(),
  ];

  // Build links section for crawlability
  let linksHTML = "";
  if (uniqueLinks.length > 0) {
    linksHTML = `\n  <nav aria-label="Site navigation">\n    <ul>\n`;
    uniqueLinks.forEach(({ href, text }) => {
      const escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
      linksHTML += `      <li><a href="${href}">${escaped}</a></li>\n`;
    });
    linksHTML += `    </ul>\n  </nav>\n`;
  }

  // Build content HTML preserving structure and links
  let contentHTML = "";
  let currentList = null;

  data.contentElements.forEach(({ tag, text, href }) => {
    const escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");

    // Handle lists properly
    if (tag === "li") {
      if (!currentList) {
        contentHTML += `    <ul>\n`;
        currentList = true;
      }
      contentHTML += `      <li>${escaped}</li>\n`;
    } else {
      if (currentList) {
        contentHTML += `    </ul>\n`;
        currentList = null;
      }

      if (tag === "h1") {
        // Skip h1 as it's already in the heading
      } else if (tag === "h2") {
        contentHTML += `    <h2>${escaped}</h2>\n`;
      } else if (tag === "h3") {
        contentHTML += `    <h3>${escaped}</h3>\n`;
      } else if (tag === "h4") {
        contentHTML += `    <h4>${escaped}</h4>\n`;
      } else if (tag === "a" && href) {
        contentHTML += `    <p><a href="${href}">${escaped}</a></p>\n`;
      } else if (tag === "blockquote") {
        contentHTML += `    <blockquote>${escaped}</blockquote>\n`;
      } else if (tag === "strong" || tag === "em") {
        // Include in context, already captured by parent elements
      } else {
        contentHTML += `    <p>${escaped}</p>\n`;
      }
    }
  });

  // Close any open list
  if (currentList) {
    contentHTML += `    </ul>\n`;
  }

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${data.title}</title>
  <meta name="description" content="${data.description}">
  <meta property="og:title" content="${data.ogTitle}">
  <meta property="og:description" content="${data.ogDescription}">
  ${data.ogImage ? `<meta property="og:image" content="${data.ogImage}">` : ""}
  ${data.ogUrl ? `<meta property="og:url" content="${data.ogUrl}">` : ""}
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${data.ogTitle}">
  <meta name="twitter:description" content="${data.ogDescription}">
  ${data.ogImage ? `<meta name="twitter:image" content="${data.ogImage}">` : ""}
  <meta name="robots" content="index, follow">
  ${data.canonical ? `<link rel="canonical" href="${data.canonical}">` : ""}
</head>
<body>
  <main>
    <h1>${data.heading}</h1>
${contentHTML}
  </main>${linksHTML}
  <script>
    // Redirect real users to the full app
    if (!/bot|crawler|spider|crawling/i.test(navigator.userAgent)) {
      window.location.href = window.location.pathname;
    }
  </script>
</body>
</html>`;
}

async function prerenderSEO(page, route, baseUrl) {
  try {
    const url = `${baseUrl}${route}`;
    await page.goto(url, {
      waitUntil: "domcontentloaded",
      timeout: 10000,
    });

    // Wait for react-helmet-async to update the title
    // The title changing indicates Helmet has rendered
    await page.waitForFunction(
      (defaultTitle) => {
        return document.title !== defaultTitle;
      },
      { timeout: 3000 },
      "Word Wiz AI - Free AI Reading Tutor for Kids | Learn Phonics & Pronunciation"
    ).catch(() => {
      // If title doesn't change (homepage), just wait
      return new Promise((resolve) => setTimeout(resolve, 800));
    });

    // Extra 200ms for meta tags to finish updating
    await new Promise((resolve) => setTimeout(resolve, 200));

    const seoData = await extractSEOContent(page);
    const seoHtml = createSEOHTML(seoData);

    // Determine output path
    const outputPath =
      route === "/"
        ? join(seoPath, "index.html")
        : join(seoPath, route, "index.html");

    const outputDir = dirname(outputPath);
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true });
    }

    writeFileSync(outputPath, seoHtml, "utf-8");
    console.log(`  ✓ ${route}`);
    return { success: true, route };
  } catch (error) {
    console.error(`  ❌ ${route}: ${error.message}`);
    return { success: false, route, error: error.message };
  }
}

async function prerenderSEOPages() {
  const startTime = Date.now();
  console.log("🤖 Starting SEO prerender for bots...\n");

  const browser = await puppeteer.launch({
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
    ],
  });

  try {
    console.log("📦 Building production files...");
    const { build } = await import("vite");
    await build();

    console.log("📦 Starting preview server...");
    const { preview } = await import("vite");
    const previewServer = await preview({
      preview: {
        port: 4173,
      },
    });
    const baseUrl = "http://localhost:4173";
    console.log(`✓ Preview server running at ${baseUrl}\n`);

    console.log(`📄 Prerendering ${routes.length} routes for SEO...\n`);

    const page = await browser.newPage();

    // Block unnecessary resources
    await page.setRequestInterception(true);
    page.on("request", (request) => {
      const resourceType = request.resourceType();
      if (["image", "stylesheet", "font", "media"].includes(resourceType)) {
        request.abort();
      } else {
        request.continue();
      }
    });

    const results = [];
    for (const route of routes) {
      const result = await prerenderSEO(page, route, baseUrl);
      results.push(result);
    }

    await page.close();
    await browser.close();
    await previewServer.close();

    const successful = results.filter((r) => r.success).length;
    const failed = results.filter((r) => !r.success).length;
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    console.log(`\n✅ SEO prerender complete in ${duration}s!`);
    console.log(
      `📊 ${successful} successful, ${failed} failed out of ${routes.length} routes`
    );

    if (failed > 0) {
      console.log("\n❌ Failed routes:");
      results
        .filter((r) => !r.success)
        .forEach((r) => console.log(`  - ${r.route}: ${r.error}`));
      process.exit(1);
    }
  } catch (error) {
    console.error("❌ Prerender failed:", error);
    await browser.close();
    process.exit(1);
  }
}

prerenderSEOPages();
