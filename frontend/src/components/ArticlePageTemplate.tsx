import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Clock,
  Calendar,
  ArrowRight,
  BookOpen,
  Share2,
  Facebook,
  Twitter,
  Linkedin,
  Mail,
  AlertCircle,
  CheckCircle,
  Info as InfoIcon,
  Lightbulb,
} from "lucide-react";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";

// ===== TYPES & INTERFACES =====

interface Breadcrumb {
  label: string;
  href: string;
}

interface Author {
  name: string;
  bio: string;
  avatar?: string;
}

interface RelatedArticle {
  title: string;
  href: string;
  category: string;
  readTime: number;
}

interface InlineCTA {
  afterSection: number; // Insert after which section (0-indexed)
  title: string;
  description: string;
  buttonText: string;
  buttonHref: string;
}

interface CalloutBox {
  type: "info" | "tip" | "warning" | "success";
  title?: string;
  content: string;
}

interface ArticleImage {
  src: string;
  alt: string;
  caption?: string;
}

export interface ArticleSection {
  type: "heading" | "paragraph" | "list" | "image" | "callout" | "subsection";
  level?: 2 | 3; // For headings
  content: string | string[] | ArticleImage | CalloutBox;
  id?: string; // For TOC anchors
}

interface ArticlePageProps {
  // Meta tags
  metaTitle: string;
  metaDescription: string;
  canonicalUrl: string;
  ogImage?: string;

  // Hero section
  heroImage: string;
  heroImageAlt: string;
  headline: string;
  subheadline?: string;

  // Author & metadata
  author: Author;
  publishDate: string; // ISO format
  readTime: number; // minutes

  // Content
  category: string;
  content: ArticleSection[];

  // Sidebar
  relatedArticles?: RelatedArticle[];

  // SEO
  structuredData: any; // JSON-LD
  breadcrumbs: Breadcrumb[];

  // CTAs
  inlineCTAs?: InlineCTA[];
}

// ===== SUBCOMPONENTS =====

const BreadcrumbNav: React.FC<{ breadcrumbs: Breadcrumb[] }> = ({
  breadcrumbs,
}) => (
  <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
    {breadcrumbs.map((crumb, idx) => (
      <React.Fragment key={idx}>
        {idx > 0 && <span>/</span>}
        {idx === breadcrumbs.length - 1 ? (
          <span className="text-foreground">{crumb.label}</span>
        ) : (
          <Link
            to={crumb.href}
            className="hover:text-foreground transition-colors"
          >
            {crumb.label}
          </Link>
        )}
      </React.Fragment>
    ))}
  </nav>
);

const ArticleHero: React.FC<{
  heroImage: string;
  heroImageAlt: string;
  headline: string;
  subheadline?: string;
  category: string;
  author: Author;
  publishDate: string;
  readTime: number;
}> = ({
  heroImage,
  heroImageAlt,
  headline,
  subheadline,
  category,
  author,
  publishDate,
  readTime,
}) => {
  const formattedDate = new Date(publishDate).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="mb-12">
      {/* Hero Image */}
      <div className="w-full h-[300px] md:h-[400px] lg:h-[500px] overflow-hidden rounded-lg mb-8">
        <img
          src={heroImage}
          alt={heroImageAlt}
          className="w-full h-full object-cover"
          loading="eager"
        />
      </div>

      {/* Category & Metadata */}
      <div className="max-w-4xl mx-auto">
        <Badge variant="outline" className="mb-4">
          <BookOpen className="w-3 h-3 mr-1" />
          {category}
        </Badge>

        {/* Headline */}
        <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 text-foreground leading-tight">
          {headline}
        </h1>

        {/* Subheadline */}
        {subheadline && (
          <p className="text-lg md:text-xl text-muted-foreground mb-6">
            {subheadline}
          </p>
        )}

        {/* Author & Meta */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            {author.avatar && (
              <img
                src={author.avatar}
                alt={author.name}
                className="w-8 h-8 rounded-full"
              />
            )}
            <span className="font-medium text-foreground">{author.name}</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            <span>{formattedDate}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{readTime} min read</span>
          </div>
        </div>

        <Separator className="mt-6" />
      </div>
    </div>
  );
};

const TableOfContents: React.FC<{ sections: ArticleSection[] }> = ({
  sections,
}) => {
  const [activeId, setActiveId] = useState<string>("");

  // Extract headings for TOC
  const headings = sections.filter(
    (section) => section.type === "heading" && section.level === 2 && section.id
  );

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: "-100px 0px -80% 0px" }
    );

    headings.forEach((heading) => {
      if (heading.id) {
        const element = document.getElementById(heading.id);
        if (element) observer.observe(element);
      }
    });

    return () => observer.disconnect();
  }, []);

  if (headings.length === 0) return null;

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-base">Table of Contents</CardTitle>
      </CardHeader>
      <CardContent>
        <nav className="space-y-2">
          {headings.map((heading, idx) => (
            <a
              key={idx}
              href={`#${heading.id}`}
              className={`block text-sm py-1 px-2 rounded transition-colors ${
                activeId === heading.id
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              }`}
            >
              {heading.content as string}
            </a>
          ))}
        </nav>
      </CardContent>
    </Card>
  );
};

