import ComparisonPage from "@/components/ComparisonPageTemplate";

const ReadingEggsStarfallComparison = () => {
  const product1 = {
    name: "Reading Eggs",
    tagline: "Online reading program with 220+ lessons",
    pricing: {
      free: "$0 (30-day trial)",
      paid: "$12.99/mo or $79.99/yr",
      trial: "30 days free",
    },
    rating: 4.4,
    reviewCount: 35000,
    website: "https://readingeggs.com",
  };

  const product2 = {
    name: "Starfall",
    tagline: "Free nonprofit educational platform",
    pricing: {
      free: "Free (limited)",
      paid: "$60/yr for full access",
      trial: "Free tier available",
    },
    rating: 4.7,
    reviewCount: 28000,
    website: "https://www.starfall.com",
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
          name: "AI-Powered Personalization",
          product1: "Algorithmic",
          product2: false,
          wordWiz: "GPT-4",
        },
        {
          name: "Real-Time Pronunciation Feedback",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Web-Based Platform",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "No Download Required",
          product1: true,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Content & Curriculum",
      features: [
        {
          name: "Structured Lessons",
          product1: "220+",
          product2: "850+",
          wordWiz: "Unlimited",
        },
        {
          name: "Phonics Instruction",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Digital Book Library",
          product1: "2,500+",
          product2: "Included",
          wordWiz: "AI-generated",
        },
        {
          name: "Spelling Practice",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Math Content",
          product1: "Mathseeds",
          product2: true,
          wordWiz: false,
        },
        {
          name: "Decodable Stories",
          product1: true,
          product2: true,
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
          name: "Gamification (Rewards)",
          product1: "Golden eggs",
          product2: "Minimal",
          wordWiz: "Achievements",
        },
        {
          name: "Untimed Activities",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Speaking Required",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Multiple Choice Quizzes",
          product1: true,
          product2: true,
          wordWiz: "Limited",
        },
      ],
    },
    {
      category: "Accessibility & Special Needs",
      features: [
        {
          name: "Dyslexia-Friendly",
          product1: "Partial",
          product2: "Designed for",
          wordWiz: true,
        },
        {
          name: "Multisensory Approach",
          product1: true,
          product2: "Strong focus",
          wordWiz: true,
        },
        {
          name: "No Pressure/Competitive Elements",
          product1: false,
          product2: true,
          wordWiz: "Adaptable",
        },
        {
          name: "Ad-Free Experience",
          product1: true,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Progress & Reporting",
      features: [
        {
          name: "Parent Dashboard",
          product1: true,
          product2: "Paid tier",
          wordWiz: true,
        },
        {
          name: "Teacher Tools",
          product1: "School edition",
          product2: "School edition",
          wordWiz: true,
        },
        {
          name: "Phoneme Error Analysis",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Progress Reports",
          product1: "Detailed",
          product2: "Basic",
          wordWiz: "Detailed",
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "220 structured lessons with clear progression" },
      { text: "2,500+ digital books in library" },
      { text: "Used globally in schools and homes" },
      { text: "Affordable mid-range pricing" },
      { text: "Age range 2-13 (Reading Eggs + Express)" },
      { text: "Multi-child family plans available" },
    ],
    cons: [
      { text: "No speech recognition for pronunciation" },
      { text: "Repetitive game mechanics" },
      { text: "Multiple choice doesn't catch reading errors" },
      { text: "Subscription required after trial" },
      { text: "Interface can feel dated" },
    ],
    bestFor: [
      "Parents wanting structured online curriculum",
      "International families (global reach)",
      "Families with multiple children",
    ],
    description:
      "Reading Eggs is a comprehensive online reading program with 220+ lessons, 2,500+ books, and a wide age range. It offers solid phonics instruction but lacks speech recognition technology.",
  };

  const product2Details = {
    pros: [
      { text: "Free tier available (no cost barrier)" },
      { text: "Nonprofit mission (education for all)" },
      { text: "Specifically designed for dyslexia" },
      { text: "Multisensory, untimed activities" },
      { text: "Trusted by educators nationwide" },
      { text: "No ads or data collection (COPPA compliant)" },
    ],
    cons: [
      { text: "No speech recognition technology" },
      { text: "Interface feels dated compared to modern apps" },
      { text: "Limited personalization (no AI)" },
      { text: "Best features require paid membership" },
      { text: "No progress tracking in free tier" },
    ],
    bestFor: [
      "Budget-conscious families seeking free options",
      "Children with dyslexia or learning differences",
      "Parents preferring nonprofit platforms",
    ],
    description:
      "Starfall is a nonprofit educational platform founded by someone with dyslexia. It offers multisensory, untimed activities with a strong accessibility focus, but lacks modern AI and speech technology.",
  };

  const wordWizDetails = {
    pros: [
      { text: "Only platform with phoneme-level speech analysis" },
      { text: "Free core features including speech recognition" },
      { text: "GPT-4 powered personalized feedback" },
      { text: "Real-time pronunciation coaching" },
      { text: "Works in any web browser" },
      { text: "Teacher dashboard with class management" },
      { text: "Unlimited AI-generated practice sentences" },
    ],
    cons: [
      { text: "Requires microphone for speech recognition" },
      { text: "Internet connection required" },
      { text: "Focused on phonics/reading only" },
      { text: "Newer platform with smaller user base" },
    ],
    bestFor: [
      "Children with pronunciation challenges",
      "Parents wanting data-driven feedback",
      "Budget-conscious families needing speech tech",
      "Teachers tracking student phoneme mastery",
    ],
    description:
      "Word Wiz AI is the only free reading platform offering advanced speech recognition and phoneme-level analysis. Powered by wav2vec2-TIMIT-IPA and GPT-4, it provides precision coaching that passive programs cannot match.",
  };

  const verdict = {
    product1:
      "Choose Reading Eggs if you want a comprehensive, structured online curriculum with thousands of activities and books. It's solid for general reading instruction but won't analyze pronunciation.",
    product2:
      "Choose Starfall if you need a free, nonprofit option designed specifically for dyslexia and learning differences. It's accessible and trusted but lacks modern AI features.",
    wordWiz:
      "Choose Word Wiz AI if you want the only free platform with speech recognition and phoneme-level feedback. It combines the accessibility of Starfall with cutting-edge AI technology neither competitor offers.",
    overall:
      "For pronunciation mastery and speech feedback, Word Wiz AI is unmatched. While Reading Eggs offers curriculum breadth and Starfall offers accessibility, only Word Wiz AI provides AI-powered pronunciation coaching—and it's free. For families on a budget who need more than passive games, Word Wiz AI delivers professional-grade speech technology at no cost.",
  };

  const faqs = [
    {
      question: "Which program is completely free?",
      answer:
        "Starfall has a limited free tier, but best features require $60/year. Word Wiz AI offers core features including speech recognition completely free forever. Reading Eggs only offers a 30-day trial before requiring paid subscription.",
    },
    {
      question: "Do any of these programs have speech recognition?",
      answer:
        "Only Word Wiz AI has speech recognition. Neither Reading Eggs nor Starfall can listen to your child read or analyze pronunciation. They rely on clicking, typing, and multiple choice activities.",
    },
    {
      question: "Which is best for a child with dyslexia?",
      answer:
        "Starfall was specifically designed for dyslexia with multisensory, untimed activities. However, Word Wiz AI's phoneme-level feedback can be extremely valuable for dyslexic learners who struggle with specific sounds. Many families use both: Starfall for general activities and Word Wiz AI for targeted pronunciation practice.",
    },
    {
      question: "Can teachers use these in classrooms?",
      answer:
        "All three offer educator options. Reading Eggs and Starfall have school editions with pricing. Word Wiz AI includes free teacher dashboard with class management and student progress tracking, making it accessible for budget-limited schools.",
    },
    {
      question: "Which has the most content?",
      answer:
        "Reading Eggs has 2,500+ books and 220+ lessons. Starfall has 850+ activities. Word Wiz AI has unlimited AI-generated content—GPT-4 creates personalized practice sentences on demand, so you never run out of material.",
    },
    {
      question: "Are these programs web-based or app-based?",
      answer:
        "All three are web-based and work in browsers. Reading Eggs and Starfall also have mobile apps. Word Wiz AI is web-first, working on any device with a browser and microphone.",
    },
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ComparisonPage",
    name: "Reading Eggs vs Starfall vs Word Wiz AI",
    description:
      "Comprehensive comparison of Reading Eggs, Starfall, and Word Wiz AI for online reading education",
    mainEntity: [
      {
        "@type": "Product",
        name: "Reading Eggs",
        description: product1Details.description,
        offers: {
          "@type": "Offer",
          price: "12.99",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.4",
          reviewCount: "35000",
        },
      },
      {
        "@type": "Product",
        name: "Starfall",
        description: product2Details.description,
        offers: {
          "@type": "Offer",
          price: "60",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.7",
          reviewCount: "28000",
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
      metaTitle="Reading Eggs vs Starfall vs Word Wiz AI (2025): Which is Best?"
      metaDescription="Compare Reading Eggs, Starfall, and Word Wiz AI. See features, pricing, speech recognition, and which online reading program offers the best value for your child."
      canonicalUrl="https://wordwizai.com/comparisons/reading-eggs-vs-starfall"
      h1Title="Reading Eggs vs Starfall vs Word Wiz AI: Complete Comparison (2025)"
      introText="Comparing Reading Eggs' structured curriculum, Starfall's free nonprofit platform, or Word Wiz AI's speech recognition? This detailed analysis covers everything you need to choose the right online reading program for your family."
      verdict={verdict}
      faqs={faqs}
      structuredData={structuredData}
    />
  );
};

export default ReadingEggsStarfallComparison;
