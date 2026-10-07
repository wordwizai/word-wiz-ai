import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import { wordWizIcon } from "@/assets";
import { trackSignupClick } from "@/utils/analytics";
import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";

const LandingPageNavbar = () => {
  // Parents who are already signed in come back through the home page too;
  // offer them the app, not another sign-up.
  const { token } = useContext(AuthContext);

  return (
    <nav className="w-full px-4 sm:px-6 py-4 sticky top-0 z-50 glass-navbar flex flex-row items-center justify-between gap-3 sm:gap-0">
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
        {token ? (
          <Button asChild size="default">
            <Link to="/dashboard">Go to dashboard</Link>
          </Button>
        ) : (
          <>
            {/* Shown on phones too: email users coming back had to scroll
                to the footer to find a way in. Hidden only below 360px,
                where it would push Sign Up off the edge. */}
            <Button
              asChild
              variant="ghost"
              size="default"
              className="hidden px-3 min-[360px]:inline-flex sm:px-4"
            >
              <Link to="/login">Log In</Link>
            </Button>
            <Button asChild size="default">
              <Link
                to="/signup"
                onClick={() => trackSignupClick("navbar", "link")}
              >
                Sign Up
              </Link>
            </Button>
          </>
        )}
      </div>
    </nav>
  );
};

export default LandingPageNavbar;
