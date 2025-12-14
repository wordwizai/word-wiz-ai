import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createServer } from "vite";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Routes to prerender
const routes = [
  "/",
  "/about",
  "/contact",
  "/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai",
  "/comparisons/reading-eggs-vs-starfall-vs-word-wiz-ai",
  "/comparisons/homer-vs-khan-academy-kids-vs-word-wiz-ai",
  "/comparisons/hooked-on-phonics-vs-word-wiz-ai",
  "/comparisons/best-free-reading-apps",
];

const distPath = join(__dirname, "..", "dist");

async function prerenderRoutes() {
  console.log("🚀 Starting prerender process...\n");

  // Use puppeteer with a local preview server for better compatibility
  const puppeteer = (await import("puppeteer")).default;

  const browser = await puppeteer.launch({
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
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

    for (const route of routes) {
      console.log(`📄 Prerendering: ${route}`);

      const page = await browser.newPage();

      // Set a user agent to avoid bot detection
      await page.setUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      );

      // Navigate to the route
      const url = `${baseUrl}${route}`;
      await page.goto(url, {
        waitUntil: "networkidle0",
        timeout: 30000,
      });

      // Wait for React to render
      await page.waitForSelector("#root > *", { timeout: 10000 });

      // Give React time to fully render
      await page.evaluate(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      // Get the rendered HTML
      const html = await page.content();

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
      console.log(`  ✓ Saved to: ${outputPath.replace(distPath, "dist")}\n`);

      await page.close();
    }

    // Close preview server
    await previewServer.httpServer.close();
    console.log("✓ Preview server closed\n");
  } catch (error) {
    console.error("❌ Prerender error:", error);
    process.exit(1);
  } finally {
    await browser.close();
  }

  console.log("✅ Prerender complete!\n");
  console.log(`📊 Prerendered ${routes.length} routes:`);
  routes.forEach((route) => console.log(`   - ${route}`));
}

prerenderRoutes();
