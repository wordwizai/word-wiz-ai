import { CreateAccountForm } from "@/components/create-account-form";

const SignUp = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background p-4">
      <CreateAccountForm className="max-w-md w-full" />
    </div>
  );
};

export default SignUp;
