import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import { lazy, Suspense } from "react";
import { AuthProvider } from "./contexts/AuthContext.tsx";
import { ThemeProvider } from "./contexts/ThemeContext.tsx";
import { SettingsProvider } from "./contexts/SettingsContext.tsx";
import { Analytics } from "@vercel/analytics/react";
import { Toaster } from "./components/ui/sonner.tsx";

// Critical components - load immediately
import LandingPage from "./pages/LandingPage.tsx";
import Login from "./pages/Login.tsx";
import SignUp from "./pages/SignUp.tsx";
import Layout from "./components/Layout.tsx";
import ProtectedRoute from "./components/ProtectedRoute.tsx";

// Lazy load non-critical routes for better initial load
const Dashboard = lazy(() => import("./pages/Dashboard.tsx"));
const ProgressDashboard = lazy(() => import("./pages/ProgressDashboard.tsx"));
const Settings = lazy(() => import("./pages/Settings.tsx"));
const ClassesPage = lazy(() => import("./pages/ClassesPage.tsx"));
const OAuthRedirect = lazy(() => import("./components/OAuthRedirect.tsx"));
const PracticeRouter = lazy(() => import("./pages/PracticeRouter.tsx"));
const PracticeDashboard = lazy(() => import("./pages/PracticeDashboard.tsx"));
const UnderConstructionPage = lazy(
  () => import("./pages/UnderConstructionPage.tsx")
);
const About = lazy(() => import("./pages/About.tsx"));
const Contact = lazy(() => import("./pages/Contact.tsx"));
const Privacy = lazy(() => import("./pages/Privacy.tsx"));
const ToastTestPage = lazy(() => import("./pages/ToastTestPage.tsx"));

// Lazy load comparison pages
const ABCmouseHookedOnPhonicsComparison = lazy(
  () => import("./pages/comparisons/ABCmouseVsHookedOnPhonics.tsx")
);
const ReadingEggsStarfallComparison = lazy(
  () => import("./pages/comparisons/ReadingEggsVsStarfall.tsx")
);
const HomerKhanAcademyKidsComparison = lazy(
  () => import("./pages/comparisons/HomerVsKhanAcademyKids.tsx")
);
const HookedOnPhonicsComparison = lazy(
  () => import("./pages/comparisons/HookedOnPhonicsVsWordWizAI.tsx")
);
const BestFreeReadingAppsComparison = lazy(
  () => import("./pages/comparisons/BestFreeReadingApps.tsx")
);
const LexiaRazKidsComparison = lazy(
  () => import("./pages/comparisons/LexiaVsRazKids.tsx")
);
const TeachMonsterABCyaComparison = lazy(
  () => import("./pages/comparisons/TeachMonsterVsABCya.tsx")
);
const IXLDuolingoABCComparison = lazy(
  () => import("./pages/comparisons/IXLVsDuolingoABC.tsx")
);

// Lazy load article pages
const WhyChildHatesReading = lazy(
  () => import("./pages/articles/WhyChildHatesReading.tsx")
);
const ChildPronounceWordsWrong = lazy(
  () => import("./pages/articles/ChildPronounceWordsWrong.tsx")
);
const DecodableBooksVsLeveledReaders = lazy(
  () => import("./pages/articles/DecodableBooksVsLeveledReaders.tsx")
);
const CantBlendSounds = lazy(
  () => import("./pages/articles/CantBlendSounds.tsx")
);
const GuessesWords = lazy(
  () => import("./pages/articles/GuessesWords.tsx")
);

// Lazy load guide pages
const ChoosingReadingApp = lazy(
  () => import("./pages/guides/ChoosingReadingApp.tsx")
);
const TeachingPhonicsAtHome = lazy(
  () => import("./pages/guides/TeachingPhonicsAtHome.tsx")
);
const IsTeacherTeachingPhonics = lazy(
  () => import("./pages/guides/IsTeacherTeachingPhonics.tsx")
);
const PhonemeAwarenessGuide = lazy(
  () => import("./pages/guides/PhonemeAwarenessGuide.tsx")
);
const TeachCVCWords = lazy(
  () => import("./pages/guides/TeachCVCWords.tsx")
);
const TeachConsonantBlends = lazy(
  () => import("./pages/guides/TeachConsonantBlends.tsx")
);
const DailyPhonicsRoutine = lazy(
  () => import("./pages/guides/DailyPhonicsRoutine.tsx")
);
const ShortVowelSounds = lazy(
  () => import("./pages/guides/ShortVowelSounds.tsx")
);
const DecodableSentences = lazy(
  () => import("./pages/guides/DecodableSentences.tsx")
);
const FiveMinuteActivities = lazy(
  () => import("./pages/guides/FiveMinuteActivities.tsx")
);
const RControlledVowels = lazy(
  () => import("./pages/guides/RControlledVowels.tsx")
);
const PhonicsWithoutWorksheets = lazy(
  () => import("./pages/guides/PhonicsWithoutWorksheets.tsx")
);
const ChildReadsSlowly = lazy(
  () => import("./pages/articles/ChildReadsSlowly.tsx")
);
const SkipsWords = lazy(
  () => import("./pages/articles/SkipsWords.tsx")
);
const TutorVsApp = lazy(
  () => import("./pages/comparisons/TutorVsApp.tsx")
);
const AIvsTraditional = lazy(
  () => import("./pages/comparisons/AIvsTraditional.tsx")
);
const FreeVsPaid = lazy(
  () => import("./pages/comparisons/FreeVsPaid.tsx")
);

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
);

