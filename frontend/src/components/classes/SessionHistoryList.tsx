import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar, ChevronDown, ChevronUp, BookOpen } from "lucide-react";
import { type SessionActivity } from "@/api";

interface SessionHistoryListProps {
  sessions: SessionActivity[];
  calculationWindow: string;
}

const SessionHistoryList = ({
  sessions,
  calculationWindow,
}: SessionHistoryListProps) => {
  const [expanded, setExpanded] = useState(false);
  const displayedSessions = expanded ? sessions : sessions.slice(0, 5);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 85) return "bg-green-100 text-green-800 border-green-300";
    if (accuracy >= 70)
      return "bg-yellow-100 text-yellow-800 border-yellow-300";
    return "bg-orange-100 text-orange-800 border-orange-300";
  };

  if (sessions.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <Calendar className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No recent practice sessions</p>
        <p className="text-sm mt-1">
          Based on {calculationWindow.toLowerCase()}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-muted-foreground">
          Showing {displayedSessions.length} of {sessions.length} sessions (
          {calculationWindow})
        </p>
      </div>

      <div className="space-y-2">
        {displayedSessions.map((session) => (
          <div
            key={session.session_id}
            className="bg-muted rounded-lg p-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-3 flex-1">
              <Calendar className="w-4 h-4 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">
                  {formatDate(session.date)}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                  <BookOpen className="w-3 h-3" />
                  <span>{session.sentence_count} sentences</span>
                </div>
              </div>
            </div>
            <div
              className={`px-3 py-1 rounded-full text-xs font-medium border ${getAccuracyColor(
                session.accuracy
              )}`}
            >
              {session.accuracy.toFixed(1)}%
            </div>
          </div>
        ))}
      </div>

      {sessions.length > 5 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="w-full"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-4 h-4 mr-2" />
              Show Less
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4 mr-2" />
              Show All {sessions.length} Sessions
            </>
          )}
        </Button>
      )}
    </div>
  );
};

export default SessionHistoryList;
