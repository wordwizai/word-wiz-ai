import { CreateAccountForm } from "@/components/create-account-form";
import { wordWizIcon } from "@/assets";
import { Link } from "react-router-dom";

const SignUp = () => {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5 p-4 overflow-hidden">
      {/* Decorative orbs */}
      <div className="absolute -top-24 -left-24 w-72 h-72 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

      {/* Brand header */}
      <Link to="/" className="flex items-center gap-3 mb-8 group">
        <div className="w-12 h-12 bg-gradient-to-br from-primary/60 to-purple-300 rounded-2xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
          <img src={wordWizIcon} alt="Word Wiz AI" className="w-9 h-9" />
        </div>
        <span className="text-xl font-bold text-foreground">
          Word Wiz <span className="text-primary">AI</span>
        </span>
      </Link>

      <CreateAccountForm className="max-w-md w-full relative z-10" />
    </div>
  );
};

export default SignUp;
