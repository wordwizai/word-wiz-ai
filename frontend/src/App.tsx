import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import Home from "./pages/Home.tsx";
import Layout from "./components/Layout.tsx";
import Login from "./pages/Login.tsx";
import SignUp from "./pages/SignUp.tsx";
import PhonemePractice from "./pages/PhonemePractice.tsx";
import Feedback from "./pages/Feedback.tsx";
import ProgressDashboard from "./pages/ProgressDashboard.tsx";
import Settings from "./pages/Settings.tsx";
import { AuthProvider } from "./contexts/AuthContext.tsx";

function App() {
  return (
    <div className="">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<SignUp />} />
            <Route
              element={
                <Layout>
                  <Outlet />
                </Layout>
              }
            >
              <Route path="/dashboard" element={<Home />} />
              <Route path="/practice" element={<PhonemePractice />} />
              <Route path="/feedback" element={<Feedback />} />
              <Route path="/progress" element={<ProgressDashboard />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