function App() {
  return (
    <div className="font-body">
      <Analytics />
      <Toaster />
      <BrowserRouter>
        <AuthProvider>
          <SettingsProvider>
            <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/about" element={<About />} />
                  <Route path="/contact" element={<Contact />} />
                  <Route path="/privacy" element={<Privacy />} />
                  <Route path="/signup" element={<SignUp />} />

                  {/* Comparison Pages */}
                  <Route
                    path="/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai"
                    element={<ABCmouseHookedOnPhonicsComparison />}
                  />
                  <Route
                    path="/comparisons/reading-eggs-vs-starfall-vs-word-wiz-ai"
                    element={<ReadingEggsStarfallComparison />}
                  />
                  <Route
                    path="/comparisons/homer-vs-khan-academy-kids-vs-word-wiz-ai"
                    element={<HomerKhanAcademyKidsComparison />}
                  />
                  <Route
                    path="/comparisons/hooked-on-phonics-vs-word-wiz-ai"
                    element={<HookedOnPhonicsComparison />}
                  />
                  <Route
                    path="/comparisons/best-free-reading-apps"
                    element={<BestFreeReadingAppsComparison />}
                  />
                  <Route
                    path="/comparisons/lexia-vs-raz-kids-vs-word-wiz-ai"
                    element={<LexiaRazKidsComparison />}
                  />
                  <Route
                    path="/comparisons/teach-your-monster-vs-abcya-vs-word-wiz-ai"
                    element={<TeachMonsterABCyaComparison />}
                  />
                  <Route
                    path="/comparisons/ixl-vs-duolingo-abc-vs-word-wiz-ai"
                    element={<IXLDuolingoABCComparison />}
                  />
                  <Route
                    path="/comparisons/reading-tutor-vs-reading-app"
                    element={<TutorVsApp />}
                  />
                  <Route
                    path="/comparisons/ai-reading-app-vs-traditional-phonics-program"
                    element={<AIvsTraditional />}
                  />
                  <Route
                    path="/comparisons/free-phonics-apps-vs-paid-reading-programs"
                    element={<FreeVsPaid />}
                  />

                  {/* Article Pages */}
                  <Route
                    path="/articles/why-child-hates-reading"
                    element={<WhyChildHatesReading />}
                  />
                  <Route
                    path="/articles/child-pronounces-words-wrong"
                    element={<ChildPronounceWordsWrong />}
                  />
                  <Route
                    path="/articles/decodable-books-vs-leveled-readers"
                    element={<DecodableBooksVsLeveledReaders />}
                  />
                  <Route
                    path="/articles/child-cant-blend-sounds-into-words"
                    element={<CantBlendSounds />}
                  />
                  <Route
                    path="/articles/kindergartener-guesses-words-instead-sounding-out"
                    element={<GuessesWords />}
                  />
                  <Route
                    path="/articles/child-reads-slowly-struggles-with-fluency"
                    element={<ChildReadsSlowly />}
                  />
                  <Route
                    path="/articles/first-grader-skips-words-when-reading-aloud"
                    element={<SkipsWords />}
                  />

                  {/* Guide Pages */}
                  <Route
                    path="/guides/how-to-choose-reading-app"
                    element={<ChoosingReadingApp />}
                  />
                  <Route
                    path="/guides/how-to-teach-phonics-at-home"
                    element={<TeachingPhonicsAtHome />}
                  />
                  <Route
                    path="/guides/is-teacher-teaching-enough-phonics"
                    element={<IsTeacherTeachingPhonics />}
                  />
                  <Route
                    path="/guides/phoneme-awareness-complete-guide"
                    element={<PhonemeAwarenessGuide />}
                  />
                  <Route
                    path="/guides/how-to-teach-cvc-words-to-struggling-readers"
                    element={<TeachCVCWords />}
                  />
                  <Route
                    path="/guides/teaching-consonant-blends-kindergarten-at-home"
                    element={<TeachConsonantBlends />}
                  />
                  <Route
                    path="/guides/daily-phonics-practice-routine-kindergarten-at-home"
                    element={<DailyPhonicsRoutine />}
                  />
                  <Route
                    path="/guides/short-vowel-sounds-exercises-beginning-readers"
                    element={<ShortVowelSounds />}
                  />
                  <Route
                    path="/guides/decodable-sentences-for-beginning-readers"
                    element={<DecodableSentences />}
                  />
                  <Route
                    path="/guides/five-minute-reading-practice-activities-kids"
                    element={<FiveMinuteActivities />}
                  />
                  <Route
                    path="/guides/r-controlled-vowels-teaching-strategies-parents"
                    element={<RControlledVowels />}
                  />
                  <Route
                    path="/guides/phonics-practice-without-worksheets-kindergarten"
                    element={<PhonicsWithoutWorksheets />}
                  />

                  <Route path="/toast-test" element={<ToastTestPage />} />
                  <Route path="/oauth-callback" element={<OAuthRedirect />} />
                  <Route
                    path="/practice/:sessionId"
                    element={
                      <ProtectedRoute>
                        <PracticeRouter />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Outlet />
                        </Layout>
                      </ProtectedRoute>
                    }
                  >
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/progress" element={<ProgressDashboard />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/practice" element={<PracticeDashboard />} />
                    <Route path="/classes" element={<ClassesPage />} />
                  </Route>
                  <Route path="*" element={<UnderConstructionPage />} />
                </Routes>
              </Suspense>
            </ThemeProvider>
          </SettingsProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
