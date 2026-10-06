import { useContext } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { WifiOff } from "lucide-react";
import { AuthContext } from "@/contexts/AuthContext";
import { rememberPostLoginRedirect } from "@/lib/postLoginRedirect";
import { Button } from "@/components/ui/button";
import { OFFLINE_MESSAGE } from "@/utils/errorHandling";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { token, user, profileLoadFailed, retryProfileLoad } =
    useContext(AuthContext);
  const location = useLocation();

  // Not signed in: send them to log in, then bring them back here.
  if (!token) {
    rememberPostLoginRedirect(location.pathname + location.search);
    return <Navigate to="/login" replace />;
  }

  // Signed in, but the profile request failed for a reason other than a bad
  // token. Keep the session and let them retry instead of spinning forever.
  if (!user && profileLoadFailed) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="max-w-sm text-center space-y-4">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-muted flex items-center justify-center">
            <WifiOff className="w-7 h-7 text-muted-foreground" />
          </div>
          <h1 className="text-xl font-semibold">Can't connect right now</h1>
          <p className="text-muted-foreground">{OFFLINE_MESSAGE}</p>
          <Button onClick={retryProfileLoad} className="rounded-xl">
            Try again
          </Button>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center" role="status">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
