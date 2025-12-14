import React from "react";
import ComparisonPage from "@/components/ComparisonPageTemplate";

const ABCmouseHookedOnPhonicsComparison = () => {
  const product1 = {
    name: "ABCmouse",
    tagline: "Comprehensive early learning for ages 2-8",
    pricing: {
      free: "$0 (30-day trial)",
      paid: "$14.99/mo or $45/yr",
      trial: "30 days free",
    },
    rating: 4.6,
    reviewCount: 50000,
    website: "https://www.abcmouse.com",
  };

  const product2 = {
    name: "Hooked on Phonics",
    tagline: "Systematic phonics program with physical materials",
    pricing: {
      free: "$1 first month",
      paid: "$19.99/mo + materials",
      trial: "$1 trial month",
    },
    rating: 4.5,
    reviewCount: 15000,
    website: "https://www.hookedonphonics.com",
  };

  const wordWiz = {
    name: "Word Wiz AI",
    tagline: "AI-powered phoneme-level pronunciation feedback",
    pricing: {
      free: "Free forever",
      paid: "Premium features available",
    },
    rating: 4.8,
    reviewCount: 2500,
    website: "https://wordwizai.com",
  };

  const comparisonFeatures = [
    {
      category: "Core Technology & Features",
      features: [
        {
          name: "Speech Recognition",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Phoneme-Level Analysis",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "AI-Powered Feedback",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Real-Time Pronunciation Coaching",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Adaptive Learning",
          product1: "Limited",
          product2: false,
          wordWiz: true,
        },
        {
          name: "Web-Based (No Download)",
          product1: true,
          product2: false,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Content & Curriculum",
      features: [
        {
          name: "Phonics Instruction",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Systematic Phonics Approach",
          product1: "Partial",
          product2: true,
          wordWiz: true,
        },
        {
          name: "Decodable Stories",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Reading Comprehension",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Math & Other Subjects",
          product1: true,
          product2: "Limited",
          wordWiz: false,
        },
        {
          name: "Physical Materials Included",
          product1: false,
          product2: true,
          wordWiz: false,
        },
        {
          name: "AI-Generated Content",
          product1: false,
          product2: false,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Learning Experience",
      features: [
        {
          name: "Interactive Games",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Videos & Animations",
          product1: true,
          product2: true,
          wordWiz: "Limited",
        },
        {
          name: "Songs & Music",
          product1: true,
          product2: true,
          wordWiz: false,
        },
        {
          name: "Rewards System",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Custom Avatars",
          product1: true,
          product2: false,
          wordWiz: false,
        },
        {
          name: "Speaking Practice Required",
          product1: false,
          product2: false,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Progress Tracking & Reporting",
      features: [
        {
          name: "Progress Dashboard",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Detailed Analytics",
          product1: true,
          product2: "Basic",
          wordWiz: true,
        },
        {
          name: "Phoneme-Level Error Reports",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Teacher Dashboard",
          product1: "School edition",
          product2: false,
          wordWiz: true,
        },
        {
          name: "Multi-Child Support",
          product1: true,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Platform & Accessibility",
      features: [
        { name: "Works on iOS", product1: true, product2: true, wordWiz: true },
        {
          name: "Works on Android",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Works in Web Browser",
          product1: true,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Offline Mode",
          product1: "App only",
          product2: "App only",
          wordWiz: false,
        },
        {
          name: "Requires Microphone",
          product1: false,
          product2: false,
          wordWiz: true,
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Comprehensive curriculum covering multiple subjects" },
      { text: "10,000+ activities and extensive content library" },
      { text: "Proven track record (15+ years in market)" },
      { text: "High production quality with professional animations" },
      { text: "Affordable annual pricing ($3.75/mo)" },
      { text: "Great for well-rounded early education" },
    ],
    cons: [
      { text: "No speech recognition or pronunciation analysis" },
      { text: "Generic feedback without personalization" },
      { text: "Subscription required after trial" },
      { text: "Can be overwhelming with too much content" },
      { text: "Not focused specifically on phonics" },
    ],
    bestFor: [
      "Parents wanting comprehensive multi-subject learning",
      "Families seeking entertainment + education",
      "Children who enjoy varied activities",
    ],
    description:
      "ABCmouse is a comprehensive early learning platform covering reading, math, science, and art. With over 10,000 activities, it offers breadth but lacks the specialized phonics focus and speech analysis of dedicated reading programs.",
  };

  const product2Details = {
    pros: [
      { text: "Systematic, research-backed phonics instruction" },
      { text: "35+ years of proven effectiveness" },
      { text: "Physical materials (workbooks, flashcards, books)" },
      { text: "Decodable storybooks matched to learned skills" },
      { text: "Complete program with no additional materials needed" },
      { text: "Strong brand trust and reputation" },
    ],
    cons: [
      { text: "Expensive compared to digital-only options" },
      { text: "No speech recognition technology" },
      { text: "Requires app download (not web-based)" },
      { text: "Physical materials can pile up" },
      { text: "Manual parent assessment of pronunciation" },
    ],
    bestFor: [
      "Parents preferring traditional + digital learning",
      "Families wanting tangible materials",
      "Children who benefit from hands-on practice",
    ],
    description:
      "Hooked on Phonics is a time-tested phonics program combining digital games with physical workbooks and books. While effective for systematic phonics, it lacks modern speech recognition technology.",
  };

  const wordWizDetails = {
    pros: [
      { text: "Only app with phoneme-level speech recognition" },
      { text: "AI-powered personalized feedback (GPT-4)" },
      { text: "Free core features (no subscription required)" },
      { text: "Real-time pronunciation coaching" },
      { text: "Web-based (works on any device)" },
      { text: "Specifically designed for phonics mastery" },
      { text: "Teacher dashboard with class management" },
    ],
    cons: [
      { text: "Requires microphone and stable internet" },
      { text: "Focused on reading only (not multi-subject)" },
      { text: "Newer platform (less brand recognition)" },
      { text: "Limited entertainment features compared to games" },
    ],
    bestFor: [
      "Children struggling with pronunciation",
      "Parents wanting precise, data-driven feedback",
      "Teachers needing student progress insights",
      "Families seeking free speech recognition tools",
    ],
    description:
      "Word Wiz AI is the only reading platform using advanced speech recognition to analyze pronunciation at the phoneme level. Powered by wav2vec2-TIMIT-IPA models and GPT-4, it provides precise, personalized feedback that generic apps cannot match.",
  };

  const verdict = {
    product1:
      "Choose ABCmouse if you want a comprehensive, multi-subject early learning platform with thousands of activities. It's great for well-rounded education but won't specifically help with pronunciation challenges.",
    product2:
      "Choose Hooked on Phonics if you prefer a traditional, systematic phonics program with physical materials and don't mind a higher price point. It's effective but requires manual parent involvement for pronunciation assessment.",
    wordWiz:
      "Choose Word Wiz AI if you want cutting-edge speech recognition technology that actually listens to your child read and provides phoneme-level feedback. It's the only free option offering AI-powered pronunciation coaching.",
    overall:
      "For families specifically concerned about pronunciation and phonics mastery, Word Wiz AI is the clear winner. While ABCmouse offers breadth and Hooked on Phonics offers tradition, only Word Wiz AI provides the precision of AI-powered speech analysis. Plus, it's free to use, making advanced technology accessible to all families.",
  };

  const faqs = [
    {
      question: "Does ABCmouse or Hooked on Phonics have speech recognition?",
      answer:
        "No, neither ABCmouse nor Hooked on Phonics includes speech recognition technology. Both rely on point-and-click activities and parent assessment. Word Wiz AI is the only platform among the three that uses advanced speech recognition to analyze pronunciation.",
    },
    {
      question: "Which is best for a child struggling with pronunciation?",
      answer:
        'Word Wiz AI is specifically designed for pronunciation challenges. Its phoneme-level speech analysis can identify exactly which sounds a child struggles with (like "th" vs "f") and provide targeted feedback. ABCmouse and Hooked on Phonics offer general phonics instruction but cannot diagnose specific pronunciation issues.',
    },
    {
      question: "Are these programs suitable for different age groups?",
      answer:
        "ABCmouse targets ages 2-8 with broad curriculum, Hooked on Phonics focuses on ages 3-8 for systematic phonics, and Word Wiz AI is optimized for ages 4-10 who are actively learning to read. Word Wiz AI is particularly effective for children who can already speak but need help refining pronunciation.",
    },
    {
      question:
        "Can I use Word Wiz AI alongside ABCmouse or Hooked on Phonics?",
      answer:
        "Absolutely! Word Wiz AI complements other programs by providing the speech recognition and pronunciation feedback they lack. Many families use ABCmouse or Hooked on Phonics for content variety and Word Wiz AI for targeted pronunciation practice.",
    },
    {
      question: "Which offers the best value for money?",
      answer:
        "Word Wiz AI offers the best value with free core features including speech recognition. ABCmouse is affordable at $45/year but requires ongoing subscription. Hooked on Phonics is the most expensive at ~$20/month plus physical materials. For speech technology specifically, Word Wiz AI provides capabilities worth hundreds of dollars for free.",
    },
    {
      question: "Do I need special equipment for these programs?",
      answer:
        "ABCmouse and Hooked on Phonics work with standard devices (tablet, computer, smartphone). Word Wiz AI additionally requires a working microphone for speech recognition, which most devices have built-in. All three need internet connectivity.",
    },
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ComparisonPage",
    name: "ABCmouse vs Hooked on Phonics vs Word Wiz AI",
    description:
      "Comprehensive comparison of ABCmouse, Hooked on Phonics, and Word Wiz AI for teaching children to read",
    mainEntity: [
      {
        "@type": "Product",
        name: "ABCmouse",
        description: product1Details.description,
        offers: {
          "@type": "Offer",
          price: "14.99",
          priceCurrency: "USD",
          availability: "https://schema.org/InStock",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.6",
          reviewCount: "50000",
        },
      },
      {
        "@type": "Product",
        name: "Hooked on Phonics",
        description: product2Details.description,
        offers: {
          "@type": "Offer",
          price: "19.99",
          priceCurrency: "USD",
          availability: "https://schema.org/InStock",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.5",
          reviewCount: "15000",
        },
      },
      {
        "@type": "Product",
        name: "Word Wiz AI",
        description: wordWizDetails.description,
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD",
          availability: "https://schema.org/InStock",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.8",
          reviewCount: "2500",
        },
      },
    ],
  };

  return (
    <ComparisonPage
      product1={product1}
      product2={product2}
      wordWiz={wordWiz}
      comparisonFeatures={comparisonFeatures}
      product1Details={product1Details}
      product2Details={product2Details}
      wordWizDetails={wordWizDetails}
      metaTitle="ABCmouse vs Hooked on Phonics vs Word Wiz AI (2025): Which is Best?"
      metaDescription="Detailed comparison of ABCmouse, Hooked on Phonics, and Word Wiz AI. Compare features, pricing, speech recognition, and effectiveness. See which reading program is right for your child."
      canonicalUrl="https://wordwizai.com/comparisons/abcmouse-vs-hooked-on-phonics"
      h1Title="ABCmouse vs Hooked on Phonics vs Word Wiz AI: Complete Comparison (2025)"
      introText="Choosing between ABCmouse's comprehensive curriculum, Hooked on Phonics' traditional approach, or Word Wiz AI's cutting-edge speech recognition? This detailed comparison covers features, pricing, effectiveness, and helps you decide which reading program is best for your child."
      verdict={verdict}
      faqs={faqs}
      structuredData={structuredData}
    />
  );
};

export default ABCmouseHookedOnPhonicsComparison;
