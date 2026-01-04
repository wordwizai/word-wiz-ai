import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createServer } from "vite";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Routes to prerender - All static SEO pages
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

const distPath = join(__dirname, "..", "dist");

// Process and save HTML for a route
function processAndSaveHTML(html, route) {
  // Determine output path
  const outputPath =
    route === "/"
      ? join(distPath, "index.html")
      : join(distPath, route, "index.html");

  // Create directory if it doesn't exist
  const outputDir = dirname(outputPath);
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  // Process HTML for nested routes
  let processedHtml = html;

  if (route !== "/") {
    const depth = route.split("/").filter((p) => p).length;
    const prefix = "../".repeat(depth);

    processedHtml = html
      .replace(/href="\/assets\//g, `href="${prefix}assets/`)
      .replace(/src="\/assets\//g, `src="${prefix}assets/`)
      .replace(/href="\//g, `href="${prefix}`)
      .replace('id="root"', 'id="root" data-server-rendered="true"');
  } else {
    processedHtml = html.replace(
      'id="root"',
      'id="root" data-server-rendered="true"'
    );
  }

  // Write the prerendered HTML
  writeFileSync(outputPath, processedHtml, "utf-8");
  return outputPath;
}

async function prerenderRoute(page, route, baseUrl) {
  try {
    const url = `${baseUrl}${route}`;
    await page.goto(url, {
      waitUntil: "domcontentloaded", // Faster than networkidle0
      timeout: 20000,
    });

    // Wait for React to render
    await page.waitForSelector("#root > *", { timeout: 10000 });

    // Get the rendered HTML immediately (no extra delay)
    const html = await page.content();
    
    const outputPath = processAndSaveHTML(html, route);
    console.log(`  ✓ ${route}`);
    return { success: true, route };
  } catch (error) {
    console.error(`  ❌ ${route}: ${error.message}`);
    return { success: false, route, error: error.message };
  }
}

async function prerenderRoutes() {
  const startTime = Date.now();
  console.log("🚀 Starting prerender process...\n");

  const puppeteer = (await import("puppeteer")).default;

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
    // Start Vite preview server
    console.log("📦 Starting preview server...");
    const { preview } = await import("vite");
    const previewServer = await preview({
      preview: {
        port: 4173,
        strictPort: true,
      },
      logLevel: "silent",
    });

    const baseUrl = `http://localhost:4173`;
    console.log(`✓ Preview server running at ${baseUrl}\n`);

    // Create a single page and reuse it for all routes
    const page = await browser.newPage();

    // Block external analytics/tracking scripts
    await page.setRequestInterception(true);
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/_vercel/') || 
          url.includes('/insights/') ||
          url.includes('vercel-insights.com') ||
          url.includes('google-analytics.com') ||
          url.includes('googletagmanager.com')) {
        request.abort();
      } else {
        request.continue();
      }
    });

    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    );

    // Process routes sequentially (but efficiently with reused page)
    console.log(`📄 Prerendering ${routes.length} routes...\n`);
    const results = [];
    
    for (const route of routes) {
      const result = await prerenderRoute(page, route, baseUrl);
      results.push(result);
    }

    // Close page before closing server
    try {
      await page.close();
    } catch (e) {
      // Page might already be closed, ignore
    }

    // Close preview server
    await previewServer.httpServer.close();
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    
    console.log(`\n✅ Prerender complete in ${duration}s!`);
    console.log(`📊 ${successful} successful, ${failed} failed out of ${routes.length} routes\n`);
    
    if (failed > 0) {
      console.log("Failed routes:");
      results.filter(r => !r.success).forEach(r => {
        console.log(`   - ${r.route}`);
      });
    }
  } catch (error) {
    console.error("❌ Prerender error:", error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

prerenderRoutes();
