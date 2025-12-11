import { useState, useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Copy, Check } from "lucide-react";
import { createClass } from "@/api";

interface CreateClassDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

const CreateClassDialog = ({
  open,
  onOpenChange,
  onCreated,
}: CreateClassDialogProps) => {
  const { token } = useContext(AuthContext);
  const [className, setClassName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [createdClass, setCreatedClass] = useState<{
    name: string;
    join_code: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !className.trim()) return;

    setLoading(true);
    setError("");

    try {
      const newClass = await createClass(token, className.trim());
      setCreatedClass({ name: newClass.name, join_code: newClass.join_code });
      setClassName("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create class");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    if (createdClass) {
      navigator.clipboard.writeText(createdClass.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClose = () => {
    setCreatedClass(null);
    setClassName("");
    setError("");
    setCopied(false);
    onOpenChange(false);
    if (createdClass) {
      onCreated();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        {!createdClass ? (
          <>
            <DialogHeader>
              <DialogTitle>Create a New Class</DialogTitle>
              <DialogDescription>
                Create a class for students to join. You'll get a unique join
                code to share with them.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="className">Class Name</Label>
                  <Input
                    id="className"
                    placeholder="e.g., Grade 5 Reading"
                    value={className}
                    onChange={(e) => setClassName(e.target.value)}
                    disabled={loading}
                  />
                </div>
                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={loading || !className.trim()}>
                  {loading ? "Creating..." : "Create Class"}
                </Button>
              </DialogFooter>
            </form>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Class Created Successfully! 🎉</DialogTitle>
              <DialogDescription>
                Share this join code with your students so they can join your
                class.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label>Class Name</Label>
                <div className="font-semibold text-lg">
                  {createdClass.name}
                </div>
              </div>
              <div className="grid gap-2">
                <Label>Join Code</Label>
                <div className="flex items-center gap-2">
                  <div className="flex-1 p-3 bg-pastel-lavender rounded-lg border-2 border-primary/20">
                    <div className="text-2xl font-bold tracking-wider text-center font-mono">
                      {createdClass.join_code}
                    </div>
                  </div>
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    onClick={handleCopyCode}
                    className="shrink-0"
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Students can join using this code in the "Join Class" tab
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default CreateClassDialog;
