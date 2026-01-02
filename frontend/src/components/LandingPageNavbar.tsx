import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import { wordWizIcon } from "@/assets";
import { motion } from "framer-motion";
import { googleLogin } from "@/api";
import { GoogleIcon } from "./GoogleIcon";

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
            <GoogleIcon className="w-5 h-5 mr-2 hidden sm:block" />
            <span className="hidden sm:inline">Sign in with Google</span>
            <span className="sm:hidden">Sign In</span>
          </Button>
        </motion.div>
      </div>
    </nav>
  );
};

export default LandingPageNavbar;
