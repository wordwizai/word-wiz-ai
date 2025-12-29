import ComparisonPage from "@/components/ComparisonPageTemplate";

const LexiaRazKidsComparison = () => {
  const product1 = {
    name: "Lexia Core5",
    tagline: "Adaptive reading intervention for K-5",
    pricing: {
      free: "School trial only",
      paid: "$50-80/student/year",
      trial: "School/district trials available",
    },
    rating: 4.2,
    reviewCount: 1200,
    website: "https://www.lexialearning.com",
  };

  const product2 = {
    name: "Raz-Kids",
    tagline: "Leveled reading library with 400+ eBooks",
    pricing: {
      free: "14-day trial",
      paid: "$120/classroom/year (36 students)",
      trial: "14 days free",
    },
    rating: 4.6,
    reviewCount: 3400,
    website: "https://www.raz-kids.com",
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
      category: "Assessment & Diagnostics",
      features: [
        {
          name: "Placement Testing",
          product1: "Comprehensive",
          product2: false,
          wordWiz: false,
        },
        {
          name: "Progress Reports",
          product1: "Detailed analytics",
          product2: "Basic reports",
          wordWiz: "Pronunciation tracking",
        },
        {
          name: "Risk Identification",
          product1: true,
          product2: false,
          wordWiz: "Pronunciation errors",
        },
        {
          name: "LEXILE Tracking",
          product1: true,
          product2: false,
          wordWiz: false,
        },
      ],
    },
    {
      category: "Instructional Content",
      features: [
        {
          name: "Systematic Phonics",
          product1: true,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Reading Library",
          product1: false,
          product2: "400+ books",
          wordWiz: "Decodable sentences",
        },
        {
          name: "Comprehension Instruction",
          product1: true,
          product2: "Basic quizzes",
          wordWiz: false,
        },
        {
          name: "Vocabulary Development",
          product1: true,
          product2: "Some",
          wordWiz: false,
        },
        {
          name: "Six Reading Areas",
          product1: true,
          product2: false,
          wordWiz: "Phonics & pronunciation",
        },
      ],
    },
    {
      category: "Technology & Innovation",
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
          wordWiz: "GPT-4",
        },
        {
          name: "Adaptive Learning",
          product1: "Algorithm-based",
          product2: false,
          wordWiz: "AI-personalized",
        },
        {
          name: "Recording Feature",
          product1: false,
          product2: "Yes (no analysis)",
          wordWiz: "With feedback",
        },
      ],
    },
    {
      category: "Teacher & Parent Support",
      features: [
        {
          name: "Teacher Dashboard",
          product1: "Advanced",
          product2: "Good",
          wordWiz: "Basic (free)",
        },
        {
          name: "Class Management",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Individual Access",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Home Use Friendly",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Training Resources",
          product1: "Extensive",
          product2: "Good",
          wordWiz: "Basic",
        },
      ],
    },
    {
      category: "Pricing & Access",
      features: [
        {
          name: "Per-Student Cost",
          product1: "$50-80/year",
          product2: "$3.33/year",
          wordWiz: "$0",
        },
        {
          name: "Free Tier",
          product1: false,
          product2: false,
          wordWiz: "Full features",
        },
        {
          name: "School Purchase Required",
          product1: true,
          product2: true,
          wordWiz: false,
        },
        {
          name: "Unlimited Students",
          product1: false,
          product2: "Up to 36",
          wordWiz: "Unlimited",
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Comprehensive assessment system identifies struggling readers" },
      { text: "Research-backed with proven efficacy in schools" },
      {
        text: "Covers all six areas of reading (phonological awareness, phonics, structural analysis, fluency, vocabulary, comprehension)",
      },
      {
        text: "Detailed teacher reports show exactly where students need help",
      },
      { text: "Adaptive learning adjusts to student performance" },
      { text: "Used in 20,000+ schools nationwide" },
    ],
    cons: [
      { text: "Expensive: $50-80 per student per year" },
      {
        text: "School/district purchase only (not available for individual parents)",
      },
      { text: "No speech recognition or pronunciation feedback" },
      { text: "Can feel drill-based and repetitive for some students" },
      { text: "Requires ongoing subscription" },
    ],
    bestFor: [
      "Schools needing data-driven intervention programs",
      "RTI (Response to Intervention) frameworks",
      "Title I programs with budget for per-student licensing",
      "Teachers who need comprehensive diagnostic information",
      "Districts wanting proven, research-backed solutions",
    ],
    description:
      "Lexia Core5 is a comprehensive reading intervention program designed for schools. It excels at identifying struggling readers and providing systematic instruction across all reading areas. However, it's expensive and doesn't offer speech recognition technology.",
  };

  const product2Details = {
    pros: [
      { text: "Affordable for classrooms: $120/year for up to 36 students" },
      { text: "Huge library of 400+ leveled eBooks keeps kids engaged" },
      { text: "Students love the gamification (robots, stars, rewards)" },
      { text: "Recording feature lets students practice reading aloud" },
      { text: "Easy to use for both teachers and students" },
      { text: "Works on most devices (iPad, Chromebook, PC)" },
    ],
    cons: [
      { text: "No phonics instruction (assumes students can already decode)" },
      { text: "No pronunciation feedback on recordings" },
      { text: "Uses leveled readers (not decodable texts)" },
      { text: "Can encourage guessing from pictures/context" },
      { text: "Classroom license only (not for individual home purchase)" },
      { text: "Limited for students with decoding difficulties" },
    ],
    bestFor: [
      "Classroom independent reading practice",
      "Students who can already decode basic words",
      "Building reading fluency and stamina",
      "Budget-conscious schools ($3.33/student is affordable)",
      "Homework/home reading practice",
      "English Language Learners with basic decoding skills",
    ],
    description:
      "Raz-Kids provides a massive library of leveled books perfect for reading practice. It's affordable and engaging but assumes students can already decode. Best used as a supplement for fluency building, not primary phonics instruction.",
  };

  const wordWizDetails = {
    pros: [
      { text: "100% free (no per-student costs, no subscription)" },
      { text: "Only option with real-time speech recognition" },
      {
        text: "Phoneme-level pronunciation analysis identifies specific errors",
      },
      { text: "AI-powered feedback from GPT-4 (personalized and encouraging)" },
      { text: "Teacher dashboard included free for educators" },
      { text: "Individual access (no school purchase required)" },
      { text: "Science of Reading aligned with systematic phonics" },
    ],
    cons: [
      {
        text: "Narrower focus than comprehensive programs (pronunciation only)",
      },
      { text: "No assessment system like Lexia" },
      { text: "No book library like Raz-Kids" },
      { text: "Newer product (less established than 20+ year competitors)" },
      { text: "Requires microphone access" },
    ],
    bestFor: [
      "Pronunciation practice and correction",
      "Budget-limited schools and classrooms",
      "Home use without school purchase requirements",
      "Supplementing existing reading curriculum",
      "English Language Learners needing pronunciation feedback",
      "Students who can decode but mispronounce words",
      "Complementing Lexia or Raz-Kids programs",
    ],
    description:
      "Word Wiz AI is the only free option that listens to students read and provides specific pronunciation feedback. While it doesn't replace comprehensive intervention (Lexia) or reading practice (Raz-Kids), it fills a critical gap by addressing pronunciation—something neither competitor offers.",
  };

  const verdict = {
    product1:
      "Best for comprehensive reading intervention and assessment. Schools with budget for per-student licensing get detailed diagnostics and systematic instruction across all reading skills. Worth the investment if you need data-driven intervention.",
    product2:
      "Best for affordable reading practice with a large book library. At $3.33/student/year, it's perfect for building fluency and engagement. However, it doesn't teach phonics or provide pronunciation feedback.",
    wordWiz:
      "Best for pronunciation feedback and speech technology. It's the only completely free option and the ONLY tool among these three that actually listens to students read. Perfect as a supplement to either Lexia or Raz-Kids, or as a standalone tool for budget-conscious educators.",
    overall:
      "These three programs serve different but complementary purposes. Lexia provides comprehensive assessment and intervention, Raz-Kids offers affordable reading practice, and Word Wiz AI delivers pronunciation feedback. Many schools successfully use combinations: Lexia + Word Wiz AI for intervention with pronunciation support, or Raz-Kids + Word Wiz AI for an affordable, complete solution. If budget allows, all three together create a comprehensive literacy program.",
  };

  const faqs = [
    {
      question: "Is Lexia better than Raz-Kids?",
      answer:
        "They serve different purposes. Lexia excels at intervention and assessment with comprehensive diagnostic data. Raz-Kids excels at providing reading practice with a large book library. Word Wiz AI excels at pronunciation feedback with speech recognition. Most schools use multiple programs together rather than choosing just one.",
    },
    {
      question: "Can I buy Lexia for home use?",
      answer:
        "No, Lexia Core5 is only available for schools and districts. For home use, consider Word Wiz AI (100% free with speech recognition) or other parent-friendly programs like Reading Eggs or Hooked on Phonics.",
    },
    {
      question: "Does Raz-Kids teach phonics?",
      answer:
        "No, Raz-Kids assumes students can already decode and focuses on reading practice with leveled books. For phonics instruction with pronunciation feedback, use Word Wiz AI. For systematic phonics curriculum, consider Lexia or programs like Reading Eggs.",
    },
    {
      question: "Which program is best for struggling readers?",
      answer:
        "Lexia excels at identifying and supporting struggling readers with its comprehensive assessment system. However, if pronunciation is the main issue, Word Wiz AI is the only option with speech recognition to identify and correct specific pronunciation errors. Consider using both together.",
    },
    {
      question: "Is Word Wiz AI really completely free?",
      answer:
        "Yes, all core features including speech recognition, pronunciation feedback, unlimited practice, and teacher dashboard are 100% free with no per-student costs, subscriptions, or hidden fees. This makes it accessible for any school or family regardless of budget.",
    },
    {
      question: "Can I use these programs together?",
      answer:
        "Absolutely! Many schools use combinations: Lexia for assessment and intervention + Word Wiz AI for pronunciation feedback, or Raz-Kids for reading practice + Word Wiz AI for pronunciation correction. These tools complement rather than compete with each other.",
    },
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ComparisonPage",
    name: "Lexia vs Raz-Kids vs Word Wiz AI Comparison",
    description:
      "Compare Lexia Core5, Raz-Kids, and Word Wiz AI reading programs for schools. See pricing, features, and which is best for your classroom.",
    mainEntity: [
      {
        "@type": "Product",
        name: "Lexia Core5 Reading",
        description: "Adaptive reading intervention software for K-5 schools",
        offers: {
          "@type": "Offer",
          price: "50-80",
          priceCurrency: "USD",
          priceSpecification: {
            "@type": "UnitPriceSpecification",
            referenceQuantity: {
              "@type": "QuantitativeValue",
              value: "1",
              unitText: "student per year",
            },
          },
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.2",
          reviewCount: "1200",
        },
      },
      {
        "@type": "Product",
        name: "Raz-Kids",
        description: "Leveled reading library for K-5 classrooms",
        offers: {
          "@type": "Offer",
          price: "120",
          priceCurrency: "USD",
          priceSpecification: {
            "@type": "UnitPriceSpecification",
            referenceQuantity: {
              "@type": "QuantitativeValue",
              value: "1",
              unitText: "classroom per year",
            },
          },
        },
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.6",
          reviewCount: "3400",
        },
      },
      {
        "@type": "Product",
        name: "Word Wiz AI",
        description:
          "Free AI-powered pronunciation feedback with speech recognition",
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
      metaTitle="Lexia vs Raz-Kids vs Word Wiz AI: Which Reading Program is Best?"
      metaDescription="Compare Lexia Core5, Raz-Kids, and Word Wiz AI for schools. See pricing, features, pros/cons, and which is best for your students. Free speech recognition option included."
      canonicalUrl="https://wordwizai.com/comparisons/lexia-vs-raz-kids-vs-word-wiz-ai"
      h1Title="Lexia vs Raz-Kids vs Word Wiz AI: Comprehensive Comparison for Schools"
      introText="Choosing the right reading program for your classroom? Compare Lexia Core5's comprehensive intervention, Raz-Kids' leveled library, and Word Wiz AI's unique speech recognition technology. See pricing, features, and which fits your needs."
      verdict={verdict}
      faqs={faqs}
      structuredData={structuredData}
    />
  );
};

export default LexiaRazKidsComparison;
