/**
 * Type definitions for SEO page data.
 *
 * These types define the structure of data files that replace
 * the 40 individual SEO page components.
 */

import type { ArticleSection } from "@/components/ArticlePageTemplate";

export interface Author {
  name: string;
  bio: string;
  avatar?: string;
}

export interface RelatedArticle {
  title: string;
  href: string;
  category: string;
  readTime: number;
}

export interface Breadcrumb {
  label: string;
  href: string;
}

export interface SEOPageData {
  // URL slug (e.g., "free-phonics-apps-vs-paid-reading-programs")
  slug: string;

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
}

export interface ComparisonPageData extends SEOPageData {
  category: "App Comparisons";
}

export interface ArticlePageData extends SEOPageData {
  category: "Reading Problems" | "Reading Tips" | "Phonics Guide";
}

export interface GuidePageData extends SEOPageData {
  category: "Parent Guides" | "Teaching Resources";
}