const CalloutBoxComponent: React.FC<{ callout: CalloutBox }> = ({
  callout,
}) => {
  const icons = {
    info: <InfoIcon className="w-5 h-5" />,
    tip: <Lightbulb className="w-5 h-5" />,
    warning: <AlertCircle className="w-5 h-5" />,
    success: <CheckCircle className="w-5 h-5" />,
  };

  const styles = {
    info: "bg-blue-50 border-blue-200 text-blue-900",
    tip: "bg-green-50 border-green-200 text-green-900",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-900",
    success: "bg-emerald-50 border-emerald-200 text-emerald-900",
  };

  return (
    <div className={`border-l-4 p-4 my-6 rounded ${styles[callout.type]}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">{icons[callout.type]}</div>
        <div>
          {callout.title && (
            <h4 className="font-semibold mb-1">{callout.title}</h4>
          )}
          <p className="text-sm">{callout.content}</p>
        </div>
      </div>
    </div>
  );
};

const InlineCTAComponent: React.FC<{ cta: InlineCTA }> = ({ cta }) => (
  <Card className="my-8 bg-primary/5 border-primary/20">
    <CardContent className="p-6">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="text-center md:text-left">
          <h3 className="text-lg font-semibold mb-2">{cta.title}</h3>
          <p className="text-sm text-muted-foreground">{cta.description}</p>
        </div>
        <Button asChild size="lg" className="flex-shrink-0">
          <Link to={cta.buttonHref}>
            {cta.buttonText}
            <ArrowRight className="ml-2 w-4 h-4" />
          </Link>
        </Button>
      </div>
    </CardContent>
  </Card>
);

const RelatedArticlesComponent: React.FC<{ articles: RelatedArticle[] }> = ({
  articles,
}) => (
  <Card className="mb-6">
    <CardHeader>
      <CardTitle className="text-base">Related Articles</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="space-y-4">
        {articles.map((article, idx) => (
          <Link
            key={idx}
            to={article.href}
            className="block p-3 rounded hover:bg-muted transition-colors"
          >
            <Badge variant="outline" className="mb-2 text-xs">
              {article.category}
            </Badge>
            <h4 className="text-sm font-medium mb-1 line-clamp-2">
              {article.title}
            </h4>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{article.readTime} min</span>
            </div>
          </Link>
        ))}
      </div>
    </CardContent>
  </Card>
);

const ShareButtons: React.FC<{ url: string; title: string }> = ({
  url,
  title,
}) => {
  const shareUrls = {
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(
      url
    )}&text=${encodeURIComponent(title)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(
      url
    )}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(
      url
    )}`,
    email: `mailto:?subject=${encodeURIComponent(
      title
    )}&body=${encodeURIComponent(url)}`,
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Share2 className="w-4 h-4" />
          Share This Article
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" asChild>
            <a
              href={shareUrls.twitter}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Twitter className="w-4 h-4" />
            </a>
          </Button>
          <Button size="sm" variant="outline" asChild>
            <a
              href={shareUrls.facebook}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Facebook className="w-4 h-4" />
            </a>
          </Button>
          <Button size="sm" variant="outline" asChild>
            <a
              href={shareUrls.linkedin}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Linkedin className="w-4 h-4" />
            </a>
          </Button>
          <Button size="sm" variant="outline" asChild>
            <a href={shareUrls.email}>
              <Mail className="w-4 h-4" />
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

const AuthorBio: React.FC<{ author: Author }> = ({ author }) => (
  <Card className="mb-6">
    <CardHeader>
      <CardTitle className="text-base">About the Author</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="flex items-start gap-3">
        {author.avatar && (
          <img
            src={author.avatar}
            alt={author.name}
            className="w-12 h-12 rounded-full flex-shrink-0"
          />
        )}
        <div>
          <h4 className="font-semibold mb-1">{author.name}</h4>
          <p className="text-sm text-muted-foreground">{author.bio}</p>
        </div>
      </div>
    </CardContent>
  </Card>
);

// ===== MAIN COMPONENT =====

const ArticlePageTemplate: React.FC<ArticlePageProps> = ({
  metaTitle,
  metaDescription,
  canonicalUrl,
  ogImage,
  heroImage,
  heroImageAlt,
  headline,
  subheadline,
  author,
  publishDate,
  readTime,
  category,
  content,
  relatedArticles,
  structuredData,
  breadcrumbs,
  inlineCTAs = [],
}) => {
  const renderSection = (section: ArticleSection, idx: number) => {
    // Check if there's a CTA to insert after this section
    const ctaAfterSection = inlineCTAs.find((cta) => cta.afterSection === idx);

    switch (section.type) {
      case "heading":
        const HeadingTag = `h${section.level}` as
          | "h1"
          | "h2"
          | "h3"
          | "h4"
          | "h5"
          | "h6";
        const headingClasses =
          section.level === 2
            ? "text-3xl md:text-4xl font-bold mt-12 mb-6 text-foreground border-b-2 border-primary/20 pb-3"
            : "text-lg md:text-xl font-semibold mt-8 mb-4 text-foreground/90 pl-4 border-l-4 border-primary/40";

        return (
          <React.Fragment key={idx}>
            <HeadingTag id={section.id} className={headingClasses}>
              {section.content as string}
            </HeadingTag>
            {ctaAfterSection && <InlineCTAComponent cta={ctaAfterSection} />}
          </React.Fragment>
        );

      case "paragraph":
        return (
          <React.Fragment key={idx}>
            <p className="text-base md:text-lg leading-relaxed text-foreground/90 mb-4">
              {section.content as string}
            </p>
            {ctaAfterSection && <InlineCTAComponent cta={ctaAfterSection} />}
          </React.Fragment>
        );

      case "list":
        const items = section.content as string[];
        return (
          <React.Fragment key={idx}>
            <ul className="list-disc list-outside ml-6 mb-6 space-y-2">
              {items.map((item, itemIdx) => (
                <li
                  key={itemIdx}
                  className="text-base md:text-lg text-foreground/90"
                >
                  {item}
                </li>
              ))}
            </ul>
            {ctaAfterSection && <InlineCTAComponent cta={ctaAfterSection} />}
          </React.Fragment>
        );

      case "image":
        const image = section.content as ArticleImage;
        return (
          <React.Fragment key={idx}>
            <figure className="my-8">
              <img
                src={image.src}
                alt={image.alt}
                className="w-full rounded-lg"
                loading="lazy"
              />
              {image.caption && (
                <figcaption className="text-sm text-center text-muted-foreground mt-2">
                  {image.caption}
                </figcaption>
              )}
            </figure>
            {ctaAfterSection && <InlineCTAComponent cta={ctaAfterSection} />}
          </React.Fragment>
        );

      case "callout":
        return (
          <React.Fragment key={idx}>
            <CalloutBoxComponent callout={section.content as CalloutBox} />
            {ctaAfterSection && <InlineCTAComponent cta={ctaAfterSection} />}
          </React.Fragment>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <Helmet>
        <title>{metaTitle}</title>
        <meta name="description" content={metaDescription} />
        <link rel="canonical" href={canonicalUrl} />
        <meta property="og:url" content={canonicalUrl} />
        <meta property="og:title" content={metaTitle} />
        <meta property="og:description" content={metaDescription} />
        <meta property="og:type" content="article" />
        {ogImage && <meta property="og:image" content={ogImage} />}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={metaTitle} />
        <meta name="twitter:description" content={metaDescription} />
        {ogImage && <meta name="twitter:image" content={ogImage} />}
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      </Helmet>

      <div className="min-h-screen flex flex-col bg-background">
        <LandingPageNavbar />

        <main className="flex-1">
          <article className="container mx-auto px-4 py-8 max-w-7xl">
            {/* Breadcrumbs */}
            <BreadcrumbNav breadcrumbs={breadcrumbs} />

            {/* Hero Section */}
            <ArticleHero
              heroImage={heroImage}
              heroImageAlt={heroImageAlt}
              headline={headline}
              subheadline={subheadline}
              category={category}
              author={author}
              publishDate={publishDate}
              readTime={readTime}
            />

            {/* Two-column layout (desktop) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 max-w-6xl mx-auto">
              {/* Main Content */}
              <div className="lg:col-span-8">
                <div className="prose prose-lg max-w-none">
                  {content.map((section, idx) => renderSection(section, idx))}
                </div>

                {/* Final CTA */}
                <Card className="mt-12 bg-primary text-primary-foreground">
                  <CardContent className="p-8 text-center">
                    <h3 className="text-2xl font-bold mb-4">
                      Ready to Help Your Child Read Better?
                    </h3>
                    <p className="mb-6 text-primary-foreground/90">
                      Try Word Wiz AI's free pronunciation feedback and phonics
                      practice
                    </p>
                    <Button size="lg" variant="secondary" asChild>
                      <Link to="/signup">
                        Get Started Free
                        <ArrowRight className="ml-2 w-4 h-4" />
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              </div>

              {/* Sidebar */}
              <aside className="lg:col-span-4">
                <div className="space-y-6">
                  <TableOfContents sections={content} />
                  <ShareButtons url={canonicalUrl} title={headline} />
                  <AuthorBio author={author} />
                  {relatedArticles && relatedArticles.length > 0 && (
                    <RelatedArticlesComponent articles={relatedArticles} />
                  )}
                </div>
              </aside>
            </div>
          </article>
        </main>

        <LandingPageFooter />
      </div>
    </>
  );
};

export default ArticlePageTemplate;
