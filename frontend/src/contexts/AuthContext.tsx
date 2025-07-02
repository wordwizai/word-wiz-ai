import { createContext, useState, useEffect, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser, fetchUserProfile, registerUser } from "../api";

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
    username: string,
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
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  user: { id: "", username: "adsf", email: "", full_name: "Guest" },
  loginWithEmailAndPassword: async () => {},
  register: async () => {},
  logout: () => {},
  loginWithGoogleToken: async () => {},
});

const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token"),
  );
  const [user, setUser] = useState<User | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      const getUser = async () => {
        try {
          const user = await fetchUserProfile(token);
          setUser(user);
        } catch (error) {
          console.error("Error fetching user profile:", error);
          logout(); // Logout if token is invalid
        }
      };
      getUser();
    }
  }, [token]);

  const loginWithEmailAndPassword = async (
    username: string,
    password: string,
  ): Promise<void> => {
    // username is an alias for email in this context
    const response = await loginUser({ username, password });
    if (response?.access_token) {
      setToken(response.access_token);
      localStorage.setItem("token", response.access_token);
      const userProfile = await fetchUserProfile(response.access_token);
      setUser(userProfile);
      navigate("/dashboard");
    }
  };

  const loginWithGoogleToken = async (token: string): Promise<void> => {
    setToken(token);
    localStorage.setItem("token", token);
    const userProfile = await fetchUserProfile(token);
    setUser(userProfile);
    navigate("/dashboard");
  };

  const register = async (
    username: string,
    email: string,
    password: string,
    full_name: string,
  ): Promise<void> => {
    await registerUser({ username, email, password, full_name });
    navigate("/login");
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
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
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export { AuthProvider, AuthContext };
export type { User, AuthContextType };
