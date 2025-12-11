import { useState, useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UserPlus } from "lucide-react";
import { joinClass } from "@/api";

interface JoinClassDialogProps {
  onJoined: () => void;
  showAsCard?: boolean;
}

const JoinClassDialog = ({
  onJoined,
  showAsCard = false,
}: JoinClassDialogProps) => {
  const { token } = useContext(AuthContext);
  const [joinCode, setJoinCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !joinCode.trim()) return;

    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      await joinClass(token, joinCode.trim());
      setSuccess(true);
      setJoinCode("");
      setTimeout(() => {
        setSuccess(false);
        onJoined();
      }, 1500);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        "Failed to join class. Please check the code and try again.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Convert to uppercase automatically
    setJoinCode(e.target.value.toUpperCase());
    setError("");
  };

  if (showAsCard) {
    return (
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <CardHeader className="p-4">
          <h2 className="text-lg font-bold text-foreground">Join a Class</h2>
          <p className="text-sm text-muted-foreground">
            Enter the join code provided by your teacher to join their class
          </p>
        </CardHeader>
        <CardContent className="p-4 pt-0">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="joinCode">Join Code</Label>
              <Input
                id="joinCode"
                placeholder="Enter 6-8 character code"
                value={joinCode}
                onChange={handleInputChange}
                disabled={loading || success}
                className="font-mono text-lg tracking-wider uppercase"
                maxLength={10}
              />
              {error && <p className="text-sm text-destructive">{error}</p>}
              {success && (
                <p className="text-sm text-green-600">
                  Successfully joined class! 🎉
                </p>
              )}
            </div>
            <Button
              type="submit"
              disabled={loading || !joinCode.trim() || success}
              className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90"
            >
              <UserPlus className="w-4 h-4 mr-2" />
              {loading ? "Joining..." : success ? "Joined!" : "Join Class"}
            </Button>
          </form>
        </CardContent>
      </Card>
    );
  }

  return null;
};

export default JoinClassDialog;
