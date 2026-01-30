/**
 * Comparison pages data registry.
 *
 * Central export point for all comparison page data.
 * Add new comparisons here as they're converted from component files.
 */

import { freeVsPaidData } from "./free-vs-paid";
import { abcmouseVsHookedOnPhonicsData } from "./abcmouse-vs-hooked-on-phonics";
import { aiVsTraditionalData } from "./ai-vs-traditional";
import { bestFreeReadingAppsData } from "./best-free-reading-apps";
import { bestPhonicsAppKindergartenData } from "./best-phonics-app-kindergarten";
import { homerVsKhanAcademyKidsData } from "./homer-vs-khan-academy-kids";
import { hookedOnPhonicsVsWordWizAiData } from "./hooked-on-phonics-vs-word-wiz-ai";
import { ixlVsDuolingoAbcData } from "./ixl-vs-duolingo-abc";
import { lexiaVsRazKidsData } from "./lexia-vs-raz-kids";
import { readingEggsVsStarfallData } from "./reading-eggs-vs-starfall";
import { teachMonsterVsAbcyaData } from "./teach-monster-vs-abcya";
import { readingTutorVsReadingAppData } from "./reading-tutor-vs-reading-app";
import { worksheetsVsInteractiveData } from "./worksheets-vs-interactive";
import type { ComparisonPageData } from "../seoPageTypes";

export const comparisonPages: Record<string, ComparisonPageData> = {
  "free-phonics-apps-vs-paid-reading-programs": freeVsPaidData,
  "abcmouse-vs-hooked-on-phonics": abcmouseVsHookedOnPhonicsData,
  "ai-reading-app-vs-traditional-phonics-program": aiVsTraditionalData,
  "best-free-reading-apps": bestFreeReadingAppsData,
  "best-phonics-app-kindergarten-struggling-readers": bestPhonicsAppKindergartenData,
  "homer-vs-khan-academy-kids": homerVsKhanAcademyKidsData,
  "hooked-on-phonics-vs-word-wiz-ai": hookedOnPhonicsVsWordWizAiData,
  "ixl-vs-duolingo-abc-vs-word-wiz-ai": ixlVsDuolingoAbcData,
  "lexia-vs-raz-kids-vs-word-wiz-ai": lexiaVsRazKidsData,
  "reading-eggs-vs-starfall": readingEggsVsStarfallData,
  "teach-your-monster-vs-abcya-vs-word-wiz-ai": teachMonsterVsAbcyaData,
  "reading-tutor-vs-reading-app": readingTutorVsReadingAppData,
  "phonics-worksheets-vs-interactive-reading": worksheetsVsInteractiveData,
};

/**
 * Get all comparison page slugs for routing.
 */
export const comparisonSlugs = Object.keys(comparisonPages);

/**
 * Get comparison data by slug.
 */
export const getComparisonBySlug = (slug: string): ComparisonPageData | undefined => {
  return comparisonPages[slug];
};
