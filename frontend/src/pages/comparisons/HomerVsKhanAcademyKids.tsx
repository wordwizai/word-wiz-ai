import ComparisonPage from "@/components/ComparisonPageTemplate";

const HomerKhanAcademyKidsComparison = () => {
  const product1 = {
    name: "HOMER",
    tagline: "Personalized learning for ages 2-8",
    pricing: {
      free: "$0 (30-day trial)",
      paid: "$12.99/mo or $79.99/yr",
      trial: "30 days free",
    },
    rating: 4.6,
    reviewCount: 22000,
    website: "https://learnwithhomer.com",
  };

  const product2 = {
    name: "Khan Academy Kids",
    tagline: "100% free learning app from Khan Academy",
    pricing: {
      free: "Free forever",
      paid: "N/A",
      trial: "All features free",
    },
    rating: 4.8,
    reviewCount: 45000,
    website: "https://www.khanacademykids.org",
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
      category: "AI & Personalization",
      features: [
        {
          name: "AI-Powered Personalization",
          product1: "Interest-based",
          product2: "Adaptive",
          wordWiz: "GPT-4",
        },
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
          name: "Real-Time Feedback",
          product1: "Activity-based",
          product2: "Activity-based",
          wordWiz: "Speech-based",
        },
        {
          name: "Interest-Based Content",
          product1: true,
          product2: "Limited",
          wordWiz: "Partial",
        },
        {
          name: "Adaptive Difficulty",
          product1: true,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Content & Subjects",
      features: [
        {
          name: "Reading & Phonics",
          product1: true,
          product2: true,
          wordWiz: "Specialized",
        },
        { name: "Math", product1: true, product2: true, wordWiz: false },
        {
          name: "Social-Emotional Learning",
          product1: true,
          product2: true,
          wordWiz: false,
        },
        {
          name: "Thinking Skills",
          product1: true,
          product2: true,
          wordWiz: false,
        },
        {
          name: "Creativity & Art",
          product1: true,
          product2: true,
          wordWiz: false,
        },
        {
          name: "Phonics Depth",
          product1: "Moderate",
          product2: "Moderate",
          wordWiz: "Advanced",
        },
      ],
    },
    {
      category: "Platform & Access",
      features: [
        {
          name: "iOS App",
          product1: true,
          product2: true,
          wordWiz: "Web-based",
        },
        {
          name: "Android App",
          product1: true,
          product2: true,
          wordWiz: "Web-based",
        },
        {
          name: "Web Browser Access",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Offline Mode",
          product1: "Downloaded",
          product2: "Downloaded",
          wordWiz: false,
        },
        {
          name: "No Download Required",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Requires Microphone",
          product1: false,
          product2: false,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Family Features",
      features: [
        {
          name: "Multiple Child Profiles",
          product1: "Up to 4",
          product2: "Unlimited",
          wordWiz: "Multiple",
        },
        {
          name: "Parent Progress Dashboard",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Offline Activities/Printables",
          product1: true,
          product2: "Limited",
          wordWiz: "Coming soon",
        },
        {
          name: "Educational Resources for Parents",
          product1: true,
          product2: "Limited",
          wordWiz: true,
        },
      ],
    },
    {
      category: "Learning Quality",
      features: [
        {
          name: "Research-Backed Curriculum",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Speaking Practice Required",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Pronunciation Correction",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Ad-Free Experience",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Safe for Kids (COPPA)",
          product1: true,
          product2: true,
          wordWiz: true,
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Highly personalized based on child interests" },
      { text: "Claims 74% improvement in reading scores" },
      { text: "Multi-subject coverage (reading, math, SEL)" },
      { text: "Up to 4 child profiles per subscription" },
      { text: "Engaging, joyful learning experience" },
      { text: "Offline activities and printables included" },
    ],
    cons: [
      { text: "No speech recognition for pronunciation" },
      { text: "App-only (no web browser version)" },
      { text: "Requires subscription after trial" },
      { text: "Limited phonics depth compared to specialists" },
      { text: "Best for younger kids (ages 2-6)" },
    ],
    bestFor: [
      "Parents wanting personalized multi-subject learning",
      "Families with children ages 2-6",
      "Parents seeking research-backed results",
    ],
    description:
      "HOMER is a personalized early learning app that adapts content to children's interests. While it offers strong multi-subject curriculum and claims impressive results, it lacks speech recognition technology.",
  };

  const product2Details = {
    pros: [
      { text: "100% free forever (no cost ever)" },
      { text: "Completely ad-free nonprofit platform" },
      { text: "Khan Academy brand trust and reputation" },
      { text: "Adaptive learning that adjusts to child" },
      { text: "Unlimited child profiles" },
      { text: "High-quality content with regular updates" },
    ],
    cons: [
      { text: "No speech recognition technology" },
      { text: "App-only (no web browser access)" },
      { text: "Limited phonics focus (broader curriculum)" },
      { text: "No pronunciation feedback" },
      { text: "Occasional bugs reported" },
    ],
    bestFor: [
      "Families seeking completely free options",
      "Parents wanting nonprofit, ad-free platform",
      "Anyone with limited budget",
    ],
    description:
      "Khan Academy Kids is a 100% free, nonprofit learning app from the trusted Khan Academy brand. It offers adaptive learning across subjects but lacks speech recognition for pronunciation practice.",
  };

  const wordWizDetails = {
    pros: [
      { text: "Only free app with speech recognition" },
      { text: "Phoneme-level pronunciation analysis" },
      { text: "GPT-4 powered personalized feedback" },
      { text: "Web-based (works on any device)" },
      { text: "No app download required" },
      { text: "Specialized for phonics and pronunciation" },
      { text: "Teacher dashboard for educators" },
    ],
    cons: [
      { text: "Requires microphone and internet" },
      { text: "Reading-focused only (not multi-subject)" },
      { text: "Newer platform with smaller community" },
      { text: "No offline mode" },
    ],
    bestFor: [
      "Children with pronunciation challenges",
      "Parents needing speech technology",
      "Teachers tracking phoneme mastery",
      "Budget-conscious families wanting AI features",
    ],
    description:
      "Word Wiz AI is the only free platform combining speech recognition with AI-powered feedback. Unlike HOMER and Khan Academy Kids, it actually listens to children read and provides phoneme-level coaching.",
  };

  const verdict = {
    product1:
      "Choose HOMER if you want personalized, interest-based learning across multiple subjects and can afford the subscription. It's engaging and effective but won't help with pronunciation.",
    product2:
      "Choose Khan Academy Kids if you want a completely free, high-quality multi-subject learning app from a trusted nonprofit. It's excellent for general education but lacks speech technology.",
    wordWiz:
      "Choose Word Wiz AI if you want the only free platform with speech recognition and phoneme-level feedback. While HOMER and Khan Kids offer breadth, only Word Wiz AI provides speech analysis depth.",
    overall:
      "For pronunciation and phonics mastery, Word Wiz AI is the clear choice among free options. Khan Academy Kids offers broad free learning, HOMER offers personalized paid learning, but only Word Wiz AI combines free access with advanced speech recognition technology. If your child needs more than games and videos—if they need actual pronunciation coaching—Word Wiz AI is unmatched.",
  };

  const faqs = [
    {
      question: "Which is completely free with no limitations?",
      answer:
        "Both Khan Academy Kids and Word Wiz AI are free. Khan Kids is 100% free for all features across all subjects. Word Wiz AI is free for core features including speech recognition, with optional premium features. HOMER requires paid subscription after 30-day trial.",
    },
    {
      question: "Do any of these apps have speech recognition?",
      answer:
        "Only Word Wiz AI has speech recognition technology. Neither HOMER nor Khan Academy Kids can listen to your child read or analyze pronunciation—they rely on tap-and-click activities.",
    },
    {
      question: "Which is best for personalized learning?",
      answer:
        "HOMER specializes in personalization based on interests (sports, princesses, space, etc.). Khan Academy Kids adapts difficulty level. Word Wiz AI uses GPT-4 to generate personalized feedback based on specific pronunciation errors—the only one that personalizes to actual speech patterns.",
    },
    {
      question: "Can I use these on a web browser or do I need an app?",
      answer:
        "HOMER and Khan Academy Kids are app-only (iOS/Android). Word Wiz AI is web-based, working in any browser without downloads. This makes Word Wiz AI more accessible across devices.",
    },
    {
      question: "Which is better for a struggling reader?",
      answer:
        "Word Wiz AI is specifically designed for pronunciation challenges. Its phoneme-level feedback identifies exactly which sounds a child struggles with. HOMER and Khan Academy Kids offer general reading content but cannot diagnose or correct specific pronunciation issues.",
    },
    {
      question: "Are these suitable for homeschooling?",
      answer:
        "All three work for homeschool. Khan Academy Kids is most comprehensive (free multi-subject). HOMER offers engaging personalization. Word Wiz AI provides the speech feedback that parents often can't deliver themselves—making it valuable for homeschool phonics instruction.",
    },
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ComparisonPage",
    name: "HOMER vs Khan Academy Kids vs Word Wiz AI",
    description:
      "Comparison of HOMER, Khan Academy Kids, and Word Wiz AI for personalized early learning",
    mainEntity: [
      {
        "@type": "Product",
        name: "HOMER",
        description: product1Details.description,
        offers: {
          "@type": "Offer",
          price: "12.99",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.6",
          reviewCount: "22000",
        },
      },
      {
        "@type": "Product",
        name: "Khan Academy Kids",
        description: product2Details.description,
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.8",
          reviewCount: "45000",
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
      metaTitle="HOMER vs Khan Academy Kids vs Word Wiz AI (2025): Free vs Paid"
      metaDescription="Compare HOMER's personalization, Khan Academy Kids' free platform, and Word Wiz AI's speech recognition. See which learning app is best for your child."
      canonicalUrl="https://wordwizai.com/comparisons/homer-vs-khan-academy-kids"
      h1Title="HOMER vs Khan Academy Kids vs Word Wiz AI: Personalized Learning Compared (2025)"
      introText="Evaluating HOMER's interest-based personalization, Khan Academy Kids' free comprehensive curriculum, or Word Wiz AI's speech recognition technology? This comparison helps you choose the right learning app for your child's needs."
      verdict={verdict}
      faqs={faqs}
      structuredData={structuredData}
    />
  );
};

export default HomerKhanAcademyKidsComparison;
