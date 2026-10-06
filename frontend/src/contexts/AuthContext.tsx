import { createContext, useState, useEffect, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser, fetchUserProfile, registerUser } from "../api";
import { getErrorStatus } from "@/utils/errorHandling";
import { consumePostLoginRedirect } from "@/lib/postLoginRedirect";

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  [key: string]: any; // For any additional user properties
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  loginWithEmailAndPassword: (
    email: string,
    password: string,
  ) => Promise<void>;
  register: (
    username: string,
    email: string,
    password: string,
    full_name: string,
  ) => Promise<void>;
  logout: () => void;
  loginWithGoogleToken: (token: string) => Promise<void>;
  /** True when the profile couldn't be loaded for a reason other than a bad token (offline, server down). */
  profileLoadFailed: boolean;
  retryProfileLoad: () => void;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  user: { id: "", username: "adsf", email: "", full_name: "Guest" },
  loginWithEmailAndPassword: async () => {},
  register: async () => {},
  logout: () => {},
  loginWithGoogleToken: async () => {},
  profileLoadFailed: false,
  retryProfileLoad: () => {},
});

// Routes that only make sense signed in (the ProtectedRoute ones in App.tsx).
// "/practice" must not match "/practice-words", hence the "/" suffix check.
const SIGNED_IN_ONLY = ["/dashboard", "/practice", "/progress", "/settings", "/classes"];

function isSignedInOnlyPath(pathname: string): boolean {
  return SIGNED_IN_ONLY.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
}

const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token"),
  );
  const [user, setUser] = useState<User | null>(null);
  const [profileLoadFailed, setProfileLoadFailed] = useState(false);
  const [profileAttempt, setProfileAttempt] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      const getUser = async () => {
        try {
          const user = await fetchUserProfile(token);
          setUser(user);
          setProfileLoadFailed(false);
        } catch (error) {
          console.error("Error fetching user profile:", error);
          const status = getErrorStatus(error);
          // Only a rejected token means "sign in again". A dropped
          // connection or a backend restart must not throw away the session.
          if (status === 401 || status === 403 || status === 404) {
            // On a public page (a guide, the try-it page) an expired token
            // shouldn't bounce the visitor to the login screen; just forget
            // it. Signed-in pages still send them to log in again.
            if (isSignedInOnlyPath(window.location.pathname)) {
              logout();
            } else {
              clearSession();
            }
          } else {
            setProfileLoadFailed(true);
          }
        }
      };
      getUser();
    }
  }, [token, profileAttempt]);

  const retryProfileLoad = () => {
    setProfileLoadFailed(false);
    setProfileAttempt((n) => n + 1);
  };

  const loginWithEmailAndPassword = async (
    email: string,
    password: string,
  ): Promise<void> => {
    // The backend's OAuth2 form calls the field "username", but it is the email.
    const response = await loginUser({ username: email, password });
    if (response?.access_token) {
      setToken(response.access_token);
      localStorage.setItem("token", response.access_token);
      const userProfile = await fetchUserProfile(response.access_token);
      setUser(userProfile);
      navigate(consumePostLoginRedirect(), { replace: true });
    }
  };

  const loginWithGoogleToken = async (token: string): Promise<void> => {
    setToken(token);
    localStorage.setItem("token", token);
    const userProfile = await fetchUserProfile(token);
    setUser(userProfile);
    navigate(consumePostLoginRedirect(), { replace: true });
  };

  const register = async (
    username: string,
    email: string,
    password: string,
    full_name: string,
  ): Promise<void> => {
    await registerUser({ username, email, password, full_name });
  };

  const clearSession = () => {
    setToken(null);
    setUser(null);
    setProfileLoadFailed(false);
    localStorage.removeItem("token");
  };

  const logout = () => {
    clearSession();
    navigate("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loginWithEmailAndPassword,
        register,
        logout,
        loginWithGoogleToken,
        profileLoadFailed,
        retryProfileLoad,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export { AuthProvider, AuthContext };
export type { User, AuthContextType };
