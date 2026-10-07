import ComparisonPage from "@/components/ComparisonPageTemplate";

const LexiaRazKidsComparison = () => {
  const product1 = {
    name: "Lexia Core5",
    tagline: "Adaptive reading intervention for Pre-K-5",
    pricing: {
      free: "No free tier",
      paid: "School quote, or $175/yr for home",
      trial: "No free tier",
    },
    website: "https://www.lexialearning.com",
  };

  const product2 = {
    name: "Raz-Kids",
    tagline: "Leveled reading library with hundreds of eBooks",
    pricing: {
      free: "14-day trial",
      paid: "About $125/classroom/year",
      trial: "14 days free",
    },
    website: "https://www.raz-kids.com",
  };

  const wordWiz = {
    name: "Word Wiz AI",
    tagline: "AI-powered pronunciation feedback with speech recognition",
    pricing: {
      free: "Free forever",
      paid: "All features free",
    },
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
          product2: "Hundreds of books",
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
          wordWiz: "Yes",
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
          product2: "Yes (teacher scores)",
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
          product1: "Via reseller",
          product2: "Parent license",
          wordWiz: true,
        },
        {
          name: "Home Use Friendly",
          product1: "With home license",
          product2: true,
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
          product1: "School quote",
          product2: "Per-classroom license",
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
          product1: "No (home via reseller)",
          product2: false,
          wordWiz: false,
        },
        {
          name: "Unlimited Students",
          product1: false,
          product2: "Per classroom",
          wordWiz: "Unlimited",
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Comprehensive assessment system identifies struggling readers" },
      { text: "Rated \"Strong\" by Evidence for ESSA" },
      {
        text: "Covers all six areas of reading (phonological awareness, phonics, structural analysis, fluency, vocabulary, comprehension)",
      },
      {
        text: "Detailed teacher reports show exactly where students need help",
      },
      { text: "Adaptive learning adjusts to student performance" },
      { text: "Used by millions of U.S. students" },
    ],
    cons: [
      { text: "Paid per-student licenses (school pricing by quote)" },
      {
        text: "Built for schools, and families buy home licenses through a reseller ($175/year)",
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
      { text: "Affordable for classrooms, about $125/year per classroom license" },
      { text: "Huge library of leveled eBooks keeps kids engaged" },
      { text: "Students love the gamification (robots, stars, rewards)" },
      { text: "Recording feature lets students practice reading aloud" },
      { text: "Easy to use for both teachers and students" },
      { text: "Works on most devices (iPad, Chromebook, PC)" },
    ],
    cons: [
      { text: "No phonics instruction (assumes students can already decode)" },
      { text: "No automatic pronunciation feedback (teachers listen to recordings)" },
      { text: "Uses leveled readers (not decodable texts)" },
      { text: "Can encourage guessing from pictures/context" },
      { text: "Sold as a classroom license, even to parents" },
      { text: "Limited for students with decoding difficulties" },
    ],
    bestFor: [
      "Classroom independent reading practice",
      "Students who can already decode basic words",
      "Building reading fluency and stamina",
      "Budget-conscious schools (one license covers a classroom)",
      "Homework/home reading practice",
      "English Language Learners with basic decoding skills",
    ],
    description:
      "Raz-Kids provides a massive library of leveled books perfect for reading practice. It's affordable and engaging but assumes students can already decode. Best used as a supplement for fluency building, not primary phonics instruction.",
  };

  const wordWizDetails = {
    pros: [
      { text: "100% free (no per-student costs, no subscription)" },
      { text: "The one of these three with real-time speech recognition" },
      {
        text: "Phoneme-level pronunciation analysis identifies specific errors",
      },
      { text: "AI-written feedback, with the next sentence built around the sounds a student missed" },
      { text: "Free classes for teachers, with phonics patterns to assign" },
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
      "Of these three, Word Wiz AI is the free option that listens to students read and gives specific pronunciation feedback. While it doesn't replace comprehensive intervention (Lexia) or reading practice (Raz-Kids), it adds something neither competitor offers by addressing pronunciation.",
  };

  const verdict = {
    product1:
      "Best for comprehensive reading intervention and assessment. Schools with budget for per-student licensing get detailed diagnostics and systematic instruction across all reading skills. Worth the investment if you need data-driven intervention.",
    product2:
      "Best for affordable reading practice with a large book library. At about $125 a year for a classroom license, it's perfect for building fluency and engagement. However, it doesn't teach phonics or provide pronunciation feedback.",
    wordWiz:
      "Best for pronunciation feedback and speech technology. It's the only completely free option and the ONLY tool among these three that actually listens to students read. Perfect as a supplement to either Lexia or Raz-Kids, or as a standalone tool for budget-conscious educators.",
    overall:
      "These three programs serve different but complementary purposes. Lexia provides comprehensive assessment and intervention, Raz-Kids offers affordable reading practice, and Word Wiz AI delivers pronunciation feedback. Schools can combine them, using Lexia + Word Wiz AI for intervention with pronunciation support, or Raz-Kids + Word Wiz AI for an affordable, complete solution. If budget allows, all three together create a comprehensive literacy program.",
  };

  const faqs = [
    {
      question: "Is Lexia better than Raz-Kids?",
      answer:
        "They serve different purposes. Lexia excels at intervention and assessment with comprehensive diagnostic data. Raz-Kids excels at providing reading practice with a large book library. Word Wiz AI excels at pronunciation feedback with speech recognition. Schools can use more than one program together rather than choosing just one.",
    },
    {
      question: "Can I buy Lexia for home use?",
      answer:
        "Not from Lexia directly. Lexia sells Core5 to schools and districts, but families can buy a home license through its partner reseller, Family Literacy Centers (lexiaforhome.com), for $175 a year for the first student. For home use, you could also consider Word Wiz AI (100% free with speech recognition) or other parent-friendly programs like Reading Eggs or Hooked on Phonics.",
    },
    {
      question: "Does Raz-Kids teach phonics?",
      answer:
        "No, Raz-Kids assumes students can already decode and focuses on reading practice with leveled books. For phonics instruction with pronunciation feedback, use Word Wiz AI. For systematic phonics curriculum, consider Lexia or programs like Reading Eggs.",
    },
    {
      question: "Which program is best for struggling readers?",
      answer:
        "Lexia excels at identifying and supporting struggling readers with its comprehensive assessment system. However, if pronunciation is the main issue, Word Wiz AI is the option here with speech recognition to identify and correct specific pronunciation errors. Consider using both together.",
    },
    {
      question: "Is Word Wiz AI really completely free?",
      answer:
        "Yes. Speech recognition, pronunciation feedback, unlimited practice, and teacher classes are all 100% free, with no paid tier, per-student costs, subscriptions, or hidden fees. This makes it accessible for any school or family regardless of budget.",
    },
    {
      question: "Can I use these programs together?",
      answer:
        "Absolutely! Schools can combine them, using Lexia for assessment and intervention + Word Wiz AI for pronunciation feedback, or Raz-Kids for reading practice + Word Wiz AI for pronunciation correction. These tools complement rather than compete with each other.",
    },
  ];

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
      introText="For classrooms, Lexia Core5 is a per-student license priced by quote for assessment-driven intervention, Raz-Kids costs about $125 a year per classroom for a leveled reading library, and Word Wiz AI is free and adds the automatic pronunciation feedback neither provides. A school can pair one paid tool with Word Wiz AI rather than choosing between them."
      verdict={verdict}
      faqs={faqs}
    />
  );
};

export default LexiaRazKidsComparison;
