import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getSession } from "../api"; // your API call

export default function Practice() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard");
      return;
    }
    getSession(sessionId).then((s) => {
      if (s?.is_completed) navigate("/dashboard");
      else setSession(s);
    });
  }, [sessionId, navigate]);

  if (!session) return <div>Loading...</div>;

  // Render the correct practice type based on session.type
  switch (session.type) {
    case "unlimited":
      return <UnlimitedPractice session={session} />;
    // Add more cases for other practice types
    default:
      return <div>Unknown practice type</div>;
  }
}
