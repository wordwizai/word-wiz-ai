import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";
import LandingPageCTA from "@/components/LandingPageCTA";
import FAQ from "@/components/FAQ";
import React from "react";
import {
  BookOpen,
  BarChart3,
  Users,
  GraduationCap,
  User,
  WholeWord,
  CircleDollarSign,
  Sparkles,
} from "lucide-react";
import AnimatedPracticeDemo from "@/components/AnimatedPracticeDemo";
import TrustBadgeCarousel from "@/components/TrustBadgeCarousel";
import { googleLogin } from "@/api";
import { GoogleIcon } from "@/components/GoogleIcon";
import { trackSignupClick } from "@/utils/analytics";

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
  // Add structured data for SEO
  React.useEffect(() => {
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "WebApplication",
      name: "Word Wiz AI",
      applicationCategory: "EducationalApplication",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
      },
      description:
        "AI-powered reading tutor that helps children learn to read with personalized phonics practice and pronunciation feedback",
      operatingSystem: "Web Browser",
      url: "https://wordwizai.com",
      author: {
        "@type": "Organization",
        name: "Word Wiz AI",
        url: "https://wordwizai.com",
      },
    };

    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.text = JSON.stringify(structuredData);
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  return (
    <main className="scroll-smooth bg-background text-foreground">
      {/* Navbar */}
      <LandingPageNavbar />

      {/* Hero Section */}
      <section className="relative px-4 sm:px-6 py-16 sm:py-20 md:py-24 bg-background text-foreground">
        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row items-center gap-8 md:gap-12 lg:gap-16">
            {/* Left side - Text and CTAs */}
            <motion.div
              className="flex-1 space-y-6 md:space-y-8 text-center lg:text-left max-w-2xl"
              variants={fadeUpVariant}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6 }}
            >
              <div className="space-y-4">
                <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight">
                  Your AI Reading Tutor
                  <br />
                  <span className="text-primary">100% Free Forever</span>
                </h1>
                <p className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-xl mx-auto lg:mx-0">
                  Help children ages 5-8 learn to read through AI-powered
                  pronunciation feedback and personalized phonics practice.
                </p>
              </div>

              {/* Trust badges carousel */}
              <TrustBadgeCarousel />

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start items-center">
                {/* Primary CTA - Google Sign In */}
                <Button
                  size="lg"
                  className="w-full sm:w-auto min-h-[56px] px-8 text-base font-semibold"
                  onClick={() => {
                    trackSignupClick('hero', 'google');
                    googleLogin();
                  }}
                >
                  <GoogleIcon className="w-5 h-5 mr-2" />
                  Sign in with Google
                </Button>

                {/* Secondary CTA */}
                <Link to="/signup" className="w-full sm:w-auto">
                  <Button
                    variant="outline"
                    size="lg"
                    className="w-full sm:w-auto min-h-[56px] px-8 text-base font-semibold"
                    onClick={() => trackSignupClick('hero', 'link')}
                  >
                    Create Account
                  </Button>
                </Link>
              </div>

              {/* Social proof */}
              <p className="text-sm text-muted-foreground">
                Join us in our mission of improving reading skills with AI
              </p>
            </motion.div>

            {/* Right side - Animated Demo */}
            <motion.div
              className="flex-1 w-full max-w-2xl"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <div className="aspect-[4/3] w-full">
                <AnimatedPracticeDemo />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* What Makes Word Wiz Unique */}
      <motion.section
        className="px-6 py-20 bg-muted/30"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto text-center space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">
              What Makes Word Wiz Unique?
            </h2>
            <p className="text-muted-foreground text-lg max-w-3xl mx-auto">
              Powered by GPT-4 and advanced speech recognition technology, and
              backed by real AI research.
            </p>
          </div>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                icon: <BarChart3 className="w-6 h-6 text-blue-600" />,
                iconBg: "from-blue-200 to-purple-200",
                title: "Personalized Reading Practice",
                text: "Get customized practice sentences targeting specific phonics patterns and letter sounds your child struggles with.",
              },
              {
                icon: <WholeWord className="w-6 h-6 text-rose-500" />,
                iconBg: "from-rose-200 to-pink-200",
                title: "Phoneme-Level Pronunciation Feedback",
                text: "Advanced speech recognition identifies exact sounds misread, more precise than whole-word feedback.",
              },
              {
                icon: <CircleDollarSign className="w-6 h-6 text-green-600" />,
                iconBg: "from-green-200 to-blue-200",
                title: "100% Free Forever",
                text: "No ads, no subscriptions, no hidden fees. Our mission is helping every child learn to read better.",
              },
            ].map((feature, i) => (
              <motion.div
                key={i}
                className="bg-card border text-card-foreground shadow-sm text-center h-full hover:shadow-md transition-shadow rounded-lg p-6"
                variants={childVariant}
              >
                <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.text}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Who It's For Section */}
      <motion.section
        className="px-6 py-20 bg-muted/50"
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
                icon: <Users className="w-6 h-6 text-orange-600" />,
                iconBg: "from-orange-200 to-yellow-200",
                title: "Young Readers (Ages 5-8)",
                text: "Perfect for Kindergarten through 3rd grade. Build reading confidence with personalized phonics practice and instant feedback.",
              },
              {
                icon: <GraduationCap className="w-6 h-6 text-blue-600" />,
                iconBg: "from-blue-200 to-cyan-200",
                title: "Teachers & Educators",
                text: "Integrate AI-powered reading practice into your classroom. Track student progress and target intervention areas.",
              },
              {
                icon: <User className="w-6 h-6 text-green-600" />,
                iconBg: "from-green-200 to-emerald-200",
                title: "Parents & Homeschoolers",
                text: "Support your child's reading journey at home with phonics instruction and pronunciation coaching.",
              },
            ].map((target, i) => (
              <motion.div
                key={i}
                className="bg-card border text-card-foreground shadow-sm text-center h-full hover:shadow-md transition-shadow rounded-lg p-6"
                variants={childVariant}
              >
                <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  {target.icon}
                </div>
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
        className="px-6 py-20 bg-background"
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
                text: "Your child reads practice sentences aloud while Word Wiz AI listens using advanced speech recognition technology.",
              },
              {
                step: "2",
                title: "AI Pronunciation Analysis",
                text: "Our AI analyzes every phoneme (individual sound) to identify which letter sounds and word patterns need more practice.",
              },
              {
                step: "3",
                title: "Personalized Phonics Feedback",
                text: "Get instant feedback with pronunciation tips and customized practice sentences targeting specific phonics skills. Guidance is provided through text-to-speech audio.",
              },
            ].map((step, i) => (
              <motion.div key={i} variants={childVariant} className="h-full">
                <Card className="bg-card border shadow-sm hover:shadow-md transition-shadow h-full">
                  <CardHeader>
                    <div className="bg-primary text-primary-foreground w-12 h-12 flex items-center justify-center rounded-lg mb-4 font-bold text-lg">
                      {step.step}
                    </div>
                    <CardTitle className="text-xl font-semibold">
                      {step.title}
                    </CardTitle>
                    <CardDescription className="text-muted-foreground">
                      {step.text}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Testimonials Section */}
      {/*<motion.section
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

      {/* FAQ Section */}
      <FAQ />

      {/* CTA button */}
      <LandingPageCTA fadeUpVariant={fadeUpVariant} />
      {/* Footer */}
      <LandingPageFooter />
    </main>
  );
};

export default LandingPage;
