import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";
import {
  categoryDescriptions,
  categoryLabels,
  getPatternsByCategory,
  patternCategories,
  phonicsPatterns,
} from "@/data/phonicsPatterns";

const SITE_ORIGIN = "https://wordwizai.com";

/**
 * Index for every phonics pattern page. This is what makes the generated
 * pages internally linked and crawlable rather than orphaned in the sitemap.
 */
const PracticeWordsHub = () => {
  const canonicalUrl = `${SITE_ORIGIN}/practice-words`;
  const metaTitle = "Phonics Word Lists & Practice by Pattern";
  const metaDescription = `Free phonics word lists for ${phonicsPatterns.length} patterns — word families, digraphs, blends, vowel teams and r-controlled vowels. Each list has decodable sentences, teaching tips and out-loud practice.`;

  const populatedCategories = patternCategories.filter(
    (category) => getPatternsByCategory(category).length > 0
  );

  return (
    <>
      <Helmet>
        <title>{metaTitle}</title>
        <meta name="description" content={metaDescription} />
        <link rel="canonical" href={canonicalUrl} />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={canonicalUrl} />
        <meta property="og:title" content={metaTitle} />
        <meta property="og:description" content={metaDescription} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={metaTitle} />
        <meta name="twitter:description" content={metaDescription} />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: metaTitle,
            description: metaDescription,
            url: canonicalUrl,
            hasPart: phonicsPatterns.map((pattern) => ({
              "@type": "WebPage",
              name: pattern.displayName,
              url: `${SITE_ORIGIN}/practice-words/${pattern.slug}`,
            })),
          })}
        </script>
      </Helmet>

      <div className="min-h-screen flex flex-col bg-background">
        <LandingPageNavbar />

        <main className="flex-1">
          <div className="container mx-auto px-4 py-12 max-w-5xl">
            <nav
              aria-label="Breadcrumb"
              className="text-sm text-muted-foreground mb-6"
            >
              <Link to="/" className="hover:text-foreground">
                Home
              </Link>
              <span className="mx-2">/</span>
              <span className="text-foreground">Practice Words</span>
            </nav>

            <h1 className="text-3xl md:text-4xl font-bold mb-4">
              Phonics Word Lists &amp; Practice
            </h1>
            <p className="text-lg text-muted-foreground mb-10 max-w-3xl">
              {phonicsPatterns.length} phonics patterns, each with a word list,
              decodable sentences, teaching guidance and the mistakes children
              make most. Pick a pattern and practice it out loud — Word Wiz AI
              shows exactly which sounds were missed.
            </p>

            {populatedCategories.map((category) => {
              const patterns = getPatternsByCategory(category);
              return (
                <section key={category} className="mb-12">
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <h2 className="text-2xl font-bold">
                      {categoryLabels[category]}
                    </h2>
                    <Badge variant="secondary">{patterns.length}</Badge>
                  </div>
                  <p className="text-muted-foreground mb-5 max-w-3xl">
                    {categoryDescriptions[category]}
                  </p>
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {patterns.map((pattern) => (
                      <Link
                        key={pattern.slug}
                        to={`/practice-words/${pattern.slug}`}
                        className="rounded-lg border bg-card p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="font-semibold">
                          {pattern.displayName}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {pattern.words.length} words · {pattern.gradeLevel}
                        </div>
                      </Link>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        </main>

        <LandingPageFooter />
      </div>
    </>
  );
};

export default PracticeWordsHub;
