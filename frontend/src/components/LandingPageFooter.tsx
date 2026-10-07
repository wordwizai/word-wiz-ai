import { Link } from "react-router-dom";
import { trackSignupClick } from "@/utils/analytics";
import { wordWizIcon } from "@/assets";
import { SUPPORT_EMAIL } from "@/config/contact";

type FooterLink = { to: string; label: string };

// Every guide, article and comparison stays linked from every page; the
// footer is how search engines reach most of them.
const READING_HELP: { title: string; links: FooterLink[] }[] = [
  {
    title: "Phonics Guides",
    links: [
      { to: "/guides/how-to-teach-phonics-at-home", label: "Teaching Phonics at Home" },
      { to: "/guides/how-to-teach-cvc-words-to-struggling-readers", label: "How to Teach CVC Words" },
      { to: "/guides/teaching-consonant-blends-kindergarten-at-home", label: "Teaching Consonant Blends" },
      { to: "/guides/short-vowel-sounds-exercises-beginning-readers", label: "Short Vowel Sounds" },
      { to: "/guides/r-controlled-vowels-teaching-strategies-parents", label: "R-Controlled Vowels" },
      { to: "/guides/daily-phonics-practice-routine-kindergarten-at-home", label: "Daily Phonics Routine" },
      { to: "/guides/decodable-sentences-for-beginning-readers", label: "Decodable Sentences" },
      { to: "/guides/phonics-practice-without-worksheets-kindergarten", label: "Phonics Without Worksheets" },
      { to: "/guides/silent-e-words-practice-for-kids", label: "Silent E Words Practice" },
      { to: "/guides/long-vowel-sounds-practice-first-grade", label: "Long Vowel Sounds" },
      { to: "/guides/vowel-digraphs-activities-first-graders", label: "Vowel Digraphs" },
      { to: "/guides/phonics-activities-5-year-old-struggling-reader", label: "Phonics for 5-Year-Olds" },
      { to: "/guides/first-grade-reading-practice-activities-home", label: "First Grade Activities" },
      { to: "/guides/reading-practice-kids-hate-reading", label: "Kids Who Hate Reading" },
    ],
  },
  {
    title: "When Reading Is Hard",
    links: [
      { to: "/articles/child-cant-blend-sounds-into-words", label: "Can't Blend Sounds" },
      { to: "/articles/kindergartener-guesses-words-instead-sounding-out", label: "Guesses Words" },
      { to: "/articles/child-reads-slowly-struggles-with-fluency", label: "Reads Slowly" },
      { to: "/articles/first-grader-skips-words-when-reading-aloud", label: "Skips Words" },
      { to: "/articles/why-child-hates-reading", label: "Why Child Hates Reading" },
      { to: "/articles/child-pronounces-words-wrong", label: "Pronunciation Errors" },
      { to: "/articles/decodable-books-vs-leveled-readers", label: "Decodable vs Leveled Books" },
      { to: "/articles/child-memorizes-books-instead-reading", label: "Memorizes vs Reads" },
      { to: "/articles/child-confuses-b-d-letters", label: "Confuses B and D" },
    ],
  },
  {
    title: "Practice Activities",
    links: [
      { to: "/practice-words", label: "Phonics Word Lists" },
      { to: "/practice-words/at-family", label: "-at Word Family" },
      { to: "/practice-words/sh-digraph", label: "SH Digraph Words" },
      { to: "/practice-words/bl-blend", label: "BL Blend Words" },
      { to: "/practice-words/ai-vowel-team", label: "AI Vowel Team Words" },
      { to: "/practice-words/ar-r-controlled", label: "AR Words (Bossy R)" },
      { to: "/guides/five-minute-reading-practice-activities-kids", label: "5 Minute Reading Activities" },
      { to: "/guides/is-teacher-teaching-enough-phonics", label: "Is Teacher Teaching Phonics?" },
      { to: "/guides/phoneme-awareness-complete-guide", label: "Phoneme Awareness Guide" },
      { to: "/guides/how-to-choose-reading-app", label: "Choosing Reading Apps" },
    ],
  },
  {
    title: "App Comparisons",
    links: [
      { to: "/comparisons/reading-tutor-vs-reading-app", label: "Tutor vs Reading App" },
      { to: "/comparisons/ai-reading-app-vs-traditional-phonics-program", label: "AI vs Traditional Phonics" },
      { to: "/comparisons/free-phonics-apps-vs-paid-reading-programs", label: "Free vs Paid Programs" },
      { to: "/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai", label: "ABCmouse vs HOP" },
      { to: "/comparisons/reading-eggs-vs-starfall-vs-word-wiz-ai", label: "Reading Eggs vs Starfall" },
      { to: "/comparisons/homer-vs-khan-academy-kids-vs-word-wiz-ai", label: "HOMER vs Khan Kids" },
      { to: "/comparisons/lexia-vs-raz-kids-vs-word-wiz-ai", label: "Lexia vs Raz-Kids" },
      { to: "/comparisons/best-free-reading-apps", label: "Best Free Apps" },
      { to: "/comparisons/reading-apps-that-listen-to-your-child-read", label: "Apps That Listen" },
      { to: "/comparisons/best-phonics-app-kindergarten-struggling-readers", label: "Best Kindergarten Phonics Apps" },
      { to: "/comparisons/phonics-worksheets-vs-interactive-reading", label: "Worksheets vs Interactive" },
      { to: "/comparisons/hooked-on-phonics-vs-word-wiz-ai", label: "Hooked on Phonics vs Word Wiz" },
      { to: "/comparisons/ixl-vs-duolingo-abc-vs-word-wiz-ai", label: "IXL vs Duolingo ABC" },
      { to: "/comparisons/teach-your-monster-vs-abcya-vs-word-wiz-ai", label: "Teach Your Monster vs ABCya" },
    ],
  },
];

