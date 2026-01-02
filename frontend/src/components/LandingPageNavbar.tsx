import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import { wordWizIcon } from "@/assets";
import { googleLogin } from "@/api";
import { GoogleIcon } from "./GoogleIcon";

const LandingPageNavbar = () => {
  return (
    <nav className="w-full px-4 sm:px-6 py-4 sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border flex flex-row items-center justify-between gap-3 sm:gap-0">
      <Link className="flex items-center gap-2" to="/">
        <img src={wordWizIcon} alt="Word Wiz Icon" className="h-8 w-8" />
        <span className="text-lg sm:text-xl font-semibold">Word Wiz AI</span>
      </Link>

      <div className="hidden md:flex items-center gap-6">
        <Link
          to="/about"
          className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          About
        </Link>
        <Link
          to="/contact"
          className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          Contact
        </Link>
      </div>

      <div className="flex flex-row items-center gap-2 w-auto">
        <Link to="/login" className="hidden sm:block">
          <Button variant="ghost" size="default">
            Log In
          </Button>
        </Link>
        <Button
          size="default"
          onClick={() => googleLogin()}
        >
          <GoogleIcon className="w-4 h-4 mr-2 hidden sm:block" />
          <span className="hidden sm:inline">Sign in with Google</span>
          <span className="sm:hidden">Sign In</span>
        </Button>
      </div>
    </nav>
  );
};

export default LandingPageNavbar;
