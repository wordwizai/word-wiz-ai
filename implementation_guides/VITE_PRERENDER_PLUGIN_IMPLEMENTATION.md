# Vite Prerender Plugin Implementation Guide

## Executive Summary

Replace the current custom Puppeteer-based prerendering with the official `vite-prerender-plugin` for better performance, maintainability, and Vite integration. The plugin will prerender 33+ static SEO pages for improved web crawling and initial page load performance.

**Current State**: Custom Puppeteer script (`scripts/prerender.mjs`) that manually launches a preview server and crawls pages
**Target State**: Vite-native prerendering using `vite-prerender-plugin` integrated into the build process

**Key Benefits**:
- ✅ Native Vite integration (no separate preview server needed)
- ✅ Automatic link discovery for SEO pages
- ✅ Cleaner build process
- ✅ Better performance (no browser launch overhead)
- ✅ Simplified configuration
- ✅ Automatic head tag management (title, meta, lang)

---

## Phase 1: Research & Setup (20% effort, 80% understanding)

### Step 1.1: Install vite-prerender-plugin
- [ ] Install the plugin: `npm install --save-dev vite-prerender-plugin`
- [ ] Install React render dependencies: `npm install --save-dev react-dom/server` (if not already available)

**Quality Check**: Run `npm list vite-prerender-plugin` to verify installation

### Step 1.2: Understand Current Routing Structure
**Already Known**:
- Landing page: `/` (LandingPage.tsx)
- Static pages: `/about`, `/contact`, `/privacy`
- SEO pages:
  - 11 comparisons pages under `/comparisons/*`
  - 7 articles pages under `/articles/*`
  - 12 guides pages under `/guides/*`
- All routes defined in `src/App.tsx`
- Total: 33+ static pages to prerender

**Quality Check**: Review `src/App.tsx` routes to confirm all static routes

### Step 1.3: Understand Plugin Requirements
**Key Points from Research**:
1. Plugin needs a `prerender()` function exported from a prerender script
2. Must set `renderTarget` option (where to inject HTML, e.g., `#root`)
3. Can use `additionalPrerenderRoutes` for routes not auto-discovered
4. Plugin calls the prerender function which should return HTML string
5. For React, we need to use `renderToString()` from `react-dom/server`

**Quality Check**: Document understanding of how plugin works

---

## Phase 2: Create Prerender Script (Simple 80/20 approach)

### Step 2.1: Create Minimal Prerender Script
- [ ] Create `src/prerender.tsx` with:
  - Import React components and router setup
  - Export `prerender()` function
  - Use `react-dom/server` to render app to string
  - Return HTML with proper route handling

**Implementation Strategy**:
```typescript
// src/prerender.tsx
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import App from './App';

export async function prerender(data) {
  const { url } = data;
  
  // Render the app for the given URL
  const html = renderToString(
    <StaticRouter location={url}>
      <App />
    </StaticRouter>
  );
  
  return { html };
}
```

**Quality Check**: Verify imports are available and syntax is correct

### Step 2.2: Handle Context Providers
- [ ] Wrap App with necessary providers (ThemeProvider, HelmetProvider, etc.)
- [ ] Ensure providers work in SSR context
- [ ] Handle any client-only code gracefully

**Quality Check**: Test that providers don't throw errors during SSR

### Step 2.3: Extract Page Metadata
- [ ] Extract title, description from Helmet for each page
- [ ] Return head metadata in prerender function
- [ ] Ensure canonical URLs are set correctly

**Implementation**:
```typescript
return {
  html,
  head: {
    title: 'Page Title',
    lang: 'en',
    elements: new Set([
      { type: 'meta', props: { name: 'description', content: '...' } }
    ])
  }
};
```

**Quality Check**: Verify metadata appears in prerendered HTML

---

## Phase 3: Configure Vite Plugin (Minimal Configuration)

### Step 3.1: Update vite.config.ts
- [ ] Import `vitePrerenderPlugin` from 'vite-prerender-plugin'
- [ ] Add plugin to plugins array with configuration
- [ ] Set `renderTarget: '#root'`
- [ ] Set `prerenderScript` to absolute path of prerender.tsx

