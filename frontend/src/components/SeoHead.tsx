import { Helmet } from "react-helmet-async";

const SITE_ORIGIN = "https://wordwizai.com";

interface SeoHeadProps {
  /** Full <title> text for this page. Must be unique per route. */
  title: string;
  /** Meta description. Must be unique per route. */
  description: string;
  /** Route path, e.g. "/about". Combined with the site origin for canonical. */
  canonicalPath: string;
  ogType?: "website" | "article";
  ogImage?: string;
  /** JSON-LD object or array of objects. */
  structuredData?: unknown;
}

/**
 * Per-page meta tags for routes that don't go through ArticlePageTemplate or
 * ComparisonPageTemplate.
 *
 * Without this, a route inherits whatever is hardcoded in index.html, which
 * means its title, description and canonical all point at the homepage — so
 * search engines treat the page as a duplicate of "/" and drop it.
 */
const SeoHead = ({
  title,
  description,
  canonicalPath,
  ogType = "website",
  ogImage = `${SITE_ORIGIN}/og-image.png`,
  structuredData,
}: SeoHeadProps) => {
  const canonicalUrl = `${SITE_ORIGIN}${canonicalPath === "/" ? "/" : canonicalPath}`;

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonicalUrl} />

      <meta property="og:type" content={ogType} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={ogImage} />

      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:url" content={canonicalUrl} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />

      {structuredData ? (
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      ) : null}
    </Helmet>
  );
};

export default SeoHead;
