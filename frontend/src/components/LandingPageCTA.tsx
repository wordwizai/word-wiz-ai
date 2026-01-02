import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { BookOpen } from "lucide-react";
import { googleLogin } from "@/api";
import { Button } from "./ui/button";

interface LandingPageCTAProps {
  fadeUpVariant: {
    hidden: { opacity: number; y: number };
    visible: { opacity: number; y: number };
  };
}

const LandingPageCTA = ({ fadeUpVariant }: LandingPageCTAProps) => {
  return (
    <motion.section
      className="px-6 py-20 bg-gradient-to-br from-purple-50 via-pink-50/30 to-blue-50/20"
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
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 400 }}
          >
            <Button
              size="lg"
              className="min-h-[56px] px-8 text-lg font-semibold shadow-xl hover:shadow-2xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-0"
              onClick={() => googleLogin()}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                className="w-6 h-6 mr-2"
              >
                <path
                  d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                  fill="currentColor"
                />
              </svg>
              Sign in with Google
            </Button>
          </motion.div>
          <Link to="/signup">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400 }}
            >
              <Button
                variant="outline"
                size="lg"
                className="min-h-[56px] px-8 text-lg font-semibold bg-white/80 hover:bg-white border-2 border-purple-200 hover:border-purple-300"
              >
                <BookOpen className="w-5 h-5 mr-2" />
                Create Account
              </Button>
            </motion.div>
          </Link>
        </div>
      </div>
    </motion.section>
  );
};

export default LandingPageCTA;
