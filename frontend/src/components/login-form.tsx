import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import React from "react";
import { AlertCircleIcon } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { googleLogin } from "@/api";

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const { loginWithEmailAndPassword } = useContext(AuthContext);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await loginWithEmailAndPassword(email, password);
      window.location.href = "/dashboard";
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="rounded-2xl border-2 border-border shadow-lg">
        <CardHeader className="text-center pb-2">
          <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
          <CardDescription className="text-sm">
            Sign in to continue your reading journey
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <form onSubmit={handleSubmit}>
            <div className="grid gap-5">
              <Button
                variant="outline"
                className="w-full h-11 rounded-xl border-2 font-medium hover:bg-muted/50 transition-colors"
                type="button"
                disabled={loading}
                onClick={() => {
                  setLoading(true);
                  googleLogin();
                }}
              >
                <svg className="w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                  <path
                    d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                    fill="currentColor"
                  />
                </svg>
                Continue with Google
              </Button>

              <div className="after:border-border relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t">
                <span className="bg-card text-muted-foreground relative z-10 px-2 text-xs uppercase tracking-wide">
                  or email
                </span>
              </div>

              <div className="grid gap-4">
                <div className="grid gap-1.5">
                  <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                    className="h-11 rounded-xl"
                  />
                </div>
                <div className="grid gap-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-sm font-medium">Password</Label>
                    <a
                      href="#"
                      className="text-xs text-muted-foreground hover:text-primary transition-colors underline-offset-4 hover:underline"
                    >
                      Forgot password?
                    </a>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    className="h-11 rounded-xl"
                  />
                </div>

                {error && (
                  <Alert variant="destructive" className="rounded-xl">
                    <AlertCircleIcon className="h-4 w-4" />
                    <AlertTitle>Unable to login</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button
                  type="submit"
                  className="w-full h-11 rounded-xl font-semibold"
                  disabled={loading}
                >
                  {loading ? "Signing in…" : "Sign in"}
                </Button>
              </div>

              <p className="text-center text-sm text-muted-foreground">
                No account?{" "}
                <a href="/signup" className="text-primary font-medium underline-offset-4 hover:underline">
                  Sign up free
                </a>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
