import ComparisonPage from "@/components/ComparisonPageTemplate";

// Competitor facts checked on 2026-10-06 against readalong.google, Microsoft's
// Reading Coach FAQ (support.microsoft.com) and ello.com. Re-check them before
// editing this page, since Ello changed its pricing in 2026.
const AppsThatListenComparison = () => {
  const product1 = {
    name: "Google Read Along",
    tagline: "Free reading buddy app from Google",
    pricing: {
      free: "Free",
      trial: "Everything is free",
    },
    website: "https://readalong.google/",
  };

  const product2 = {
    name: "Microsoft Reading Coach",
    tagline: "Free reading fluency practice from Microsoft",
    pricing: {
      free: "Free",
      trial: "Free with a Microsoft account",
    },
    website: "https://coach.microsoft.com/",
  };

  const wordWiz = {
    name: "Word Wiz AI",
    tagline: "Free reading tutor that checks every sound",
    pricing: {
      free: "Free",
    },
    website: "https://wordwizai.com",
  };

  const comparisonFeatures = [
    {
      category: "Listening and Feedback",
      features: [
        {
          name: "Listens as your child reads aloud",
          product1: true,
          product2: true,
          wordWiz: true,
        },
        {
          name: "What the feedback points to",
          product1: "Words your child gets stuck on",
          product2: "Challenging words, accuracy and reading speed",
          wordWiz: "The exact sound inside each word",
        },
        {
          name: "Next practice built from mistakes",
          product1: "Not stated",
          product2: "Missed words go into the next chapter",
          wordWiz: "Next sentence targets the missed sounds",
        },
        {
          name: "What your child reads",
          product1: "1,000+ stories and word games",
          product2: "AI stories, leveled passages, or your own text",
          wordWiz: "Short sentences built around phonics patterns",
        },
      ],
    },
    {
      category: "Access",
      features: [
        {
          name: "Price",
          product1: "Free",
          product2: "Free",
          wordWiz: "Free",
        },
        {
          name: "Where it runs",
          product1: "Android app or web",
          product2: "Web browser or Windows app",
          wordWiz: "Any web browser",
        },
        {
          name: "Sign-in",
          product1: "Child profiles set up by a parent",
          product2: "Microsoft account",
          wordWiz: "Free account (Google or email)",
        },
        {
          name: "Best age range",
          product1: "Early readers",
          product2: "6 to 11",
          wordWiz: "5 to 8",
        },
      ],
    },
    {
      category: "Privacy",
      features: [
        {
          name: "Voice recordings",
          product1: "Processed on the device",
          product2: "Processed on the device",
          wordWiz: "Checked, then discarded",
        },
      ],
    },
  ];

  const product1Details = {
    pros: [
      { text: "Completely free, with no ads or in-app purchases" },
      { text: "The Android app works offline once it's downloaded" },
      { text: "A large library of stories and word games" },
      { text: "Voice data stays on the device" },
      { text: "English, Spanish and several other languages" },
    ],
    cons: [
      { text: "The app is Android only. Other devices use the web version" },
      { text: "Help is given at the word level, not for the sounds inside a word" },
    ],
    bestFor: [
      "Families with an Android phone or tablet",
      "Practice without internet access",
      "Kids who like stories and badges",
    ],
    description:
      "Read Along is Google's free app for young readers. A reading buddy named Diya listens as your child reads stories aloud, helps when they get stuck on a word, and hands out stars and badges. It has no ads or purchases, and the Android app keeps working offline.",
  };

  const product2Details = {
    pros: [
      { text: "Free for any family with a Microsoft account" },
      { text: "Kids can make their own AI stories by picking a character and setting" },
      { text: "Words a child misses come back in the next chapter" },
      { text: "Runs in any browser with a microphone, or as a Windows app" },
      { text: "Tracks accuracy and words per minute" },
    ],
    cons: [
      { text: "Needs a Microsoft account to sign in" },
      { text: "Focused on fluency, so it fits kids who can already read simple text" },
      { text: "Feedback is described in terms of whole words rather than sounds" },
    ],
    bestFor: [
      "Kids ages 6 to 11 building reading fluency",
      "Families already using Microsoft accounts",
      "Readers who are motivated by making their own stories",
    ],
    description:
      "Reading Coach is Microsoft's free fluency tool. Children read AI-generated stories, leveled passages, or text a parent adds, and it collects the words they struggled with into a practice list. Microsoft says it is most useful for ages 6 to 11.",
  };

  const wordWizDetails = {
    pros: [
      { text: "Points to the exact sound your child missed, not just the word" },
      { text: "Writes the next sentence to practice that sound" },
      { text: "Free, with no ads and no subscription" },
      { text: "Runs in any browser, so nothing to install" },
      { text: "Recordings are checked and then thrown away" },
    ],
    cons: [
      { text: "Needs an internet connection" },
      { text: "Short practice sentences, not a library of storybooks" },
      { text: "English only" },
      { text: "Newer and smaller than the Google and Microsoft apps" },
    ],
    bestFor: [
      "Kids ages 5 to 8 learning to sound words out",
      "Children who keep mixing up the same sounds",
      "Parents who want to know which sound is the problem",
    ],
    description:
      "Word Wiz AI is a free reading tutor for ages 5 to 8. Your child reads a sentence out loud, Word Wiz breaks the recording into individual sounds, and it shows which sound slipped. The next sentence is written to practice that sound.",
  };

  const verdict = {
    product1:
      "Choose Read Along if your child uses an Android device, you want something that works offline, or your child is motivated by stories and rewards. It's a strong free option for general read-aloud practice.",
    product2:
      "Choose Reading Coach if your child can already read simple text and needs fluency practice, especially if they'd enjoy making their own stories. It fits families who already have Microsoft accounts.",
    wordWiz:
      "Choose Word Wiz AI if your child is still learning to sound words out and keeps getting stuck on particular sounds. It's built around showing which sound inside the word went wrong.",
    overall:
      "All three are free and all three listen while your child reads, so you can't pick badly. The real difference is what the feedback looks at. Read Along and Reading Coach describe their feedback in terms of whole words and fluency, which suits kids who are building speed and confidence. Word Wiz AI works at the level of individual sounds, which suits kids who are still decoding. Many families use more than one.",
  };

  const faqs = [
    {
      question: "Is there a free app that listens to my child read?",
      answer:
        "Yes, several. Google Read Along, Microsoft Reading Coach and Word Wiz AI are all free and all listen as your child reads aloud. Read Along is an Android app with a web version, Reading Coach runs in a browser or on Windows, and Word Wiz AI runs in any browser.",
    },
    {
      question: "Which reading app tells you exactly what sound my child got wrong?",
      answer:
        "Word Wiz AI. It compares each sound your child said with how the word should sound and points to the one that slipped, for example reading 'ship' as 'sip'. Read Along and Reading Coach describe their feedback in terms of words (words your child got stuck on, words to practice) rather than individual sounds.",
    },
    {
      question: "What about Ello?",
      answer:
        "Ello also listens as children read books aloud and is aimed at ages 4 to 9 on iPhone, iPad and Android. As of 2026 it offers free daily activities, and an optional paid upgrade adds premium features. Check the app for the current price.",
    },
    {
      question: "What about Amira?",
      answer:
        "Amira is an AI reading tutor that listens to students read, but it is sold to schools and districts rather than to families. If your child's school uses it, they can usually log in from home.",
    },
    {
      question: "Do these apps record my child's voice?",
      answer:
        "Each one has to hear your child to give feedback. Google and Microsoft both say voice data for these apps is processed on the device. Word Wiz AI uses the recording to check the reading and then throws it away. It keeps scores and which sounds were hard so practice can adapt.",
    },
    {
      question: "Can my child try Word Wiz AI without an account?",
      answer:
        "Yes. A short sample at wordwizai.com/try works without signing up. A free account (Google or email) is needed to keep practicing and to save progress.",
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
      metaTitle="Free Reading Apps That Listen to Your Child Read (Compared)"
      metaDescription="Google Read Along, Microsoft Reading Coach and Word Wiz AI are free and listen as kids read aloud. Compare feedback, devices, ages and privacy."
      canonicalUrl="https://wordwizai.com/comparisons/reading-apps-that-listen-to-your-child-read"
      h1Title="Free Reading Apps That Listen to Your Child Read: Google Read Along vs Microsoft Reading Coach vs Word Wiz AI"
      introText="Google Read Along, Microsoft Reading Coach and Word Wiz AI are all free, and all three listen while your child reads aloud. Read Along is a story app with a reading buddy that helps with hard words. Reading Coach builds fluency with AI-written stories and a list of words to practice. Word Wiz AI checks each sound inside each word and writes the next sentence around the sounds your child missed, which suits kids who are still learning to sound words out."
      verdict={verdict}
      faqs={faqs}
    />
  );
};

export default AppsThatListenComparison;
