// Which /practice-words pages each guide and article links to.
//
// The 109 pattern pages were only reachable from the sitemap and their own
// hub, and Search Console left every one of them "Discovered - currently not
// indexed" with no crawl. The guides and articles are already indexed, so a
// contextual link from them is the strongest signal we can send that the
// pattern pages matter.
//
// Keyed by path (the canonical URL minus the origin). Pages not listed here
// still get one representative link per category, so every article links into
// the cluster. Rendered by ArticlePageTemplate.

import {
  getPatternBySlug,
  getPatternsByCategory,
  patternCategories,
  type PhonicsPattern,
} from "./phonicsPatterns";

const SHORT_VOWEL_FAMILIES = [
  "at-family",
  "an-family",
  "et-family",
  "en-family",
  "ig-family",
  "it-family",
  "op-family",
  "ug-family",
];

const articlePracticeLinks: Record<string, string[]> = {
  // Guides
  "/guides/how-to-teach-cvc-words-to-struggling-readers": SHORT_VOWEL_FAMILIES,
  "/guides/short-vowel-sounds-exercises-beginning-readers": SHORT_VOWEL_FAMILIES,
  "/guides/decodable-sentences-for-beginning-readers": [
    "at-family",
    "ap-family",
    "ig-family",
    "ot-family",
    "un-family",
    "sh-digraph",
  ],
  "/guides/teaching-consonant-blends-kindergarten-at-home": [
    "bl-blend",
    "cl-blend",
    "fl-blend",
    "st-blend",
    "sp-blend",
    "tr-blend",
    "gr-blend",
    "sn-blend",
  ],
  "/guides/r-controlled-vowels-teaching-strategies-parents": [
    "ar-r-controlled",
    "or-r-controlled",
    "er-r-controlled",
    "ir-r-controlled",
    "ur-r-controlled",
  ],
  "/guides/vowel-digraphs-activities-first-graders": [
    "ai-vowel-team",
    "ay-vowel-team",
    "ee-vowel-team",
    "ea-vowel-team",
    "oa-vowel-team",
    "oo-vowel-team",
    "ou-vowel-team",
    "oi-vowel-team",
  ],
  "/guides/long-vowel-sounds-practice-first-grade": [
    "ai-vowel-team",
    "ay-vowel-team",
    "ee-vowel-team",
    "ea-vowel-team",
    "ie-vowel-team",
    "oa-vowel-team",
    "ue-vowel-team",
  ],
  "/guides/silent-e-words-practice-for-kids": [
    "at-family",
    "ap-family",
    "in-family",
    "it-family",
    "ot-family",
    "ub-family",
  ],
  "/guides/how-to-teach-phonics-at-home": [
    "at-family",
    "sh-digraph",
    "ch-digraph",
    "bl-blend",
    "st-blend",
    "ai-vowel-team",
    "ar-r-controlled",
  ],
  "/guides/phonics-activities-5-year-old-struggling-reader": [
    "at-family",
    "an-family",
    "ig-family",
    "op-family",
    "ug-family",
    "sh-digraph",
  ],
  "/guides/daily-phonics-practice-routine-kindergarten-at-home": [
    "at-family",
    "an-family",
    "ap-family",
    "ig-family",
    "ot-family",
    "un-family",
  ],
  "/guides/phonics-practice-without-worksheets-kindergarten": [
    "at-family",
    "ig-family",
    "op-family",
    "ug-family",
    "ell-family",
    "ick-family",
  ],
  "/guides/first-grade-reading-practice-activities-home": [
    "sh-digraph",
    "ch-digraph",
    "th-digraph",
    "st-blend",
    "tr-blend",
    "ee-vowel-team",
    "ar-r-controlled",
  ],
  "/guides/phoneme-awareness-complete-guide": [
    "at-family",
    "sh-digraph",
    "th-digraph",
    "bl-blend",
    "st-blend",
  ],
  "/guides/five-minute-reading-practice-activities-kids": [
    "at-family",
    "ig-family",
    "ack-family",
    "ing-family",
    "sh-digraph",
    "st-blend",
  ],

  // Articles
  "/articles/child-cant-blend-sounds-into-words": [
    "at-family",
    "an-family",
    "ig-family",
    "bl-blend",
    "st-blend",
    "sn-blend",
  ],
  "/articles/kindergartener-guesses-words-instead-sounding-out": [
    "at-family",
    "ap-family",
    "in-family",
    "op-family",
    "ug-family",
  ],
  "/articles/child-pronounces-words-wrong": [
    "th-digraph",
    "sh-digraph",
    "ch-digraph",
    "wh-digraph",
    "ng-digraph",
    "ph-digraph",
  ],
  "/articles/child-confuses-b-d-letters": [
    "ab-family",
    "ad-family",
    "ed-family",
    "id-family",
    "ob-family",
    "ub-family",
  ],
  "/articles/child-reads-slowly-struggles-with-fluency": [
    "at-family",
    "ill-family",
    "ack-family",
    "ing-family",
    "ee-vowel-team",
    "ai-vowel-team",
  ],
};

/**
 * Pattern pages to link from the article at `path`.
 *
 * Throws on an unknown slug rather than dropping it: a typo here would
 * otherwise ship a silently missing link, and the prerender fails the build
 * on any page that throws while rendering.
 */
export function getPracticeLinksForArticle(path: string): PhonicsPattern[] {
  const slugs = articlePracticeLinks[path];

  if (!slugs) {
    // One representative pattern per category.
    return patternCategories
      .map((category) => getPatternsByCategory(category)[0])
      .filter((p): p is PhonicsPattern => Boolean(p));
  }

  return slugs.map((slug) => {
    const pattern = getPatternBySlug(slug);
    if (!pattern) {
      throw new Error(
        `articlePracticeLinks: "${path}" links to unknown pattern "${slug}"`
      );
    }
    return pattern;
  });
}
