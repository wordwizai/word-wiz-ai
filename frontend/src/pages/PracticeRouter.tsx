import { useParams, useNavigate } from "react-router-dom";
import { useContext, useEffect, useState } from "react";
import { getSession } from "../api"; // your API call
import UnlimitedPractice from "./UnlimitedPractice";
import { AuthContext } from "@/contexts/AuthContext";
import type { Session } from "@/api";

export default function PracticeRouter() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { token } = useContext(AuthContext);
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard");
      return;
    }
    getSession(token ?? "", parseInt(sessionId)).then((s) => {
      if (s?.is_completed) navigate("/dashboard");
      else setSession(s);
    });
  }, [token, sessionId, navigate]);

  if (!session) return <div>Loading...</div>;

  // Render the correct practice type based on session.type
  switch (session.activity.activity_type) {
    case "unlimited":
      return <UnlimitedPractice session={session} />;
    // Add more cases for other practice types
    default:
      return <div>Unknown practice type</div>;
  }
}
