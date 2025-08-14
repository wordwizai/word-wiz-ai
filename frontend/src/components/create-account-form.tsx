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
import { motion } from "framer-motion";
import { 
  formContainerVariants, 
  formFieldVariants, 
  buttonHover, 
  buttonTap 
} from "@/lib/animations";

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

  const { register } = useContext<AuthContextType>(AuthContext);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register(username, email, password, fullName);
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
    <motion.div
      className={cn("flex flex-col gap-6 max-w-sm w-full mx-auto", className)}
      initial="hidden"
      animate="visible"
      variants={formContainerVariants}
      {...props}
    >
      <motion.div variants={formFieldVariants}>
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-xl">Create your account</CardTitle>
            <CardDescription>Fill in your details to sign up</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-6">
                <motion.div 
                  className="grid gap-3"
                  variants={formFieldVariants}
                >
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="Your Name"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    disabled={loading}
                  />
                </motion.div>
                <motion.div 
                  className="grid gap-3"
                  variants={formFieldVariants}
                >
                  <Label htmlFor="email">Username</Label>
                  <Input
                    id="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={loading}
                  />
                </motion.div>
                <motion.div 
                  className="grid gap-3"
                  variants={formFieldVariants}
                >
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                  />
                </motion.div>
                <motion.div 
                  className="grid gap-3"
                  variants={formFieldVariants}
                >
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                  />
                </motion.div>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Alert variant="destructive">
                      <AlertCircleIcon />
                      <AlertTitle>Unable to Create an account</AlertTitle>
                      <AlertDescription>
                        <p>{error}</p>
                      </AlertDescription>
                    </Alert>
                  </motion.div>
                )}
                <motion.div
                  variants={formFieldVariants}
                  whileHover={buttonHover}
                  whileTap={buttonTap}
                >
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Creating Account..." : "Create Account"}
                  </Button>
                </motion.div>
                <motion.div 
                  className="text-center text-sm"
                  variants={formFieldVariants}
                >
                  Already have an account?{" "}
                  <a href="/login" className="underline underline-offset-4">
                    Login
                  </a>
                </motion.div>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
