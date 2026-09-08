const { join } = require("path");

/**
 * Keep Chromium inside node_modules so hosted builds cache it alongside
 * dependencies. The default location (~/.cache/puppeteer) is not part of
 * Vercel's build cache, which would mean re-downloading Chromium on every
 * deploy — slow, and a common cause of build timeouts.
 */
module.exports = {
  cacheDirectory: join(__dirname, "node_modules", ".cache", "puppeteer"),
};
