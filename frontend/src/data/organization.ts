/**
 * The Organization node for JSON-LD, shared by the homepage and About page.
 *
 * Search and answer engines decide which listings belong to which company by
 * matching sameAs links and a stable @id. Two pages describing Word Wiz with
 * different names, descriptions and profile lists makes that harder, so there
 * is one copy. Only list profiles Word Wiz actually controls or is listed on.
 */
export const ORGANIZATION_ID = "https://wordwizai.com/#organization";

export const ORGANIZATION_SCHEMA = {
  "@type": "Organization",
  "@id": ORGANIZATION_ID,
  name: "Word Wiz AI",
  url: "https://wordwizai.com/",
  // SVG because the PNG favicon is under Google's 112px logo minimum.
  logo: "https://wordwizai.com/wordwizIcon.svg",
  description:
    "A free, browser-based AI reading tutor for children ages 5-8. It listens to a child read aloud and gives feedback on the specific sounds they missed.",
  email: "contactwordwizai@gmail.com",
  founder: {
    "@type": "Person",
    name: "Bruce Peters",
  },
  sameAs: [
    "https://instagram.com/wordwizai",
    "https://github.com/wordwizai",
    "https://www.producthunt.com/products/word-wiz",
    "https://www.saashub.com/word-wiz-ai",
    "https://alternativeto.net/software/word-wiz-ai/about/",
  ],
};
