import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { BookOpen } from "lucide-react";

interface LandingPageCTAProps {
  fadeUpVariant: {
    hidden: { opacity: number; y: number };
    visible: { opacity: number; y: number };
  };
}

const LandingPageCTA = ({ fadeUpVariant }: LandingPageCTAProps) => {
  return (
    <motion.section
      className="px-6 py-20 bg-muted/50"
      variants={fadeUpVariant}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-4xl mx-auto text-center space-y-6">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">
          Start Reading Practice Today
        </h2>
        <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
          Join thousands of families using Word Wiz AI for personalized phonics
          practice with AI-powered pronunciation feedback. No credit card
          required, no ads, no subscriptions.
        </p>
        <motion.div
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 300 }}
          className="inline-block"
        >
          <Link
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground py-3 px-8 rounded-lg font-semibold transition-all duration-300 hover:shadow-md w-full max-w-xs mx-auto md:mx-0 justify-center"
            to="/signup"
          >
            <BookOpen className="w-5 h-5" />
            Start Free Reading Practice
          </Link>
        </motion.div>
      </div>
    </motion.section>
  );
};

export default LandingPageCTA;
