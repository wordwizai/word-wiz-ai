# Quick Reference: Prerendering Static Pages

## What Changed?

**Before**: Only 9 pages were prerendered
**Now**: All 34 static SEO pages are prerendered

## Build Commands

```bash
# Production build with prerendering (default)
npm run build

# Development build (no prerendering, faster)
npm run build:only

# Preview the built site
npm run preview
```

## How to Add a New SEO Page

1. **Create the page component** in `src/pages/`
   ```tsx
   // src/pages/guides/MyNewGuide.tsx
   export default function MyNewGuide() {
     return <div>My guide content</div>;
   }
   ```

2. **Add route in** `src/App.tsx`
   ```tsx
   const MyNewGuide = lazy(() => import("./pages/guides/MyNewGuide.tsx"));
   
   // In Routes:
   <Route path="/guides/my-new-guide" element={<MyNewGuide />} />
   ```

3. **Add to prerender list** in `scripts/prerender.mjs`
   ```javascript
   const routes = [
     // ... existing routes
     "/guides/my-new-guide", // ADD THIS
   ];
   ```

4. **Build and test**
   ```bash
   npm run build
   npm run preview
   # Visit http://localhost:5173/guides/my-new-guide
   ```

5. **Verify it worked**
   ```bash
   # Check the HTML file exists
   ls dist/guides/my-new-guide/index.html
   
   # Check it has content (not empty)
   cat dist/guides/my-new-guide/index.html | grep "<title>"
   ```

## Verify Prerendering Works

### Check dist/ folder structure
```bash
tree dist/ -L 2
```

Expected output:
```
dist/
├── index.html
├── about/
├── contact/
├── privacy/
├── comparisons/ (11 subfolders)
├── articles/ (7 subfolders)
├── guides/ (12 subfolders)
└── assets/
```

### Check HTML has content
```bash
# Landing page
head -n 20 dist/index.html

# Any SEO page
head -n 20 dist/about/index.html
```

Should see:
- `<title>` with actual title
- `<meta name="description" content="...">` with description
- Content inside `<div id="root">`, not empty

### Search for prerender marker
```bash
grep -r "data-server-rendered" dist/*.html dist/*/*.html | wc -l
```

Should show: `34` (one for each page)

## Troubleshooting

### Build fails with "puppeteer not found"
```bash
npm install --save-dev puppeteer
```

### Prerender hangs or times out
- Check if preview server starts (port 4173)
- Increase timeout in `scripts/prerender.mjs`
- Check for console errors in the page

### Page not prerendering
- Verify route is in `scripts/prerender.mjs`
- Check route path matches exactly (including hyphens)
- Ensure component doesn't have client-only dependencies that break SSR

### Asset paths broken on prerendered page
- Check `scripts/prerender.mjs` asset path correction logic
- For nested routes, paths should be relative: `../../assets/`

## Current Prerendered Pages (34 total)

### Core (4)
- `/` - Landing page
- `/about` - About page
- `/contact` - Contact page
- `/privacy` - Privacy policy

### Comparisons (11)
- `/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai`
- `/comparisons/reading-eggs-vs-starfall-vs-word-wiz-ai`
- `/comparisons/homer-vs-khan-academy-kids-vs-word-wiz-ai`
- `/comparisons/hooked-on-phonics-vs-word-wiz-ai`
- `/comparisons/best-free-reading-apps`
- `/comparisons/lexia-vs-raz-kids-vs-word-wiz-ai`
- `/comparisons/teach-your-monster-vs-abcya-vs-word-wiz-ai`
- `/comparisons/ixl-vs-duolingo-abc-vs-word-wiz-ai`
- `/comparisons/reading-tutor-vs-reading-app`
- `/comparisons/ai-reading-app-vs-traditional-phonics-program`
- `/comparisons/free-phonics-apps-vs-paid-reading-programs`

### Articles (7)
- `/articles/why-child-hates-reading`
- `/articles/child-pronounces-words-wrong`
- `/articles/decodable-books-vs-leveled-readers`
- `/articles/child-cant-blend-sounds-into-words`
- `/articles/kindergartener-guesses-words-instead-sounding-out`
- `/articles/child-reads-slowly-struggles-with-fluency`
- `/articles/first-grader-skips-words-when-reading-aloud`

### Guides (12)
- `/guides/how-to-choose-reading-app`
- `/guides/how-to-teach-phonics-at-home`
- `/guides/is-teacher-teaching-enough-phonics`
- `/guides/phoneme-awareness-complete-guide`
- `/guides/how-to-teach-cvc-words-to-struggling-readers`
- `/guides/teaching-consonant-blends-kindergarten-at-home`
- `/guides/daily-phonics-practice-routine-kindergarten-at-home`
- `/guides/short-vowel-sounds-exercises-beginning-readers`
- `/guides/decodable-sentences-for-beginning-readers`
- `/guides/five-minute-reading-practice-activities-kids`
- `/guides/r-controlled-vowels-teaching-strategies-parents`
- `/guides/phonics-practice-without-worksheets-kindergarten`

## SEO Benefits

✅ **Search engines see full content** without executing JavaScript
✅ **Faster initial page load** - content visible immediately
✅ **Better indexing** - crawlers can easily parse content
✅ **Structured data** included for rich search results
✅ **Social media previews** work (OpenGraph meta tags)

## Performance Impact

- **Build time**: +2-5 minutes (for prerendering 34 pages)
- **Bundle size**: No change (prerendering doesn't affect bundle)
- **Runtime**: Faster initial load, same interactive speed

## Deployment

Works automatically with current Vercel setup:
```json
{
  "buildCommand": "npm run build"
}
```

No configuration changes needed.

## Questions?

See full documentation:
- [`PRERENDER_IMPLEMENTATION_SUMMARY.md`](./PRERENDER_IMPLEMENTATION_SUMMARY.md)
- [`VITE_PRERENDER_PLUGIN_IMPLEMENTATION.md`](./VITE_PRERENDER_PLUGIN_IMPLEMENTATION.md)
