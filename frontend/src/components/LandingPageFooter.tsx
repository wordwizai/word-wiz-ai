import { Link } from "react-router-dom";
import { trackSignupClick } from "@/utils/analytics";

const LandingPageFooter = () => {
  return (
    <footer className="bg-primary text-primary-foreground py-12 px-6 mt-12">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-8 mb-8">
          {/* Brand */}
          <div className="text-center md:text-left">
            <h3 className="text-xl font-bold mb-2">Word Wiz AI</h3>
            <p className="text-sm">Read smarter. Grow faster.</p>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">Product</h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link to="/about" className="hover:underline">
                About
              </Link>
              <Link
                to="/signup"
                className="hover:underline"
                onClick={() => trackSignupClick("footer", "link")}
              >
                Sign Up
              </Link>
              <Link to="/login" className="hover:underline">
                Login
              </Link>
              <Link to="/contact" className="hover:underline">
                Contact
              </Link>
            </div>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">Resources</h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link
                to="#"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Coming soon");
                }}
                className="hover:underline"
              >
                For Educators
              </Link>
              <Link to="/privacy" className="hover:underline">
                Privacy Policy
              </Link>
              <Link
                to="#"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Coming soon");
                }}
                className="hover:underline"
              >
                Terms of Service
              </Link>
            </div>
          </div>

          {/* Comparisons */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">
              App Comparisons
            </h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link
                to="/comparisons/reading-tutor-vs-reading-app"
                className="hover:underline"
              >
                Tutor vs Reading App
              </Link>
              <Link
                to="/comparisons/ai-reading-app-vs-traditional-phonics-program"
                className="hover:underline"
              >
                AI vs Traditional Phonics
              </Link>
              <Link
                to="/comparisons/free-phonics-apps-vs-paid-reading-programs"
                className="hover:underline"
              >
                Free vs Paid Programs
              </Link>
              <Link
                to="/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai"
                className="hover:underline"
              >
                ABCmouse vs HOP
              </Link>
              <Link
                to="/comparisons/reading-eggs-vs-starfall-vs-word-wiz-ai"
                className="hover:underline"
              >
                Reading Eggs vs Starfall
              </Link>
              <Link
                to="/comparisons/homer-vs-khan-academy-kids-vs-word-wiz-ai"
                className="hover:underline"
              >
                HOMER vs Khan Kids
              </Link>
              <Link
                to="/comparisons/lexia-vs-raz-kids-vs-word-wiz-ai"
                className="hover:underline"
              >
                Lexia vs Raz-Kids
              </Link>
              <Link
                to="/comparisons/best-free-reading-apps"
                className="hover:underline"
              >
                Best Free Apps
              </Link>
              <Link
                to="/comparisons/best-phonics-app-kindergarten-struggling-readers"
                className="hover:underline"
              >
                Best Kindergarten Phonics Apps
              </Link>
              <Link
                to="/comparisons/phonics-worksheets-vs-interactive-reading"
                className="hover:underline"
              >
                Worksheets vs Interactive
              </Link>
            </div>
          </div>

          {/* Guides */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">
              Phonics Guides
            </h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link
                to="/guides/how-to-teach-phonics-at-home"
                className="hover:underline"
              >
                Teaching Phonics at Home
              </Link>
              <Link
                to="/guides/how-to-teach-cvc-words-to-struggling-readers"
                className="hover:underline"
              >
                How to Teach CVC Words
              </Link>
              <Link
                to="/guides/teaching-consonant-blends-kindergarten-at-home"
                className="hover:underline"
              >
                Teaching Consonant Blends
              </Link>
              <Link
                to="/guides/short-vowel-sounds-exercises-beginning-readers"
                className="hover:underline"
              >
                Short Vowel Sounds
              </Link>
              <Link
                to="/guides/r-controlled-vowels-teaching-strategies-parents"
                className="hover:underline"
              >
                R-Controlled Vowels
              </Link>
              <Link
                to="/guides/daily-phonics-practice-routine-kindergarten-at-home"
                className="hover:underline"
              >
                Daily Phonics Routine
              </Link>
              <Link
                to="/guides/decodable-sentences-for-beginning-readers"
                className="hover:underline"
              >
                Decodable Sentences
              </Link>
              <Link
                to="/guides/phonics-practice-without-worksheets-kindergarten"
                className="hover:underline"
              >
                Phonics Without Worksheets
              </Link>
              <Link
                to="/guides/silent-e-words-practice-for-kids"
                className="hover:underline"
              >
                Silent E Words Practice
              </Link>
              <Link
                to="/guides/long-vowel-sounds-practice-first-grade"
                className="hover:underline"
              >
                Long Vowel Sounds
              </Link>
              <Link
                to="/guides/vowel-digraphs-activities-first-graders"
                className="hover:underline"
              >
                Vowel Digraphs
              </Link>
              <Link
                to="/guides/phonics-activities-5-year-old-struggling-reader"
                className="hover:underline"
              >
                Phonics for 5-Year-Olds
              </Link>
              <Link
                to="/guides/first-grade-reading-practice-activities-home"
                className="hover:underline"
              >
                First Grade Activities
              </Link>
              <Link
                to="/guides/reading-practice-kids-hate-reading"
                className="hover:underline"
              >
                Kids Who Hate Reading
              </Link>
            </div>
          </div>

          {/* Practice Activities */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">
              Practice Activities
            </h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link
                to="/guides/five-minute-reading-practice-activities-kids"
                className="hover:underline"
              >
                5 Minute Reading Activities
              </Link>
              <Link
                to="/guides/is-teacher-teaching-enough-phonics"
                className="hover:underline"
              >
                Is Teacher Teaching Phonics?
              </Link>
              <Link
                to="/guides/phoneme-awareness-complete-guide"
                className="hover:underline"
              >
                Phoneme Awareness Guide
              </Link>
              <Link
                to="/guides/how-to-choose-reading-app"
                className="hover:underline"
              >
                Choosing Reading Apps
              </Link>
            </div>
          </div>

          {/* Reading Problems */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">
              Reading Problems
            </h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link
                to="/articles/child-cant-blend-sounds-into-words"
                className="hover:underline"
              >
                Can't Blend Sounds
              </Link>
              <Link
                to="/articles/kindergartener-guesses-words-instead-sounding-out"
                className="hover:underline"
              >
                Guesses Words
              </Link>
              <Link
                to="/articles/child-reads-slowly-struggles-with-fluency"
                className="hover:underline"
              >
                Reads Slowly
              </Link>
              <Link
                to="/articles/first-grader-skips-words-when-reading-aloud"
                className="hover:underline"
              >
                Skips Words
              </Link>
              <Link
                to="/articles/why-child-hates-reading"
                className="hover:underline"
              >
                Why Child Hates Reading
              </Link>
              <Link
                to="/articles/child-pronounces-words-wrong"
                className="hover:underline"
              >
                Pronunciation Errors
              </Link>
              <Link
                to="/articles/decodable-books-vs-leveled-readers"
                className="hover:underline"
              >
                Decodable vs Leveled Books
              </Link>
              <Link
                to="/articles/child-memorizes-books-instead-reading"
                className="hover:underline"
              >
                Memorizes vs Reads
              </Link>
              <Link
                to="/articles/child-confuses-b-d-letters"
                className="hover:underline"
              >
                Confuses B and D
              </Link>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-primary-foreground/20 pt-6 text-center text-sm">
          <p>{new Date().getFullYear()} Word Wiz AI</p>
        </div>
      </div>
    </footer>
  );
};

export default LandingPageFooter;
