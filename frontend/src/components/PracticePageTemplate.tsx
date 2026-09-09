import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ArrowRight,
  BookOpen,
  Mic,
  AlertCircle,
  Info as InfoIcon,
} from "lucide-react";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";
import { DEFAULT_OG_IMAGE } from "@/components/SeoHead";
import { trackSignupClick } from "@/utils/analytics";
import {
  categoryLabels,
  getPatternBySlug,
  type PhonicsPattern,
} from "@/data/phonicsPatterns";

const SITE_ORIGIN = "https://wordwizai.com";

/**
 * Renders one phonics pattern as a standalone practice page.
 *
 * Every page must emit exactly one <title>, one meta description, and one
 * canonical matching its own route — scripts/prerender.mjs fails the build
 * otherwise.
 */
const PracticePageTemplate = ({ pattern }: { pattern: PhonicsPattern }) => {
  const {
    slug,
    displayName,
    category,
    gradeLevel,
    words,
    sampleSentences,
    teachingNotes,
    commonErrors,
    relatedSlugs,
  } = pattern;

  const canonicalUrl = `${SITE_ORIGIN}/practice-words/${slug}`;
  const metaTitle = `${displayName}: Word List, Sentences & Practice`;
  const metaDescription = `${words.length} ${displayName.toLowerCase()} words with decodable sentences, teaching tips, and the mistakes children make most. Free ${gradeLevel} phonics practice with pronunciation feedback.`;

  // A short, quotable answer up top. Answer engines cite pages that resolve the
  // question in the first hundred words rather than warming up to it.
  const directAnswer = `${displayName} words follow one repeating pattern, so a child who can read one of them has most of what they need to read the rest. This list has ${words.length} ${gradeLevel.toLowerCase()}-level words plus ${sampleSentences.length} decodable sentences. Practice them out loud — the most common error is ${commonErrors[0]?.charAt(0).toLowerCase()}${commonErrors[0]?.slice(1)}.`;

  const related = relatedSlugs
    .map((relatedSlug) => getPatternBySlug(relatedSlug))
    .filter((p): p is PhonicsPattern => Boolean(p));

  const structuredData = [
    {
      "@context": "https://schema.org",
      "@type": "Article",
      headline: metaTitle,
      description: metaDescription,
      author: { "@type": "Organization", name: "Word Wiz AI" },
      publisher: {
        "@type": "Organization",
        name: "Word Wiz AI",
        logo: {
          "@type": "ImageObject",
          url: `${SITE_ORIGIN}/wordwizIcon.svg`,
        },
      },
      mainEntityOfPage: { "@type": "WebPage", "@id": canonicalUrl },
    },
    {
      "@context": "https://schema.org",
      "@type": "HowTo",
      name: `How to practice ${displayName.toLowerCase()} words`,
      description: `A short at-home routine for teaching ${displayName.toLowerCase()} words to a ${gradeLevel.toLowerCase()} reader.`,
      step: [
        {
          "@type": "HowToStep",
          name: "Read the pattern aloud first",
          text: `Say the ${pattern.pattern} sound on its own before reading any whole words, so the child hears the part that stays the same.`,
        },
        {
          "@type": "HowToStep",
          name: "Blend three or four words",
          text: "Work through a small set of words, changing only the sound that differs between them.",
        },
        {
          "@type": "HowToStep",
          name: "Read the sentences",
          text: "Move from single words to the decodable sentences so the pattern appears in real reading.",
        },
        {
          "@type": "HowToStep",
          name: "Check pronunciation",
          text: "Have the child read aloud and confirm each sound is correct before moving to a new pattern.",
        },
      ],
    },
  ];

  return (
    <>
      <Helmet>
        <title>{metaTitle}</title>
        <meta name="description" content={metaDescription} />
        <link rel="canonical" href={canonicalUrl} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={canonicalUrl} />
        <meta property="og:title" content={metaTitle} />
        <meta property="og:description" content={metaDescription} />
        <meta property="og:image" content={DEFAULT_OG_IMAGE} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={metaTitle} />
        <meta name="twitter:description" content={metaDescription} />
        <meta name="twitter:image" content={DEFAULT_OG_IMAGE} />
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      </Helmet>

      <div className="min-h-screen flex flex-col bg-background">
        <LandingPageNavbar />

        <main className="flex-1">
          <article className="container mx-auto px-4 py-8 max-w-4xl">
            <nav
              aria-label="Breadcrumb"
              className="text-sm text-muted-foreground mb-6"
            >
              <Link to="/" className="hover:text-foreground">
                Home
              </Link>
              <span className="mx-2">/</span>
              <Link to="/practice-words" className="hover:text-foreground">
                Practice Words
              </Link>
              <span className="mx-2">/</span>
              <span className="text-foreground">{displayName}</span>
            </nav>

            <div className="flex flex-wrap items-center gap-2 mb-4">
              <Badge variant="secondary">{categoryLabels[category]}</Badge>
              <Badge variant="outline">{gradeLevel}</Badge>
            </div>

            <h1 className="text-3xl md:text-4xl font-bold mb-4 text-foreground">
              {displayName}: Word List &amp; Practice
            </h1>

            <div className="border-l-4 border-blue-200 bg-blue-50 text-blue-900 p-4 my-6 rounded">
              <div className="flex gap-3">
                <InfoIcon className="h-5 w-5 shrink-0 mt-0.5" />
                <p className="text-sm leading-relaxed">{directAnswer}</p>
              </div>
            </div>

            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <BookOpen className="h-5 w-5" />
                  {words.length} {displayName} Words
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
                  {words.map((word) => (
                    <li
                      key={word}
                      className="rounded-lg border bg-card px-3 py-2 text-center font-medium"
                    >
                      {word}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="mb-8 border-2 border-primary/30 bg-primary/5">
              <CardContent className="py-6 text-center">
                <Mic className="h-8 w-8 mx-auto mb-3 text-primary" />
                <h2 className="text-xl font-semibold mb-2">
                  Practice these words out loud
                </h2>
                <p className="text-muted-foreground mb-4 max-w-xl mx-auto">
                  Word Wiz AI listens to your child read and shows exactly which
                  sounds they missed — not just whether the word was right. Free,
                  no ads.
                </p>
                <Button
                  asChild
                  size="lg"
                  onClick={() =>
                    trackSignupClick("practice-words", "link", slug)
                  }
                >
                  <Link to="/signup">
                    Start practicing free
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </CardContent>
            </Card>

            <section className="mb-8">
              <h2 className="text-2xl font-bold mb-4">Decodable Sentences</h2>
              <p className="text-muted-foreground mb-4">
                Every word in these sentences uses sounds your child has already
                learned, so they can be read by decoding rather than guessing.
              </p>
              <ul className="space-y-3">
                {sampleSentences.map((sentence) => (
                  <li
                    key={sentence}
                    className="rounded-lg border bg-card px-4 py-3 text-lg"
                  >
                    {sentence}
                  </li>
                ))}
              </ul>
            </section>

            <Separator className="my-8" />

            <section className="mb-8">
              <h2 className="text-2xl font-bold mb-4">
                How to Teach {displayName} Words
              </h2>
              <div className="space-y-4">
                {teachingNotes.map((note, index) => (
                  <p
                    key={index}
                    className="text-base leading-relaxed text-foreground/90"
                  >
                    {note}
                  </p>
                ))}
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold mb-4">
                Common Mistakes to Watch For
              </h2>
              <ul className="space-y-3">
                {commonErrors.map((error) => (
                  <li key={error} className="flex gap-3">
                    <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-amber-600" />
                    <span className="text-foreground/90">{error}</span>
                  </li>
                ))}
              </ul>
            </section>

            {related.length > 0 && (
              <section className="mb-8">
                <h2 className="text-2xl font-bold mb-4">Practice Next</h2>
                <div className="grid sm:grid-cols-2 gap-3">
                  {related.map((item) => (
                    <Link
                      key={item.slug}
                      to={`/practice-words/${item.slug}`}
                      className="rounded-lg border bg-card p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="font-semibold">{item.displayName}</div>
                      <div className="text-sm text-muted-foreground">
                        {item.words.length} words · {item.gradeLevel}
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            <div className="text-center">
              <Link
                to="/practice-words"
                className="text-primary hover:underline"
              >
                Browse all phonics patterns
              </Link>
            </div>
          </article>
        </main>

        <LandingPageFooter />
      </div>
    </>
  );
};

export default PracticePageTemplate;