const linkClass = "hover:underline underline-offset-4";

const LandingPageFooter = () => {
  // Dark mode's primary is a light lavender, which made the footer a bright
  // slab under a dark page, so it drops to a purple tint there.
  return (
    <footer className="bg-primary text-primary-foreground dark:bg-primary/15 dark:text-foreground pt-16 pb-8 px-4 sm:px-6 mt-12">
      <div className="max-w-6xl mx-auto space-y-11">
        <div className="flex flex-col gap-10 md:flex-row md:justify-between">
          {/* Brand */}
          <div className="max-w-sm space-y-3.5">
            <div className="flex items-center gap-3">
              <span className="flex size-11 items-center justify-center rounded-xl bg-white">
                <img src={wordWizIcon} alt="" className="h-[26px] w-[30px] object-contain" />
              </span>
              <span className="text-xl font-semibold">Word Wiz AI</span>
            </div>
            <p className="text-[15px] leading-relaxed">
              A free reading tutor for kids ages 5 to 8. Reach us at{" "}
              <a
                href={`mailto:${SUPPORT_EMAIL}`}
                className="font-semibold underline underline-offset-4"
              >
                {SUPPORT_EMAIL}
              </a>
              .
            </p>
          </div>

          {/* Site links */}
          <nav aria-label="Word Wiz" className="flex flex-col gap-2.5 text-sm">
            <span className="font-semibold">Word Wiz</span>
            <Link to="/about" className={linkClass}>
              About
            </Link>
            <Link to="/contact" className={linkClass}>
              Contact
            </Link>
            <Link to="/privacy" className={linkClass}>
              Privacy Policy
            </Link>
            <Link to="/login" className={linkClass}>
              Log In
            </Link>
            <Link
              to="/signup"
              className={linkClass}
              onClick={() => trackSignupClick("footer", "link")}
            >
              Sign Up
            </Link>
          </nav>
        </div>

        {/* Reading help library */}
        <nav
          aria-label="Free reading help"
          className="space-y-5 border-t border-primary-foreground/20 pt-8 dark:border-border"
        >
          <span className="block text-sm font-semibold">
            Free reading help for parents and teachers
          </span>
          <div className="grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 lg:grid-cols-4">
            {READING_HELP.map((group) => (
              <div key={group.title} className="flex flex-col gap-2 text-sm">
                <span className="opacity-80">{group.title}</span>
                {group.links.map((link) => (
                  <Link key={link.to} to={link.to} className={linkClass}>
                    {link.label}
                  </Link>
                ))}
              </div>
            ))}
          </div>
        </nav>

        {/* Copyright */}
        <div className="flex flex-wrap justify-between gap-x-6 gap-y-2 border-t border-primary-foreground/20 pt-6 text-sm dark:border-border">
          <p>© {new Date().getFullYear()} Word Wiz AI</p>
          <p>Free forever · No ads</p>
        </div>
      </div>
    </footer>
  );
};

export default LandingPageFooter;
