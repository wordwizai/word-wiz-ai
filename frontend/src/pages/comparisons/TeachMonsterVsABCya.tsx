import ComparisonPage from "@/components/ComparisonPageTemplate";

const TeachMonsterABCyaComparison = () => {
  const product1 = {
    name: "Teach Your Monster to Read",
    tagline: "Award-winning free phonics game for ages 3-6",
    pricing: {
      free: "$0 (browser version)",
      paid: "$4.99 (mobile app, optional)",
      trial: "Free forever (web)",
    },
    rating: 4.7,
    reviewCount: 8500,
    website: "https://www.teachyourmonstertoread.com",
  };

  const product2 = {
    name: "ABCya",
    tagline: "Educational game portal with 400+ activities",
    pricing: {
      free: "$0 (with ads)",
      paid: "$99/year (ad-free)",
      trial: "Free tier available",
    },
    rating: 4.3,
    reviewCount: 12000,
    website: "https://www.abcya.com",
  };

  const wordWiz = {
    name: "Word Wiz AI",
    tagline: "Free speech recognition for pronunciation practice",
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
      category: "Educational Approach",
      features: [
        {
          name: "Systematic Phonics",
          product1: true,
          product2: false,
          wordWiz: true,
        },
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
          name: "Gamification Level",
          product1: "High (adventure game)",
          product2: "High (variety games)",
          wordWiz: "Moderate",
        },
      ],
    },
    {
      category: "Content & Coverage",
      features: [
        {
          name: "Age Range",
          product1: "3-6 years",
          product2: "3-12 years",
          wordWiz: "4-9 years",
        },
        {
          name: "Phonics Coverage",
          product1: "Comprehensive",
          product2: "Scattered games",
          wordWiz: "Systematic",
        },
        {
          name: "Subject Variety",
          product1: "Reading only",
          product2: "Math, science, art too",
          wordWiz: "Reading only",
        },
        {
          name: "Progress Tracking",
          product1: "Basic",
          product2: "Minimal",
          wordWiz: "Pronunciation data",
        },
      ],
    },
    {
      category: "Platform & Access",
      features: [
        {
          name: "Web Browser",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Mobile Apps",
          product1: "iOS/Android ($5)",
          product2: "iOS/Android",
          wordWiz: "Web (all devices)",
        },
        {
          name: "Offline Mode",
          product1: "App only",
          product2: "Premium only",
          wordWiz: false,
        },
        {
          name: "No Ads",
          product1: true,
          product2: "Premium ($99/yr)",
          wordWiz: true,
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Completely free on browser with no ads or in-app purchases" },
      { text: "Award-winning (BAFTA Children's Award 2018)" },
      { text: "Highly engaging adventure game keeps kids motivated" },
      {
        text: "Systematic phonics instruction aligned with Science of Reading",
      },
      { text: "Created by educators from UK's successful phonics program" },
      {
        text: "Kids genuinely love playing it (excellent for reluctant learners)",
      },
    ],
    cons: [
      {
        text: "No speech recognition (can't check if child pronounces correctly)",
      },
      { text: "Limited to early reading (ages 3-6, stops at basic phonics)" },
      { text: "UK English pronunciation may differ from US" },
      { text: "No feedback on reading aloud accuracy" },
      { text: "Limited progress data for parents" },
    ],
    bestFor: [
      "Preschool and kindergarten (ages 3-6)",
      "Making phonics fun and engaging",
      "Budget-conscious families (completely free)",
      "Kids who love games and need motivation",
      "Introducing phonics concepts in entertaining way",
    ],
    description:
      "Teach Your Monster to Read is an award-winning, completely free phonics game that makes learning to read fun. Kids create monsters and progress through adventures while learning systematic phonics. While it doesn't provide pronunciation feedback, it's perfect for making early phonics engaging.",
  };

  const product2Details = {
    pros: [
      { text: "Huge variety: 400+ educational games across multiple subjects" },
      { text: "Works for wider age range (K-6)" },
      { text: "Trusted by teachers and used in schools since 2004" },
      { text: "Colorful, kid-friendly interface" },
      { text: "Free tier available (with ads)" },
      { text: "Regular updates with new games" },
    ],
    cons: [
      { text: "No speech recognition or pronunciation feedback" },
      { text: "Not a systematic curriculum (just scattered games)" },
      { text: "Ads on free tier can be distracting" },
      { text: "Games prioritize entertainment over deep learning" },
      { text: "$99/year for ad-free experience" },
      { text: "No real assessment or progress tracking" },
    ],
    bestFor: [
      "General educational gaming across subjects",
      "Kids who need variety to stay engaged",
      "Classrooms wanting game-based supplemental activities",
      "Rainy day activities or reward time",
      "Families wanting one platform for multiple subjects",
    ],
    description:
      "ABCya offers 400+ educational games covering reading, math, science, and more. It's great for variety and engagement but lacks systematic phonics instruction and pronunciation feedback. Best used as supplemental entertainment rather than primary reading instruction.",
  };

  const wordWizDetails = {
    pros: [
      { text: "100% free with all features (speech recognition included)" },
      { text: "ONLY option among these three with speech recognition" },
      { text: "Provides actual pronunciation feedback (not just game scores)" },
      { text: "Phoneme-level analysis identifies specific errors" },
      { text: "AI-powered personalization with GPT-4" },
      { text: "Works on any device with browser (no app download needed)" },
      { text: "Science of Reading aligned with systematic phonics" },
    ],
    cons: [
      { text: "Less entertaining than Teach Monster or ABCya games" },
      { text: "Narrower focus (pronunciation practice, not full curriculum)" },
      { text: "More serious/educational, less adventure-style" },
      { text: "Requires microphone access" },
    ],
    bestFor: [
      "Pronunciation practice and assessment",
      "Kids who can decode but mispronounce words",
      "Complementing game-based learning with actual feedback",
      "English Language Learners needing pronunciation help",
      "Parents who want to know if child is reading correctly",
      "Adding assessment component to entertaining games",
    ],
    description:
      "Word Wiz AI fills the gap left by games: it actually listens to children read and provides specific pronunciation feedback. While less game-like than competitors, it's the only free tool that assesses pronunciation accuracy and helps correct errors.",
  };

  const verdict = {
    product1:
      "Best for making early phonics (ages 3-6) fun and engaging. Kids love the adventure game format, and it's completely free. However, it can't tell you if your child is actually pronouncing words correctly.",
    product2:
      "Best for variety and multi-subject entertainment. With 400+ games, kids won't get bored. But it's not systematic phonics instruction, and the free version has ads. At $99/year for ad-free, it's not the most budget-friendly option.",
    wordWiz:
      "Best for pronunciation feedback and assessment. It's the only free tool that actually listens to kids read and provides specific corrections. Less entertaining than games, but more educational and informative for parents.",
    overall:
      "The ideal combination is Teach Your Monster + Word Wiz AI (both free!). Use Teach Monster to make phonics fun and engaging, then use Word Wiz AI to practice pronunciation and ensure accuracy. Together, they provide entertainment plus feedback without spending anything.",
  };

  const faqs = [
    {
      question: "Is Teach Your Monster to Read really free?",
      answer:
        "Yes! The browser version at teachyourmonstertoread.com is 100% free with no ads, in-app purchases, or subscriptions. The mobile app (iOS/Android) costs $4.99 but is optional—the free browser version has all the same content.",
    },
    {
      question: "Does ABCya have a free version?",
      answer:
        "Yes, ABCya has a free tier, but it includes ads and has limited access to games. ABCya Plus ($99/year) removes ads and unlocks all 400+ games with offline mode.",
    },
    {
      question: "Which app teaches phonics best?",
      answer:
        "Teach Your Monster has the most systematic phonics instruction, following the UK's Letters and Sounds program. Word Wiz AI also teaches phonics systematically but adds pronunciation feedback through speech recognition. ABCya has phonics games but they're not organized into a systematic curriculum.",
    },
    {
      question: "Can these apps tell if my child is reading correctly?",
      answer:
        "Only Word Wiz AI has speech recognition to check pronunciation. Teach Your Monster and ABCya don't listen to your child read, so you won't know if they're mispronouncing words. If pronunciation assessment is important, Word Wiz AI is your only free option.",
    },
    {
      question: "Which is best for a 4-year-old just starting to read?",
      answer:
        "Start with Teach Your Monster to Read—it's perfect for beginners (ages 3-6), completely free, and makes phonics fun. Once your child is reading simple words, add Word Wiz AI to practice pronunciation and get feedback.",
    },
    {
      question: "Can I use these together?",
      answer:
        "Absolutely! The best combo is Teach Your Monster for fun phonics learning + Word Wiz AI for pronunciation practice. Both are free, so you get comprehensive support (entertainment + feedback) without spending anything.",
    },
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ComparisonPage",
    name: "Teach Your Monster vs ABCya vs Word Wiz AI",
    description:
      "Compare free phonics games: Teach Your Monster, ABCya, and Word Wiz AI. See which is best for your child's reading practice.",
    mainEntity: [
      {
        "@type": "Product",
        name: "Teach Your Monster to Read",
        description: "Free phonics game for ages 3-6",
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.7",
          reviewCount: "8500",
        },
      },
      {
        "@type": "Product",
        name: "ABCya",
        description: "Educational game portal with 400+ games",
        offers: {
          "@type": "Offer",
          price: "99",
          priceCurrency: "USD",
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.3",
          reviewCount: "12000",
        },
      },
      {
        "@type": "Product",
        name: "Word Wiz AI",
        description: "Free speech recognition for pronunciation practice",
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
      metaTitle="Teach Monster vs ABCya vs Word Wiz AI: Best Free Reading Games"
      metaDescription="Compare Teach Your Monster, ABCya, and Word Wiz AI. All offer free phonics practice, but only Word Wiz AI provides speech recognition. See which is right for your child."
      canonicalUrl="https://wordwizai.com/comparisons/teach-your-monster-vs-abcya-vs-word-wiz-ai"
      h1Title="Teach Your Monster vs ABCya vs Word Wiz AI: Which Free Reading Game is Best?"
      introText="Looking for free reading games for your child? Compare Teach Your Monster's adventure phonics, ABCya's game variety, and Word Wiz AI's unique speech recognition. See which fits your child's needs and learning style."
      verdict={verdict}
      faqs={faqs}
      structuredData={structuredData}
    />
  );
};

export default TeachMonsterABCyaComparison;
