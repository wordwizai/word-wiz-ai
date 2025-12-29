import ComparisonPage from "@/components/ComparisonPageTemplate";

const IXLDuolingoABCComparison = () => {
  const product1 = {
    name: "IXL Language Arts",
    tagline: "Comprehensive PreK-12 language arts curriculum",
    pricing: {
      free: "7-day trial",
      paid: "$19.95/month or $79/year",
      trial: "7 days free",
    },
    rating: 4.1,
    reviewCount: 2800,
    website: "https://www.ixl.com",
  };

  const product2 = {
    name: "Duolingo ABC",
    tagline: "Free early literacy app from Duolingo",
    pricing: {
      free: "$0 (completely free, no ads)",
      paid: "No paid version",
      trial: "Free forever",
    },
    rating: 4.6,
    reviewCount: 15000,
    website: "https://www.duolingoabc.com",
  };

  const wordWiz = {
    name: "Word Wiz AI",
    tagline: "AI-powered pronunciation feedback with speech recognition",
    pricing: {
      free: "Free forever",
      paid: "All features free",
    },
    rating: 4.8,
    reviewCount: 250,
    website: "https://wordwizai.com",
  };

  const comparisonFeatures = [
    {
      category: "Scope & Coverage",
      features: [
        {
          name: "Age Range",
          product1: "PreK-12",
          product2: "3-7 years",
          wordWiz: "4-9 years",
        },
        {
          name: "Skill Count",
          product1: "8,000+ skills",
          product2: "~200 lessons",
          wordWiz: "Focused on pronunciation",
        },
        {
          name: "Curriculum Breadth",
          product1: "Comprehensive",
          product2: "Early literacy only",
          wordWiz: "Phonics & pronunciation",
        },
        {
          name: "Subject Coverage",
          product1: "All language arts",
          product2: "Reading basics",
          wordWiz: "Reading pronunciation",
        },
      ],
    },
    {
      category: "Technology & Features",
      features: [
        {
          name: "Speech Recognition",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Pronunciation Feedback",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Adaptive Learning",
          product1: "Algorithm-based",
          product2: "Progression-based",
          wordWiz: "AI-personalized",
        },
        {
          name: "AI Technology",
          product1: false,
          product2: false,
          wordWiz: "GPT-4",
        },
      ],
    },
    {
      category: "Learning Approach",
      features: [
        {
          name: "Systematic Phonics",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Gamification",
          product1: "Awards & certificates",
          product2: "Very high",
          wordWiz: "Moderate",
        },
        {
          name: "Practice Format",
          product1: "Questions & drills",
          product2: "Interactive games",
          wordWiz: "Read aloud practice",
        },
      ],
    },
    {
      category: "Platform & Access",
      features: [
        {
          name: "Web Browser",
          product1: true,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Mobile Apps",
          product1: "iOS & Android",
          product2: "iOS only",
          wordWiz: "Web (all devices)",
        },
        {
          name: "Offline Mode",
          product1: false,
          product2: true,
          wordWiz: false,
        },
      ],
    },
    {
      category: "Cost & Value",
      features: [
        {
          name: "Monthly Cost",
          product1: "$19.95",
          product2: "$0",
          wordWiz: "$0",
        },
        {
          name: "Annual Cost",
          product1: "$79",
          product2: "$0",
          wordWiz: "$0",
        },
        {
          name: "Free Tier",
          product1: "7-day trial only",
          product2: "Everything free",
          wordWiz: "Everything free",
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Comprehensive: 8,000+ skills covering all language arts areas" },
      { text: "PreK-12 range means it grows with your child" },
      { text: "Adaptive learning adjusts difficulty automatically" },
      { text: "Detailed analytics show exactly where child needs help" },
      { text: "Used in 1 million+ classrooms (trusted by schools)" },
      { text: "Aligned to Common Core and state standards" },
    ],
    cons: [
      { text: "Expensive: $19.95/month ongoing ($240/year)" },
      { text: "No speech recognition or pronunciation feedback" },
      { text: "Can feel drill-based and repetitive" },
      { text: "Overwhelming number of skills may frustrate some learners" },
      { text: "Requires ongoing subscription commitment" },
    ],
    bestFor: [
      "Families wanting comprehensive K-12 curriculum",
      "Multiple children at different grade levels",
      "Detailed progress tracking needs",
      "Supplementing school across all language arts",
      "Parents who can afford ongoing subscription",
    ],
    description:
      "IXL Language Arts is a comprehensive PreK-12 curriculum with 8,000+ skills covering phonics, reading comprehension, grammar, vocabulary, and writing. It's thorough and adaptive but expensive, and it doesn't offer speech recognition technology for pronunciation practice.",
  };

  const product2Details = {
    pros: [
      {
        text: "Completely free (no ads, no in-app purchases, no subscriptions)",
      },
      { text: "From trusted Duolingo brand" },
      { text: "Highly engaging for young children (ages 3-7)" },
      { text: "Systematic phonics progression" },
      { text: "Works offline (great for travel)" },
      { text: "Cute animations and characters kids love" },
    ],
    cons: [
      { text: "Limited to ages 3-7 (early literacy only)" },
      { text: "No speech recognition or pronunciation feedback" },
      { text: "iOS only (no Android or web version)" },
      { text: "Can't check if child is pronouncing correctly" },
      { text: "Minimal progress data for parents" },
    ],
    bestFor: [
      "Early readers (ages 3-7)",
      "Budget-conscious families (totally free)",
      "iPad/iPhone users",
      "Kids who love Duolingo's style",
      "Making phonics fun and engaging",
    ],
    description:
      "Duolingo ABC is a completely free early literacy app (ages 3-7) from the makers of Duolingo. It offers systematic phonics instruction in a fun, gamified format. However, it's iOS-only and doesn't include speech recognition to check pronunciation.",
  };

  const wordWizDetails = {
    pros: [
      { text: "100% free with all features including speech recognition" },
      { text: "ONLY option among these three with pronunciation feedback" },
      { text: "AI-powered with GPT-4 (most advanced technology)" },
      { text: "Works on all devices via web browser (not platform-limited)" },
      {
        text: "Phoneme-level analysis identifies specific pronunciation errors",
      },
      { text: "Science of Reading aligned" },
      { text: "Immediate, personalized feedback" },
    ],
    cons: [
      {
        text: "Narrower focus (pronunciation only, not full curriculum like IXL)",
      },
      { text: "Not as comprehensive as IXL for all language arts" },
      { text: "Less game-like than Duolingo ABC" },
      { text: "Requires microphone access" },
    ],
    bestFor: [
      "Pronunciation practice and assessment",
      "Supplementing IXL or Duolingo ABC with speech technology",
      "English Language Learners",
      "Budget-conscious families (free)",
      "Cross-device access (works on any device)",
      "Kids who can decode but mispronounce words",
    ],
    description:
      "Word Wiz AI is the specialist among these options—it does one thing excellently: pronunciation feedback through speech recognition. While not as comprehensive as IXL or as game-like as Duolingo ABC, it's the only free tool that actually listens and corrects pronunciation at the phoneme level.",
  };

  const verdict = {
    product1:
      "Best for families wanting comprehensive language arts curriculum that grows from PreK through 12th grade. The breadth is unmatched (8,000+ skills), but at $20/month, it's a significant investment. Worth it if you need full curriculum coverage, but doesn't include speech recognition.",
    product2:
      "Best for early literacy fun (ages 3-7) on a $0 budget. Kids love Duolingo's style, and it's completely free. Perfect for preschool through first grade, but limited to iOS devices and doesn't provide pronunciation feedback.",
    wordWiz:
      "Best for pronunciation feedback and speech technology. It's the only free option with actual speech recognition among these three. While narrower in scope than IXL, it's the most advanced technologically (GPT-4, phoneme-level analysis) and works on all devices.",
    overall:
      "These three serve different needs: IXL is comprehensive but expensive, Duolingo ABC is fun and free for early readers, and Word Wiz AI provides unique pronunciation feedback. The best free combination is Duolingo ABC (ages 3-7) + Word Wiz AI for pronunciation practice. If budget allows, add IXL for comprehensive coverage, using Word Wiz AI to fill IXL's pronunciation gap.",
  };

  const faqs = [
    {
      question: "Is IXL worth the $20/month cost?",
      answer:
        "IXL is worth it if you need comprehensive PreK-12 coverage across all language arts areas with detailed progress tracking. However, for pronunciation practice specifically, Word Wiz AI offers free speech recognition that IXL doesn't have. Consider combining both: Word Wiz AI (free, pronunciation) + IXL (paid, comprehensive).",
    },
    {
      question: "Is Duolingo ABC really 100% free?",
      answer:
        "Yes! Duolingo ABC is completely free with no ads, in-app purchases, or subscriptions. It's funded by Duolingo's main app revenue. The only limitation is that it's iOS-only (iPad/iPhone).",
    },
    {
      question: "Which has the best technology?",
      answer:
        "Word Wiz AI has the most advanced technology with GPT-4 AI and speech recognition for pronunciation feedback. Neither IXL nor Duolingo ABC can listen to your child read or provide pronunciation corrections—Word Wiz AI is the only option with this capability.",
    },
    {
      question: "Can I use these together?",
      answer:
        "Absolutely! Many families use Duolingo ABC for fun early literacy + Word Wiz AI for pronunciation feedback (both free), or IXL for comprehensive curriculum + Word Wiz AI for pronunciation practice. These tools complement rather than compete with each other.",
    },
    {
      question: "Which is best for a 5-year-old?",
      answer:
        "For ages 5-7, Duolingo ABC is perfect for engaging, systematic phonics. Add Word Wiz AI (also free) to practice pronunciation and ensure your child is saying sounds correctly. Together, they provide comprehensive early literacy support at $0 cost.",
    },
    {
      question: "Does any of these check pronunciation?",
      answer:
        "Only Word Wiz AI has speech recognition to check pronunciation. Neither IXL nor Duolingo ABC can listen to your child read or identify pronunciation errors. If pronunciation feedback is important to you, Word Wiz AI is your only free option.",
    },
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ComparisonPage",
    name: "IXL vs Duolingo ABC vs Word Wiz AI",
    description:
      "Compare IXL Language Arts, Duolingo ABC, and Word Wiz AI for teaching reading. See pricing, features, and which is right for your child.",
    mainEntity: [
      {
        "@type": "Product",
        name: "IXL Language Arts",
        description: "Comprehensive PreK-12 language arts curriculum",
        offers: {
          "@type": "Offer",
          price: "19.95",
          priceCurrency: "USD",
          priceSpecification: {
            "@type": "UnitPriceSpecification",
            referenceQuantity: {
              "@type": "QuantitativeValue",
              value: "1",
              unitText: "month",
            },
          },
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.1",
          reviewCount: "2800",
        },
      },
      {
        "@type": "Product",
        name: "Duolingo ABC",
        description: "Free early literacy app for ages 3-7",
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.6",
          reviewCount: "15000",
        },
      },
      {
        "@type": "Product",
        name: "Word Wiz AI",
        description: "Free AI-powered pronunciation feedback",
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.8",
          reviewCount: "250",
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
      metaTitle="IXL vs Duolingo ABC vs Word Wiz AI: Which is Best? (2024)"
      metaDescription="Compare IXL Language Arts, Duolingo ABC, and Word Wiz AI for teaching reading. See pricing, features, and which is right for your child. Free speech recognition option included."
      canonicalUrl="https://wordwizai.com/comparisons/ixl-vs-duolingo-abc-vs-word-wiz-ai"
      h1Title="IXL Language Arts vs Duolingo ABC vs Word Wiz AI: Comprehensive Comparison"
      introText="Comparing literacy programs for your child? See how IXL's comprehensive curriculum, Duolingo ABC's free gamified learning, and Word Wiz AI's unique speech recognition technology stack up. Find the right fit for your family's needs and budget."
      verdict={verdict}
      faqs={faqs}
      structuredData={structuredData}
    />
  );
};

export default IXLDuolingoABCComparison;
