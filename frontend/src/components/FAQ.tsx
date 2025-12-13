import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

interface FAQItem {
  question: string;
  answer: string;
}

const faqs: FAQItem[] = [
  {
    question: "Is Word Wiz AI really free?",
    answer: "Yes! Word Wiz AI is 100% free with no ads, no subscriptions, and absolutely no hidden costs. Unlike other reading apps that charge $10-15/month, we believe every child deserves access to quality reading education regardless of their family's financial situation. Word Wiz AI will always remain free because improving children's literacy is our mission, not our business model."
  },
  {
    question: "What age is Word Wiz AI designed for?",
    answer: "Word Wiz AI is specifically designed for children ages 5-8 (typically Kindergarten through 3rd grade) who are learning to read or struggling with early reading skills. The app focuses on phoneme awareness and phonics—the foundational skills needed for reading success. Whether your child is just beginning to recognize letters and sounds, or working on decoding more complex words, Word Wiz AI adapts to their level."
  },
  {
    question: "How does Word Wiz AI help with pronunciation?",
    answer: "Word Wiz AI uses advanced speech recognition technology to listen as your child reads aloud and analyze their pronunciation at the phoneme level. Unlike traditional reading apps that only check if a word is read correctly, Word Wiz AI identifies exactly which sounds your child mispronounces. The AI then generates customized practice sentences focusing on those specific sound patterns, providing targeted, immediate feedback."
  },
  {
    question: "Is my child's data safe?",
    answer: "Absolutely. We take privacy seriously and are committed to protecting your child's information. We comply with COPPA (Children's Online Privacy Protection Act) regulations. Audio recordings are processed for learning purposes only and are not stored permanently. We never sell or share personal data with third parties."
  },
  {
    question: "What devices does Word Wiz AI work on?",
    answer: "Word Wiz AI is a web-based application that works in any modern web browser. It's compatible with desktop computers, laptops, tablets, and smartphones. All you need is an internet connection and a device with a microphone. Works great on iPads, Chromebooks, Windows PCs, and Macs!"
  },
  {
    question: "How is Word Wiz AI different from other reading apps?",
    answer: "Word Wiz AI offers phoneme-level pronunciation analysis (most apps only check whole words), AI-generated custom content that adapts to your child's specific struggle areas, and real-time speech recognition for immediate feedback. Plus, it's 100% free with no ads—unlike competitors that charge monthly subscriptions or show advertisements."
  }
];

const FAQ: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  // Add structured data for SEO
  React.useEffect(() => {
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": faqs.map(faq => ({
        "@type": "Question",
        "name": faq.question,
        "acceptedAnswer": {
          "@type": "Answer",
          "text": faq.answer
        }
      }))
    };

    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.text = JSON.stringify(structuredData);
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="px-6 py-20 bg-gradient-to-br from-background to-purple-50/50">
      <div className="max-w-4xl mx-auto space-y-10">
        <div className="text-center space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold">
            Frequently Asked Questions
          </h2>
          <p className="text-muted-foreground text-lg">
            Everything you need to know about Word Wiz AI
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white border-2 border-purple-100/50 rounded-2xl shadow-sm overflow-hidden"
            >
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-purple-50/30 transition-colors"
              >
                <h3 className="text-lg font-semibold pr-4">{faq.question}</h3>
                <motion.div
                  animate={{ rotate: openIndex === index ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <ChevronDown className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                </motion.div>
              </button>

              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="px-6 pb-5 text-muted-foreground">
                      {faq.answer}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQ;
