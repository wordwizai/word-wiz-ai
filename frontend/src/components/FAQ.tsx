import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { SUPPORT_EMAIL } from "@/config/contact";
import { cn } from "@/lib/utils";
import { PenArrow, PenGroup, PenWords } from "./landing/TeacherPen";
import { penNote, sectionTitle } from "./landing/styles";

interface FAQItem {
  question: string;
  answer: string;
}

// Plain answers a parent can act on. The data answer has to stay in step
// with the privacy policy and the home page's "What happens to the recording".
const faqs: FAQItem[] = [
  {
    question: "Is it really free?",
    answer:
      "Yes. There are no ads, no subscription, and no card on file. It stays free because charging $10 to $15 a month would shut out the kids who need reading help most.",
  },
  {
    question: "What ages is it for?",
    answer:
      "Ages 5 to 8, roughly kindergarten through 3rd grade. It's built for kids who are learning to sound words out, or who keep getting stuck on certain sounds.",
  },
  {
    question: "How does the feedback work?",
    answer:
      "Your child reads a sentence out loud. Word Wiz breaks the recording into individual sounds, compares them with how each word should sound, and points to the exact sound that slipped. The next sentence is written to practice it.",
  },
  {
    question: "Is my child's data safe?",
    answer:
      "Recordings are used to check the reading and then thrown away. We keep scores and which sounds were hard, so practice can adapt. There are no ads, and nothing is sold or shared.",
  },
  {
    question: "What devices does it work on?",
    answer:
      "Any modern browser with a microphone. That includes iPads, Chromebooks, Windows laptops, Macs, and phones.",
  },
  {
    question: "How is it different from other reading apps?",
    answer:
      "Most apps check whether the whole word was right. Word Wiz checks each sound inside the word, and writes new practice around the sounds your child misses.",
  },
];

const FAQ: React.FC = () => {
  // The first answer starts open; it's the question most parents arrive with.
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  // Add structured data for SEO
  React.useEffect(() => {
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity: faqs.map((faq) => ({
        "@type": "Question",
        name: faq.question,
        acceptedAnswer: {
          "@type": "Answer",
          text: faq.answer,
        },
      })),
    };

    const script = document.createElement("script");
    script.type = "application/ld+json";
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
    <section className="bg-muted/50 px-4 py-20 sm:px-6 md:py-24">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 lg:flex-row lg:items-start lg:gap-16">
        <PenGroup className="space-y-4 lg:w-[380px] lg:flex-none">
          <h2 className={sectionTitle}>Questions parents ask</h2>
          <p className="text-[17px] text-muted-foreground">
            Straight answers. If yours isn&rsquo;t here, write to{" "}
            <a
              href={`mailto:${SUPPORT_EMAIL}`}
              className="break-words font-semibold text-primary underline-offset-4 hover:underline"
            >
              {SUPPORT_EMAIL}
            </a>
            .
          </p>
          <div className="hidden items-end gap-1.5 pt-2 lg:flex">
            <PenWords
              delay={0.3}
              text="start with this one, it’s the big one"
              className={cn(penNote, "max-w-[200px] -rotate-3")}
            />
            <PenArrow
              variant="up-right"
              delay={1.5}
              className="mb-4 h-10 w-20 flex-none"
            />
          </div>
        </PenGroup>

        <div className="min-w-0 flex-1 rounded-3xl border border-border bg-card px-5 py-2 shadow-sm sm:px-7">
          {faqs.map((faq, index) => {
            const open = openIndex === index;
            return (
              <div
                key={faq.question}
                className={cn(
                  "py-2",
                  index < faqs.length - 1 && "border-b border-border"
                )}
              >
                <button
                  type="button"
                  onClick={() => toggleFAQ(index)}
                  aria-expanded={open}
                  aria-controls={`faq-answer-${index}`}
                  className="flex min-h-14 w-full items-center justify-between gap-4 rounded-lg text-left outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
                >
                  <h3 className="text-lg font-semibold">{faq.question}</h3>
                  <motion.span
                    animate={{ rotate: open ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex-none"
                  >
                    <ChevronDown
                      className="size-5 text-muted-foreground"
                      aria-hidden="true"
                    />
                  </motion.span>
                </button>

                <AnimatePresence initial={false}>
                  {open && (
                    <motion.div
                      id={`faq-answer-${index}`}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <p className="max-w-[620px] pb-4 text-muted-foreground">
                        {faq.answer}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default FAQ;
