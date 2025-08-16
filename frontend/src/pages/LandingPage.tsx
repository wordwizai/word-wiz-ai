import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { demoScreenshot, wordWizIcon } from "@/assets";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const fadeUpVariant = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.15,
    },
  },
};

const childVariant = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const LandingPage = () => {
  return (
    <main className="scroll-smooth bg-background text-foreground">
      {/* Navbar */}
      <nav className="w-full px-4 sm:px-6 py-4 sticky top-0 z-50 bg-background/70 backdrop-blur border-b border-border flex flex-row items-center justify-between gap-3 sm:gap-0">
        <div className="flex items-center gap-2">
          <img src={wordWizIcon} alt="Word Wiz Icon" className="h-8 w-8" />
          <span className="text-lg sm:text-xl font-semibold">Word Wiz AI</span>
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

      {/* Hero Section */}
      <motion.section
        className="px-4 sm:px-6 py-12 sm:py-20 md:py-28 bg-pastel-purple text-foreground"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex flex-col md:flex-row items-center gap-6 sm:gap-8 md:gap-12">
          <div className="flex-1 space-y-4 sm:space-y-6 text-center md:text-left">
            <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-6xl font-extrabold leading-tight text-primary">
              Your Personal Reading Companion
            </h1>
            <p className="text-sm sm:text-base md:text-lg lg:text-xl text-muted-foreground max-w-full sm:max-w-xl mx-auto md:mx-0">
              Word Wiz AI helps you become a better reader by analyzing your
              mistakes and recommending engaging texts that sharpen your skills.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center md:justify-start">
              <Link to="/signup" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  className="w-full sm:w-auto min-h-[48px]"
                  as={motion.button}
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  📖 Create an Account
                </Button>
              </Link>
              <a href="#how-it-works-section" className="w-full sm:w-auto">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full sm:w-auto min-h-[48px]"
                  as={motion.button}
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  🔍 How It Works
                </Button>
              </a>
            </div>
          </div>
          <div className="flex-1 max-w-full">
            <div className="bg-muted border border-border rounded-2xl aspect-[4/3] flex items-center justify-center max-w-full">
              <img
                src={demoScreenshot}
                alt="Word Wiz AI Demo"
                className="w-full h-full object-cover rounded-2xl p-2 bg-background"
              />
            </div>
          </div>
        </div>
      </motion.section>

      {/* What Makes Word Wiz Unique */}
      <motion.section
        className="px-6 py-20 bg-muted/50"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto text-center space-y-10">
          <h2 className="text-3xl md:text-4xl font-bold">
            What Makes Word Wiz Unique?
          </h2>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                icon: "📊",
                title: "Spot Reading Patterns",
                text: "Get instant feedback on where you pause, stumble, or misread.",
              },
              {
                icon: "✍️",
                title: "Improve Pronunciation",
                text: "Receive tailored pronunciation tips to enhance fluency.",
              },
              {
                icon: "💰",
                title: "Completely Free",
                text: "No ads, no subscriptions. Our mission is to help kids across the country read better *without* cost",
              },
            ].map((feature, i) => (
              <motion.div
                key={i}
                className="bg-card p-6 rounded-2xl shadow-md text-left"
                variants={childVariant}
              >
                <div className="text-3xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.text}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Who It's For Section */}
      <motion.section
        className="px-6 py-20 bg-background border-t border-border"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto text-center space-y-10">
          <h2 className="text-3xl md:text-4xl font-bold">Who It's For</h2>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                icon: "🧒",
                title: "Young Readers",
                text: "Boost reading confidence with personalized feedback.",
              },
              {
                icon: "🧑‍🏫",
                title: "Educators",
                text: "Integrate AI reading feedback into your classroom reading programs.",
              },
              {
                icon: "🧑",
                title: "Parents",
                text: "Empower your kids with personalized reading feedback.",
              },
            ].map((target, i) => (
              <motion.div
                key={i}
                className="bg-muted p-6 rounded-2xl shadow-md"
                variants={childVariant}
              >
                <div className="text-3xl mb-4">{target.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{target.title}</h3>
                <p className="text-muted-foreground">{target.text}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* How It Works */}
      <motion.section
        id="how-it-works-section"
        className="px-6 py-20 bg-background border-t border-border"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto space-y-10">
          <h2 className="text-3xl md:text-4xl font-bold text-center">
            How It Works
          </h2>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                step: "1",
                title: "Read Aloud",
                text: "Practice reading passages aloud and let Word Wiz listen.",
              },
              {
                step: "2",
                title: "AI Analysis",
                text: "We highlight misread words, pauses, and fluency metrics.",
              },
              {
                step: "3",
                title: "Personal Feedback",
                text: "You get guidance, scores, and recommended practice.",
              },
            ].map((step, i) => (
              <motion.div key={i} variants={childVariant}>
                <Card className="p-6 rounded-2xl shadow-md bg-muted">
                  <CardHeader>
                    <div className="bg-primary text-white w-12 h-12 flex items-center justify-center rounded-full mb-4">
                      {step.step}
                    </div>
                    <CardTitle>{step.title}</CardTitle>
                    <CardDescription>{step.text}</CardDescription>
                  </CardHeader>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Testimonials Section */}
      <motion.section
        className="px-6 py-20 bg-muted/50"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-4xl mx-auto text-center space-y-10">
          <h2 className="text-3xl md:text-4xl font-bold">
            What Readers Are Saying
          </h2>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                name: "Alex, Grade 4",
                quote:
                  "Word Wiz made reading fun and helped me feel more confident!",
              },
              {
                name: "Mrs. Rivera, Teacher",
                quote:
                  "A game changer in my classroom. Every student is improving.",
              },
            ].map((testimonial, i) => (
              <motion.div key={i} variants={childVariant}>
                <Card className="p-6 bg-background border border-border rounded-2xl shadow-sm">
                  <CardContent className="space-y-4">
                    <p className="italic">“{testimonial.quote}”</p>
                    <p className="font-semibold">— {testimonial.name}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* CTA button */}
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
            Get personalized feedback and book recommendations in just minutes.
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

      {/* Footer */}
      <footer className="bg-primary text-primary-foreground py-8 px-6 mt-12">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 md:gap-0">
          <div className="mb-4 md:mb-0 text-center md:text-left">
            <h3 className="text-xl font-bold">Word Wiz AI</h3>
            <p className="text-sm">Read smarter. Grow faster.</p>
          </div>
          <div className="flex flex-wrap justify-center md:justify-start gap-4 text-sm">
            <a href="#about" className="hover:underline">
              About
            </a>
            <a href="#contact" className="hover:underline">
              Contact
            </a>
            <a href="#privacy" className="hover:underline">
              Privacy
            </a>
            <a href="#terms" className="hover:underline">
              Terms
            </a>
            <a href="#educators" className="hover:underline">
              For Educators
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
};

export default LandingPage;
