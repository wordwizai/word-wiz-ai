import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import { wordWizIcon } from "@/assets";
import { motion } from "framer-motion";
import { googleLogin } from "@/api";

const LandingPageNavbar = () => {
  return (
    <nav className="w-full px-4 sm:px-6 py-4 sticky top-0 z-50 bg-background/70 backdrop-blur border-b border-border flex flex-row items-center justify-between gap-3 sm:gap-0">
      <Link className="flex items-center gap-2" to="/">
        <img src={wordWizIcon} alt="Word Wiz Icon" className="h-8 w-8" />
        <span className="text-lg sm:text-xl font-semibold">Word Wiz AI</span>
      </Link>

      <div className="hidden md:flex items-center gap-6">
        <Link
          to="/about"
          className="text-muted-foreground hover:text-foreground transition-colors font-medium"
        >
          About
        </Link>
        <Link
          to="/contact"
          className="text-muted-foreground hover:text-foreground transition-colors font-medium"
        >
          Contact
        </Link>
      </div>

      <div className="flex flex-row items-center gap-2 w-auto">
        <Link to="/login" className="hidden sm:block">
          <motion.div
            whileHover={{ scale: 1.05 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <Button variant="ghost" className="min-h-[44px]">
              Log In
            </Button>
          </motion.div>
        </Link>
        <motion.div
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Button
            size="lg"
            className="min-h-[44px] bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
            onClick={() => googleLogin()}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              className="w-5 h-5 mr-2 hidden sm:block"
            >
              <path
                d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                fill="currentColor"
              />
            </svg>
            <span className="hidden sm:inline">Sign in with Google</span>
            <span className="sm:hidden">Sign In</span>
          </Button>
        </motion.div>
      </div>
    </nav>
  );
};

export default LandingPageNavbar;
