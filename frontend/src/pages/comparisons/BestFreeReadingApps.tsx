import ComparisonPage from "@/components/ComparisonPageTemplate";

const BestFreeReadingAppsComparison = () => {
  const product1 = {
    name: "Starfall",
    tagline: "Nonprofit educational platform, online since 2002",
    pricing: {
      free: "Limited free",
      paid: "$35/yr for full access",
      trial: "Free tier available",
    },
    website: "https://www.starfall.com",
  };

  const product2 = {
    name: "Khan Academy Kids",
    tagline: "100% free from Khan Academy nonprofit",
    pricing: {
      free: "Free forever",
      paid: "N/A",
      trial: "All features free",
    },
    website: "https://www.khanacademykids.org",
  };

  const wordWiz = {
    name: "Word Wiz AI",
    tagline: "Free AI-powered speech recognition",
    pricing: {
      free: "Free forever",
    },
    website: "https://wordwizai.com",
  };

  const comparisonFeatures = [
    {
      category: "Free Features",
      features: [
        {
          name: "Completely Free",
          product1: "Limited",
          product2: true,
          wordWiz: true,
        },
        {
          name: "No Trial Period Limits",
          product1: "Free tier",
          product2: true,
          wordWiz: true,
        },
        {
          name: "Speech Recognition Included",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Full Curriculum Access",
          product1: "Paid",
          product2: true,
          wordWiz: "Yes",
        },
        {
          name: "No Credit Card Required",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        { name: "No Ads", product1: true, product2: true, wordWiz: true },
      ],
    },
    {
      category: "Reading & Phonics",
      features: [
        {
          name: "Phonics Instruction",
          product1: true,
          product2: true,
          wordWiz: "Specialized",
        },
        {
          name: "Pronunciation Feedback",
          product1: false,
          product2: false,
          wordWiz: "AI-powered",
        },
        {
          name: "Phoneme-Level Analysis",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Reading Comprehension",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Decodable Stories",
          product1: true,
          product2: "Limited",
          wordWiz: true,
        },
      ],
    },
    {
      category: "Technology & Platform",
      features: [
        {
          name: "Web Browser Access",
          product1: true,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Mobile Apps",
          product1: "Available",
          product2: true,
          wordWiz: "Web-based",
        },
        {
          name: "AI-Powered Personalization",
          product1: false,
          product2: "Adaptive",
          wordWiz: "Yes",
        },
        {
          name: "Real-Time Speech Analysis",
          product1: false,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Offline Mode",
          product1: false,
          product2: "Downloaded",
          wordWiz: false,
        },
      ],
    },
    {
      category: "Content & Subjects",
      features: [
        {
          name: "Reading Focus",
          product1: "Strong",
          product2: "Moderate",
          wordWiz: "Primary",
        },
        { name: "Math", product1: true, product2: true, wordWiz: false },
        {
          name: "Science & Social Studies",
          product1: true,
          product2: true,
          wordWiz: false,
        },
        {
          name: "Art & Creativity",
          product1: true,
          product2: true,
          wordWiz: false,
        },
        {
          name: "Phonics Depth",
          product1: "High",
          product2: "Moderate",
          wordWiz: "Very High",
        },
      ],
    },
    {
      category: "Accessibility",
      features: [
        {
          name: "Designed for Dyslexia",
          product1: true,
          product2: false,
          wordWiz: true,
        },
        {
          name: "Multisensory Learning",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "No Time Pressure",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Privacy Focused (COPPA)",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Multiple Child Profiles",
          product1: false,
          product2: true,
          wordWiz: true,
        },
      ],
    },
    {
      category: "Progress Tracking",
      features: [
        {
          name: "Parent Dashboard",
          product1: false,
          product2: true,
          wordWiz: true,
        },
        {
          name: "Teacher Tools",
          product1: "School edition",
          product2: "Limited",
          wordWiz: true,
        },
        {
          name: "Detailed Progress Reports",
          product1: false,
          product2: "Basic",
          wordWiz: "Detailed",
        },
        {
          name: "Phoneme Error Analysis",
          product1: false,
          product2: false,
          wordWiz: true,
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Free tier available (no cost to start)" },
      { text: "Nonprofit mission focused on education" },
      { text: "Founded by someone who had dyslexia" },
      { text: "Multisensory, untimed activities" },
      { text: "Trusted by teachers nationwide" },
      { text: "No advertising, and no personal data collected from children" },
    ],
    cons: [
      { text: "Best features require $35/year" },
      { text: "No speech recognition technology" },
      { text: "Interface feels dated" },
      { text: "No progress tracking for children" },
      { text: "Limited personalization" },
    ],
    bestFor: [
      "Families wanting free dyslexia-friendly resources",
      "Parents seeking nonprofit platforms",
      "Multi-subject learning on a budget",
    ],
    description:
      "Starfall is a nonprofit platform whose founder had dyslexia and built it to help children learn to read. It offers multisensory activities with a free tier, though best features require annual membership.",
  };

  const product2Details = {
    pros: [
      { text: "100% free forever (all features)" },
      { text: "No ads ever (nonprofit)" },
      { text: "Khan Academy brand trust" },
      { text: "Adaptive learning technology" },
      { text: "Multiple child profiles" },
      { text: "Comprehensive multi-subject curriculum" },
    ],
    cons: [
      { text: "No speech recognition" },
      { text: "App-only (no web browser version)" },
      { text: "Limited phonics depth" },
      { text: "No pronunciation feedback" },
      { text: "Broader focus, not phonics-specialized" },
    ],
    bestFor: [
      "Families seeking 100% free learning",
      "Budget-conscious parents",
      "General education across subjects",
    ],
    description:
      "Khan Academy Kids is a completely free learning app from the trusted Khan Academy nonprofit. It offers adaptive multi-subject learning but lacks specialized phonics focus and speech recognition.",
  };

  const wordWizDetails = {
    pros: [
      { text: "Listens as your child reads aloud" },
      { text: "Phoneme-level pronunciation analysis" },
      { text: "Next sentence written around the sounds your child missed" },
      { text: "Web-based (no download needed)" },
      { text: "Specialized for phonics mastery" },
      { text: "Teacher dashboard included" },
      { text: "Real-time automated coaching" },
    ],
    cons: [
      { text: "Requires microphone and internet" },
      { text: "Reading-focused only (not multi-subject)" },
      { text: "Newer platform (smaller community)" },
      { text: "No offline mode" },
    ],
    bestFor: [
      "Children with pronunciation challenges",
      "Parents needing speech technology",
      "Teachers tracking phoneme mastery",
      "Families wanting AI without paying",
    ],
    description:
      "Word Wiz AI is a free reading tutor that listens as your child reads and checks each sound inside each word. The next sentence is written around the sounds your child missed.",
  };

  const verdict = {
    product1:
      "Choose Starfall if you want a free dyslexia-friendly platform with multisensory activities. It's trusted by educators but requires $35/year for full features and lacks speech recognition.",
    product2:
      "Choose Khan Academy Kids if you want 100% free multi-subject learning from a trusted nonprofit. It's comprehensive and completely free but doesn't focus on phonics or pronunciation.",
    wordWiz:
      "Choose Word Wiz AI if you want an app that listens to your child read. Of these three, it's the one that checks each sound your child says, at no cost.",
    overall:
      "Khan Academy Kids offers breadth across subjects and Starfall offers multisensory phonics, but neither listens to your child read aloud. Word Wiz AI does, for free. If you want to compare it with other free apps that listen, such as Google Read Along and Microsoft Reading Coach, see our comparison of reading apps that listen to your child read.",
  };

  const faqs = [
    {
      question: "Which app is truly 100% free with no limitations?",
      answer:
        "Khan Academy Kids is 100% free forever with all features included. Starfall has a free tier but best features require $60/year. Word Wiz AI is free, including speech recognition, with no paid tier.",
    },
    {
      question: "Do any free reading apps have speech recognition?",
      answer:
        "Yes. Of these three, Word Wiz AI is the one that listens as your child reads. Starfall and Khan Academy Kids focus on tapping, listening and multiple choice activities. Google Read Along and Microsoft Reading Coach are also free and listen to children read, and we compare them in a separate guide.",
    },
    {
      question: "Which free app is best for pronunciation problems?",
      answer:
        "Word Wiz AI is specifically designed for pronunciation challenges. Its phoneme-level speech analysis identifies exactly which sounds children struggle with. Starfall and Khan Academy Kids cannot analyze pronunciation because they lack speech recognition.",
    },
    {
      question: "Are these apps safe for kids?",
      answer:
        "Yes, all three are COPPA compliant with no advertising. Starfall and Khan Academy Kids are nonprofit organizations. Word Wiz AI is ad-free and privacy-focused. All are trusted by parents and educators.",
    },
    {
      question: "Which is best for homeschooling on a budget?",
      answer:
        "Khan Academy Kids is best for comprehensive free multi-subject homeschool curriculum. Starfall works well for phonics focus. Word Wiz AI adds pronunciation coaching that parents may struggle to provide themselves.",
    },
    {
      question: "Can I use multiple apps together?",
      answer:
        "Absolutely! You could use Khan Academy Kids for broad learning, Starfall for dyslexia-friendly activities, and Word Wiz AI for pronunciation practice. Since all have free options, you can combine them based on your child's needs.",
    },
    {
      question: "Which requires an app download vs works in browser?",
      answer:
        "Starfall and Word Wiz AI work in web browsers (no download needed). Khan Academy Kids is app-only (iOS/Android). For families who prefer not downloading apps, Starfall and Word Wiz AI are more accessible.",
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
      metaTitle="Best Free Reading Apps: Starfall vs Khan Academy Kids vs Word Wiz AI"
      metaDescription="Compare the best free reading apps for kids. See Starfall, Khan Academy Kids, and Word Wiz AI features, speech recognition, and which is best for your child."
      canonicalUrl="https://wordwizai.com/comparisons/best-free-reading-apps"
      h1Title="Best Free Reading Apps: Starfall vs Khan Academy Kids vs Word Wiz AI"
      introText="Khan Academy Kids is entirely free with the broadest curriculum, Starfall is free with limits or $35/year for full access, and Word Wiz AI is free and the only one that gives spoken pronunciation feedback. For a genuinely free setup, Khan Academy Kids covers breadth while Word Wiz AI covers pronunciation accuracy."
      verdict={verdict}
      faqs={faqs}
    />
  );
};

export default BestFreeReadingAppsComparison;
