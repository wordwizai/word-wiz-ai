// src/pages/OAuthRedirect.tsx
import { AuthContext } from "@/contexts/AuthContext";
import { useContext, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const OAuthRedirect = () => {
  const { loginWithGoogleToken } = useContext(AuthContext);

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get("token");

    if (token) {
      loginWithGoogleToken(token);
    } else {
      navigate("/login");
    }
  }, [location, navigate, loginWithGoogleToken]);

  return <p>Logging you in...</p>;
};

export default OAuthRedirect;
