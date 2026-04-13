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
import { AuthContext, type AuthContextType } from "@/contexts/AuthContext";
import { useContext } from "react";
import React from "react";
import { AlertCircleIcon } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { googleLogin } from "@/api";
import { trackSignupClick } from "@/utils/analytics";

export function CreateAccountForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [fullName, setFullName] = React.useState("");
  const [username, setUsername] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const { register, loginWithEmailAndPassword } =
    useContext<AuthContextType>(AuthContext);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      trackSignupClick('signup_form', 'email');
      await register(username, email, password, fullName);
      await loginWithEmailAndPassword(username, password);
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
    <div
      className={cn("flex flex-col gap-6 max-w-sm w-full", className)}
      {...props}
    >
      <Card className="rounded-2xl border-2 border-border shadow-lg">
        <CardHeader className="text-center pb-2">
          <CardTitle className="text-2xl font-bold">Create your account</CardTitle>
          <CardDescription className="text-sm">
            Start your reading journey today
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
                  trackSignupClick('signup_form', 'google');
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
                  <Label htmlFor="name" className="text-sm font-medium">Full name</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="Your name"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    disabled={loading}
                    className="h-11 rounded-xl"
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="username" className="text-sm font-medium">Username</Label>
                  <Input
                    id="username"
                    type="text"
                    placeholder="Choose a username"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={loading}
                    className="h-11 rounded-xl"
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="signup-email" className="text-sm font-medium">Email</Label>
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="you@example.com"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                    className="h-11 rounded-xl"
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="signup-password" className="text-sm font-medium">Password</Label>
                  <Input
                    id="signup-password"
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
                    <AlertTitle>Unable to create account</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button
                  type="submit"
                  className="w-full h-11 rounded-xl font-semibold"
                  disabled={loading}
                >
                  {loading ? "Creating account…" : "Create account"}
                </Button>

                <p className="text-center text-sm text-muted-foreground">
                  Already have an account?{" "}
                  <a href="/login" className="text-primary font-medium underline-offset-4 hover:underline">
                    Sign in
                  </a>
                </p>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
