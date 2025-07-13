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

function App() {
  return (
    <div className="">
      <BrowserRouter>
        <AuthProvider>
          <SettingsProvider>
            <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<SignUp />} />
                <Route path="/oauth-callback" element={<OAuthRedirect />} />
                <Route
                  path="/practice/:sessionId"
                  element={<PracticeRouter />}
                />
                <Route
                  element={
                    <Layout>
                      <Outlet />
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
