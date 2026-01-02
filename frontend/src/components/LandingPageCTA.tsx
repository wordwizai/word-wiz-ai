import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { BookOpen } from "lucide-react";
import { googleLogin } from "@/api";
import { Button } from "./ui/button";
import { GoogleIcon } from "./GoogleIcon";

interface LandingPageCTAProps {
  fadeUpVariant: {
    hidden: { opacity: number; y: number };
    visible: { opacity: number; y: number };
  };
}

const LandingPageCTA = ({ fadeUpVariant }: LandingPageCTAProps) => {
  return (
    <motion.section
      className="px-6 py-20 bg-muted/30"
      variants={fadeUpVariant}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-4xl mx-auto text-center space-y-8">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">
          Start Reading Practice Today
        </h2>
        <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
          Join thousands of families using Word Wiz AI for personalized phonics
          practice with AI-powered pronunciation feedback. No credit card
          required, no ads, no subscriptions.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
          <Button
            size="lg"
            className="min-h-[56px] px-8 text-base font-semibold"
            onClick={() => googleLogin()}
          >
            <GoogleIcon className="w-5 h-5 mr-2" />
            Sign in with Google
          </Button>
          <Link to="/signup">
            <Button
              variant="outline"
              size="lg"
              className="min-h-[56px] px-8 text-base font-semibold"
            >
              <BookOpen className="w-5 h-5 mr-2" />
              Create Account
            </Button>
          </Link>
        </div>
      </div>
    </motion.section>
  );
};

export default LandingPageCTA;
