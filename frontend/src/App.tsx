import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import Dashboard from "./pages/Dashboard.tsx";
import Layout from "./components/Layout.tsx";
import Login from "./pages/Login.tsx";
import SignUp from "./pages/SignUp.tsx";
import ProgressDashboard from "./pages/ProgressDashboard.tsx";
import Settings from "./pages/Settings.tsx";
import { AuthProvider } from "./contexts/AuthContext.tsx";
import OAuthRedirect from "./components/OAuthRedirect.tsx";
import { ThemeProvider } from "./contexts/ThemeContext.tsx";
import { SettingsProvider } from "./contexts/SettingsContext.tsx";
import PracticeRouter from "./pages/PracticeRouter.tsx";
import PracticeDashboard from "./pages/PracticeDashboard.tsx";
import LandingPage from "./pages/LandingPage.tsx";
import PageTransition from "./components/PageTransition.tsx";

function App() {
  return (
    <div className="font-body">
      <BrowserRouter>
        <AuthProvider>
          <SettingsProvider>
            <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
              <Routes>
                <Route path="/" element={
                  <PageTransition>
                    <LandingPage />
                  </PageTransition>
                } />
                <Route path="/login" element={
                  <PageTransition>
                    <Login />
                  </PageTransition>
                } />
                <Route path="/signup" element={
                  <PageTransition>
                    <SignUp />
                  </PageTransition>
                } />
                <Route path="/oauth-callback" element={<OAuthRedirect />} />
                <Route
                  path="/practice/:sessionId"
                  element={<PracticeRouter />}
                />
                <Route
                  element={
                    <Layout>
                      <PageTransition>
                        <Outlet />
                      </PageTransition>
                    </Layout>
                  }
                >
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/progress" element={<ProgressDashboard />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/practice" element={<PracticeDashboard />} />
                </Route>
              </Routes>
            </ThemeProvider>
          </SettingsProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
