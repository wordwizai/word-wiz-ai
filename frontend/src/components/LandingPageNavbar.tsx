import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import { wordWizIcon } from "@/assets";
import { motion } from "framer-motion";

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
        <Link to="/login" className="w-full sm:w-auto">
          <Button
            variant="ghost"
            className="w-full min-h-[44px]"
            as={motion.button}
            whileHover={{ scale: 1.05 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            Log In
          </Button>
        </Link>
        <Link to="/signup" className="w-full sm:w-auto">
          <Button
            size="lg"
            className="w-full min-h-[44px]"
            as={motion.button}
            whileHover={{ scale: 1.05 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            Sign Up
          </Button>
        </Link>
      </div>
    </nav>
  );
};

export default LandingPageNavbar;
