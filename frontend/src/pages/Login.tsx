import { LoginForm } from "@/components/login-form";

const Login = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <LoginForm className={"max-w-md w-full"} />
    </div>
  );
};

export default Login;
