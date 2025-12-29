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
