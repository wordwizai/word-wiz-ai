import { Navigate, useParams } from "react-router-dom";
import PracticePageTemplate from "@/components/PracticePageTemplate";
import { getPatternBySlug } from "@/data/phonicsPatterns";

/**
 * Route wrapper for /practice-words/:slug.
 *
 * The route is dynamic at runtime, but scripts/prerender.mjs expands one
 * static URL per pattern from phonicsPatterns.ts so each page ships as real
 * HTML with its own title and canonical.
 */
const PracticeWordsPage = () => {
  const { slug } = useParams<{ slug: string }>();
  const pattern = slug ? getPatternBySlug(slug) : undefined;

  if (!pattern) {
    return <Navigate to="/practice-words" replace />;
  }

  return <PracticePageTemplate pattern={pattern} />;
};

export default PracticeWordsPage;
