import ComparisonPage from "@/components/ComparisonPageTemplate";

const HookedOnPhonicsComparison = () => {
  const product1 = {
    name: "Hooked on Phonics",
    tagline: "Trusted phonics program for 35+ years",
    pricing: {
      free: "$1 first month",
      paid: "Monthly subscription + physical materials",
      trial: "$1 trial",
    },
    website: "https://www.hookedonphonics.com",
  };

  const product2 = {
    name: "Word Wiz AI",
    tagline: "AI-powered phoneme-level pronunciation feedback",
    pricing: {
      free: "Free forever",
    },
    website: "https://wordwizai.com",
  };

  // For head-to-head, we'll use wordWiz as both product2 and wordWiz for display purposes
  const wordWiz = product2;

  const comparisonFeatures = [
    {
      category: "Core Technology",
      features: [
        {
          name: "Speech Recognition Technology",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Phoneme-Level Analysis",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "AI-Powered Personalized Feedback",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Real-Time Pronunciation Coaching",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Automated Error Detection",
          product1: false,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Phonics Instruction",
      features: [
        {
          name: "Systematic Phonics Curriculum",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Letter Sounds & Recognition",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Blending & Decoding Practice",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Decodable Storybooks",
          product1: "Print + ebooks",
          product2: "Digital",
          wordWiz: "Digital",
        },
        {
          name: "Phonics Phases/Levels",
          product1: "Sequential",
          product2: "Adaptive",
          wordWiz: "Adaptive",
        },
      ],
    },
    {
      category: "Learning Materials",
      features: [
        {
          name: "Digital App/Platform",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Physical Workbooks",
          product1: "Included",
          product2: false,
          wordWiz: false,
        },
        {
          name: "Printed Storybooks",
          product1: "Included",
          product2: false,
          wordWiz: false,
        },
        {
          name: "Flashcards",
          product1: "Pre-K only",
          product2: false,
          wordWiz: false,
        },
        {
          name: "Web-Based (No Download)",
          product1: false,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Feedback & Assessment",
      features: [
        {
          name: "Pronunciation Feedback",
          product1: "Parent manual",
          product2: "AI automated",
          wordWiz: "AI automated",
        },
        {
          name: "Specific Phoneme Error Reports",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Progress Tracking",
          product1: "Basic",
          product2: "Detailed",
          wordWiz: "Detailed",
        },
        {
          name: "Parent/Teacher Dashboard",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Immediate Corrective Feedback",
          product1: false,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Cost & Accessibility",
      features: [
        {
          name: "Free Tier Available",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Monthly Subscription Cost",
          product1: "Paid ($1 first month)",
          product2: "$0",
          wordWiz: "$0",
        },
        {
          name: "Physical Materials Shipping",
          product1: "Included",
          product2: "N/A",
          wordWiz: "N/A",
        },
        {
          name: "Total Annual Cost",
          product1: "Paid subscription",
          product2: "Free",
          wordWiz: "Free",
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Used by families for 35+ years" },
      { text: "Systematic, research-backed phonics approach" },
      { text: "Physical materials (workbooks, books, flashcards)" },
      { text: "Complete program with tangible resources" },
      { text: "Strong brand trust and recognition" },
      { text: "Decodable books matched to learned phonemes" },
    ],
    cons: [
      { text: "Ongoing paid subscription" },
      { text: "No speech recognition technology" },
      { text: "Requires manual parent assessment" },
      { text: "Physical materials create clutter" },
      { text: "Depends on materials arriving by mail" },
      { text: "Not web-based (app download required)" },
    ],
    bestFor: [
      "Parents preferring traditional + digital approach",
      "Families wanting physical learning materials",
      "Those who can commit to a monthly subscription",
    ],
    description:
      "Hooked on Phonics is a time-tested systematic phonics program combining digital games with physical workbooks and books. While trusted for 35+ years, it lacks modern speech recognition technology.",
  };

  const product2Details = {
    pros: [
      { text: "Advanced speech recognition (wav2vec2-TIMIT-IPA)" },
      { text: "Phoneme-level pronunciation analysis" },
      { text: "Next sentence written around the sounds your child missed" },
      { text: "Completely free, with no paid tier" },
      { text: "Web-based (works on any device)" },
      { text: "Real-time automated coaching" },
      { text: "Teacher dashboard included" },
      { text: "No physical materials needed" },
    ],
    cons: [
      { text: "Requires microphone and internet" },
      { text: "No physical workbooks" },
      { text: "Newer platform (less brand recognition)" },
      { text: "Digital-only experience" },
    ],
    bestFor: [
      "Children with pronunciation challenges",
      "Budget-conscious families",
      "Parents wanting data-driven feedback",
      "Teachers needing student progress tracking",
    ],
    description:
      "Word Wiz AI is a modern phonics platform using advanced speech recognition to provide phoneme-level pronunciation feedback. Unlike traditional programs, it offers AI-powered coaching for free.",
  };

  const wordWizDetails = product2Details; // Same for this head-to-head

  const verdict = {
    product1:
      "Hooked on Phonics is excellent if you prefer a traditional program with physical materials and don't mind paying a monthly subscription. It delivers systematic phonics instruction but requires parents to manually assess pronunciation.",
    product2:
      "Word Wiz AI excels if you want modern AI technology that actually listens to your child and provides precise phoneme-level feedback. It delivers what Hooked on Phonics cannot—automated speech analysis—and it's free.",
    wordWiz:
      "Word Wiz AI represents the future of phonics instruction: AI-powered, data-driven, and accessible. While Hooked on Phonics offers time-tested materials, Word Wiz AI offers technology that can identify pronunciation errors parents might miss.",
    overall:
      "For families prioritizing pronunciation accuracy and wanting modern technology, Word Wiz AI is the stronger option. It provides speech recognition capabilities that Hooked on Phonics cannot match, at zero cost. While Hooked on Phonics offers tangible materials, Word Wiz AI offers precise, automated pronunciation coaching. The main reason to choose Hooked on Phonics is if you specifically want physical workbooks and are willing to pay a monthly subscription for them.",
  };

  const faqs = [
    {
      question: "Does Hooked on Phonics have speech recognition?",
      answer:
        "No, Hooked on Phonics does not include speech recognition technology. Parents must manually listen to their child read and assess pronunciation. Word Wiz AI provides automated speech recognition with phoneme-level analysis.",
    },
    {
      question: "Which is better for pronunciation problems?",
      answer:
        'Word Wiz AI is specifically designed for pronunciation challenges. Its phoneme-level analysis can identify exactly which sounds a child struggles with (like confusing "th" with "f"). Hooked on Phonics teaches phonics systematically but cannot diagnose specific pronunciation errors automatically.',
    },
    {
      question: "How much does each program cost?",
      answer:
        "Hooked on Phonics costs $1 for the first month, then a monthly subscription that includes books and workbooks mailed to your home. Word Wiz AI is completely free, including speech recognition, with no paid tier.",
    },
    {
      question: "Do I need to buy workbooks with Word Wiz AI?",
      answer:
        "No, Word Wiz AI is entirely digital. Some parents like Hooked on Phonics' physical workbooks for offline practice. However, Word Wiz AI's speech recognition provides feedback that workbooks cannot—real-time pronunciation analysis.",
    },
    {
      question: "Can teachers use these programs?",
      answer:
        "Hooked on Phonics is mainly built for home use, though it also offers an educator dashboard for classrooms. Word Wiz AI includes a free teacher dashboard with class management and student progress tracking, making it practical for classroom use.",
    },
    {
      question: "Which program is more effective?",
      answer:
        "Both teach phonics systematically. However, Word Wiz AI's speech recognition allows for immediate correction of pronunciation errors, while the word is still fresh. Hooked on Phonics requires parents to provide this feedback manually, which may not be as precise or consistent.",
    },
    {
      question: "Is Hooked on Phonics worth the extra cost?",
      answer:
        "That depends on your priorities. If you strongly prefer physical materials and are willing to pay a monthly subscription, Hooked on Phonics delivers. However, Word Wiz AI provides more advanced technology (speech recognition) at no cost. For most families, Word Wiz AI offers better value.",
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
      metaTitle="Hooked on Phonics vs Word Wiz AI: Which Phonics Program is Better?"
      metaDescription="Detailed comparison of Hooked on Phonics and Word Wiz AI. Compare speech recognition, pricing, effectiveness, and features to find the best phonics program for your child."
      canonicalUrl="https://wordwizai.com/comparisons/hooked-on-phonics-vs-word-wiz-ai"
      h1Title="Hooked on Phonics vs Word Wiz AI: Which Phonics Program is Better?"
      introText="Hooked on Phonics is a paid monthly subscription ($1 for the first month) that delivers systematic phonics with physical workbooks, but a parent has to judge pronunciation by ear. Word Wiz AI is free and analyzes speech at the phoneme level automatically. Choose Hooked on Phonics for tangible materials and structure; choose Word Wiz AI for automated pronunciation feedback."
      verdict={verdict}
      faqs={faqs}
    />
  );
};

export default HookedOnPhonicsComparison;