**Implementation**:
```typescript
import { vitePrerenderPlugin } from 'vite-prerender-plugin';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    vitePrerenderPlugin({
      renderTarget: '#root',
      prerenderScript: path.resolve(__dirname, './src/prerender.tsx'),
      additionalPrerenderRoutes: [
        '/',
        '/about',
        '/contact',
        '/privacy',
        // Add all SEO routes here
      ],
    }),
    // ... other plugins
  ],
});
```

**Quality Check**: Ensure TypeScript doesn't show errors

### Step 3.2: List All Static Routes
- [ ] Extract all static routes from `App.tsx`
- [ ] Create comprehensive list for `additionalPrerenderRoutes`
- [ ] Include all comparison, article, and guide pages

**Routes to Include**:
- Landing: `/`
- Static: `/about`, `/contact`, `/privacy`
- Comparisons (11): `/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai`, etc.
- Articles (7): `/articles/why-child-hates-reading`, etc.
- Guides (12): `/guides/how-to-choose-reading-app`, etc.

**Quality Check**: Count routes matches pages in `src/pages/*`

### Step 3.3: Update Build Scripts
- [ ] Keep `build:only` for regular build: `"build:only": "vite build"`
- [ ] Update `build` to use plugin: `"build": "vite build"` (plugin runs automatically)
- [ ] Remove old `build:prerender` script (or keep as fallback)

**Quality Check**: Verify scripts in `package.json` are correct

---

## Phase 4: Handle Edge Cases & Client-Only Code

### Step 4.1: Identify Client-Only Dependencies
**Known Issues**:
- Browser APIs (localStorage, window, navigator)
- Audio/Media APIs (MediaRecorder, AudioContext)
- WebSocket connections
- @huggingface/transformers (WASM/WebGPU)

- [ ] Audit components for client-only code
- [ ] Add guards: `if (typeof window !== 'undefined')`
- [ ] Use `useEffect` for client-only initialization

**Quality Check**: Search codebase for browser APIs

### Step 4.2: Handle Lazy Loading
- [ ] Ensure Suspense boundaries work in SSR
- [ ] Consider prerendering with fallback loading states
- [ ] Or keep lazy loading only for client hydration

**Decision**: Keep current lazy loading as-is since prerendered pages will show loading state initially

**Quality Check**: Test that lazy components don't break SSR

### Step 4.3: Handle Dynamic Imports
- [ ] Check if any dynamic imports need SSR handling
- [ ] Ensure imports in prerender script are static

**Quality Check**: No dynamic import errors during build

---

## Phase 5: Testing & Validation

### Step 5.1: Test Build Process
- [ ] Run `npm run build` and verify it completes
- [ ] Check that `dist/` contains prerendered HTML files
- [ ] Verify folder structure: `dist/about/index.html`, `dist/contact/index.html`, etc.

**Expected Output**:
```
dist/
  index.html (landing page)
  about/index.html
  contact/index.html
  privacy/index.html
  comparisons/
    abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai/index.html
    ...
  articles/
    why-child-hates-reading/index.html
    ...
  guides/
    how-to-choose-reading-app/index.html
    ...
```

**Quality Check**: Manually inspect HTML files for content

### Step 5.2: Verify HTML Content
- [ ] Open prerendered HTML files
- [ ] Verify page content is present (not empty root div)
- [ ] Check meta tags are populated correctly
- [ ] Verify assets paths are correct
- [ ] Ensure structured data is included

**Quality Check**: Use browser "View Source" to see raw HTML

### Step 5.3: Test Preview Server
- [ ] Run `npm run preview`
- [ ] Navigate to prerendered routes
- [ ] Verify pages load correctly
- [ ] Check that hydration works (React takes over after initial render)

**Quality Check**: No console errors, pages are interactive

### Step 5.4: Test SEO Improvements
- [ ] Use Google's Rich Results Test on prerendered HTML
- [ ] Verify structured data is valid
- [ ] Test with Lighthouse (should improve SEO score)
- [ ] Check that crawlers can see content without JS

**Quality Check**: SEO score improves, structured data validates

---

## Phase 6: Cleanup & Documentation

