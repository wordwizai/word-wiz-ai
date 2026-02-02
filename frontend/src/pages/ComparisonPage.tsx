import { useParams, Navigate } from "react-router-dom";
import ArticlePageTemplate from "@/components/ArticlePageTemplate";
import { comparisonPages } from "@/data/comparisons";

/**
 * Generic comparison page component that loads data by slug.
 *
 * This single component replaces 13 individual comparison page files,
 * reducing duplication and improving maintainability.
 */
const ComparisonPage = () => {
  const { slug } = useParams<{ slug: string }>();

  // Look up the comparison data by slug
  const data = slug ? comparisonPages[slug] : undefined;

  // If slug not found, redirect to 404
  if (!data) {
    return <Navigate to="/404" replace />;
  }

  // Render using ArticlePageTemplate with the data
  return (
    <ArticlePageTemplate
      metaTitle={data.metaTitle}
      metaDescription={data.metaDescription}
      canonicalUrl={data.canonicalUrl}
      ogImage={data.ogImage}
      heroImage={data.heroImage}
      heroImageAlt={data.heroImageAlt}
      headline={data.headline}
      subheadline={data.subheadline}
      author={data.author}
      publishDate={data.publishDate}
      readTime={data.readTime}
      category={data.category}
      content={data.content}
      relatedArticles={data.relatedArticles}
      structuredData={data.structuredData}
      breadcrumbs={data.breadcrumbs}
    />
  );
};

export default ComparisonPage;
