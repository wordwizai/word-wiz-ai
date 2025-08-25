import { motion } from "framer-motion";
import { Link } from "react-router-dom";

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
          Start Reading Smarter Today
        </h2>
        <p className="text-muted-foreground max-w-md mx-auto">
          Get personalized feedback on your reading for free.
        </p>
        <Link
          className="inline-block bg-primary text-primary-foreground py-3 px-8 rounded-lg font-semibold transition-all duration-300 hover:shadow-md w-full max-w-xs mx-auto md:mx-0"
          to="/signup"
          as={motion.a}
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          📖 Create a Word Wiz account
        </Link>
      </div>
    </motion.section>
  );
};

export default LandingPageCTA;