### Step 6.1: Remove Old Prerender Script
- [ ] Delete or archive `scripts/prerender.mjs`
- [ ] Remove puppeteer dependency if no longer needed: `npm uninstall puppeteer`
- [ ] Clean up old build script references

**Quality Check**: Build still works without old script

### Step 6.2: Update Documentation
- [ ] Update README.md with new build process
- [ ] Document prerendering approach in IMPLEMENTATION_SUMMARY.md
- [ ] Add comments to vite.config.ts explaining prerender setup

**Quality Check**: Documentation is clear for future developers

### Step 6.3: Update Deployment Configuration
- [ ] Verify Vercel configuration (`vercel.json`)
- [ ] Ensure `buildCommand` is correct: `npm run build`
- [ ] Test deployment to ensure prerendered pages are served correctly

**Quality Check**: Deployment works and pages are accessible

---

## Quality Assurance Checklist (Per Phase)

### Phase 1 QA:
- ✅ Plugin installed successfully
- ✅ Dependencies resolved
- ✅ Understanding documented

### Phase 2 QA:
- ✅ Prerender script created
- ✅ No TypeScript errors
- ✅ Providers work in SSR context
- ✅ Metadata extraction works

### Phase 3 QA:
- ✅ Vite config updated without errors
- ✅ All static routes listed
- ✅ Build scripts updated

### Phase 4 QA:
- ✅ No browser API errors during build
- ✅ Lazy loading works
- ✅ No dynamic import issues

### Phase 5 QA:
- ✅ Build completes successfully
- ✅ HTML files contain actual content
- ✅ Preview server works
- ✅ SEO tools validate correctly
- ✅ Lighthouse score improved

### Phase 6 QA:
- ✅ Old code removed
- ✅ Documentation updated
- ✅ Deployment successful

---

## Rollback Plan

If issues arise:
1. Revert vite.config.ts changes
2. Restore old build script: `"build:prerender": "vite build && node scripts/prerender.mjs"`
3. Keep `scripts/prerender.mjs` as backup until confident

---

## Expected Outcomes

**Build Time**: Similar or slightly faster (no browser launch)
**Output Size**: Same (HTML is prerendered, not bundled differently)
**SEO Impact**: Improved crawler access to content
**Developer Experience**: Cleaner, more maintainable prerendering

**Success Metrics**:
- ✅ All 33+ pages prerender successfully
- ✅ Build completes without errors
- ✅ Preview server serves prerendered content
- ✅ SEO tools can read page content
- ✅ Lighthouse SEO score improves or stays the same
- ✅ Deployment works on Vercel

---

## Notes & Considerations

### 80/20 Approach Applied:
- Focus on core static pages first (landing, about, contact)
- Use simple prerender function without over-optimization
- Rely on plugin defaults where possible
- Add complexity only if needed

### Potential Issues:
1. **React 19 Compatibility**: Verify react-dom/server works with React 19
2. **StaticRouter**: May need react-router-dom v7 compatible approach
3. **HelmetProvider**: Ensure react-helmet-async works in SSR
4. **Client-only code**: Guard carefully

### Alternative Approaches Considered:
- Keep Puppeteer script: More control but harder to maintain
- Use vite-plugin-prerender: Different package, less maintained
- No prerendering: Worse for SEO, rejected

### Future Enhancements:
- Auto-discover routes from App.tsx instead of manual list
- Generate sitemap.xml during prerender
- Add 404 page prerendering
- Cache prerendered pages for faster rebuilds

---

## Implementation Timeline

**Estimated Time**: 2-4 hours total
- Phase 1: 30 min
- Phase 2: 1 hour
- Phase 3: 30 min
- Phase 4: 30 min
- Phase 5: 1 hour
- Phase 6: 30 min

**Risk Level**: Medium (SSR can have edge cases, but pages are mostly static)

---

## References

- [vite-prerender-plugin GitHub](https://github.com/preactjs/vite-prerender-plugin)
- [vite-prerender-plugin npm](https://www.npmjs.com/package/vite-prerender-plugin)
- [React Server-Side Rendering](https://react.dev/reference/react-dom/server)
- [React Router v7 Static Rendering](https://reactrouter.com/en/main/guides/ssr)
