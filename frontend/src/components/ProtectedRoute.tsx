import { useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "@/contexts/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { token, user } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    // If no token, redirect to login immediately
    if (!token) {
      navigate("/login");
      return;
    }

    // If token exists but no user yet, wait for user to be loaded
    // The AuthContext will handle invalid tokens by calling logout()
  }, [token, user, navigate]);

  // If no token, don't render anything (user will be redirected)
  if (!token) {
    return null;
  }

  // If token exists but user is still loading, show loading state
  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // User is authenticated, render the protected content
  return <>{children}</>;
};

export default ProtectedRoute;