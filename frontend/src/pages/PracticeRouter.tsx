import { Link, useParams, useNavigate } from "react-router-dom";
import { useContext, useEffect, useState } from "react";
import { getSession } from "../api"; // your API call
import { AuthContext } from "@/contexts/AuthContext";
import type { Session } from "@/api";
import GenericPractice from "@/components/practice/GenericPractice";
import { Button } from "@/components/ui/button";
import { getErrorStatus, OFFLINE_MESSAGE } from "@/utils/errorHandling";

type LoadError = "missing" | "offline";

export default function PracticeRouter() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { token } = useContext(AuthContext);
  const [session, setSession] = useState<Session | null>(null);
  const [loadError, setLoadError] = useState<LoadError | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const id = Number(sessionId);
    if (!sessionId || !Number.isInteger(id) || id <= 0) {
      setLoadError("missing");
      return;
    }
    setLoadError(null);
    let cancelled = false;
    getSession(token ?? "", id)
      .then((s) => {
        if (cancelled) return;
        if (s?.is_completed) navigate("/dashboard");
        else setSession(s);
      })
      .catch((err) => {
        if (cancelled) return;
        // Without this the page said "Loading..." forever. A 4xx means the
        // session is someone else's, was deleted, or the URL is mangled.
        const status = getErrorStatus(err);
        setLoadError(status !== undefined && status < 500 ? "missing" : "offline");
      });
    return () => {
      cancelled = true;
    };
  }, [token, sessionId, navigate, attempt]);

  if (loadError) {
    return (
      <div className="flex min-h-dvh items-center justify-center p-6">
        <div className="max-w-sm space-y-4 text-center">
          <h1 className="text-xl font-semibold text-foreground">
            {loadError === "missing"
              ? "We couldn't find that practice session"
              : "Can't connect right now"}
          </h1>
          <p className="text-muted-foreground">
            {loadError === "missing"
              ? "It may have come from an old link. Pick an activity on your dashboard to start reading again."
              : OFFLINE_MESSAGE}
          </p>
          <div className="flex justify-center gap-3">
            {loadError === "offline" && (
              <Button
                variant="outline"
                className="rounded-xl"
                onClick={() => setAttempt((n) => n + 1)}
              >
                Try again
              </Button>
            )}
            <Button asChild className="rounded-xl">
              <Link to="/dashboard">Go to your dashboard</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex min-h-dvh items-center justify-center" role="status">
        <div className="size-12 animate-spin rounded-full border-b-2 border-primary" />
        <span className="sr-only">Loading your practice</span>
      </div>
    );
  }

  // Render the correct practice type based on session.type
  return (
    <GenericPractice
      session={session}
      activityType={session.activity.activity_type}
    />
  ); // Adjust this line to match your practice component
}
