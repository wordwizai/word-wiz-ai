import { LoginForm } from "@/components/login-form";

const Login = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background p-4">
      <LoginForm className={"max-w-md w-full"} />
    </div>
  );
};

export default Login;
