import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { demoScreenshot } from "@/assets";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";
import LandingPageCTA from "@/components/LandingPageCTA";
import FAQ from "@/components/FAQ";
import React from "react";
import {
  BookOpen,
  Search,
  BarChart3,
  PenTool,
  DollarSign,
  Users,
  GraduationCap,
  User,
  Speech,
  WholeWord,
  CircleDollarSign,
} from "lucide-react";

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
      "name": "Word Wiz AI",
      "applicationCategory": "EducationalApplication",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      },
      "description": "AI-powered reading tutor that helps children learn to read with personalized phonics practice and pronunciation feedback",
      "operatingSystem": "Web Browser",
      "url": "https://wordwizai.com",
      "author": {
        "@type": "Organization",
        "name": "Word Wiz AI",
        "url": "https://wordwizai.com"
      }
    };

    const script = document.createElement('script');
    script.type = 'application/ld+json';
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
              Free AI Reading Tutor - Help Kids Learn to Read with Phonics
            </h1>
            <p className="text-sm sm:text-base md:text-lg lg:text-xl text-muted-foreground max-w-full sm:max-w-xl mx-auto md:mx-0">
              Word Wiz AI helps children ages 5-8 learn to read through AI-powered pronunciation feedback and personalized phonics practice. 100% free, no ads, no subscriptions.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center md:justify-start">
              <Link to="/signup" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  className="w-full sm:w-auto min-h-[48px] flex items-center gap-2"
                  as={motion.button}
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <BookOpen className="w-5 h-5" />
                  Create an Account
                </Button>
              </Link>
              <a href="#how-it-works-section" className="w-full sm:w-auto">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full sm:w-auto min-h-[48px] flex items-center gap-2"
                  as={motion.button}
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Search className="w-5 h-5" />
                  How It Works
                </Button>
              </a>
            </div>
          </div>
          <div className="flex-1 max-w-full">
            <div className="border border-border rounded-2xl aspect-[4/3] flex items-center justify-center max-w-full bg-background">
              <img
                src={demoScreenshot}
                alt="Word Wiz AI reading practice interface showing real-time phoneme-level pronunciation feedback for children learning to read"
                className="w-full h-full object-cover rounded-2xl p-2 bg-background m-2"
              />
            </div>
          </div>
        </div>
      </motion.section>

      {/* What Makes Word Wiz Unique */}
      <motion.section
        className="px-6 py-20 bg-gradient-to-br from-background to-purple-50/50"
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
              Powered by GPT-4 and advanced speech recognition technology. Trusted by parents and teachers nationwide.
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
                className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl text-center h-full hover:shadow-2xl transition-shadow rounded-3xl p-6"
                variants={childVariant}
              >
                <div
                  className={`w-12 h-12 bg-gradient-to-r ${feature.iconBg} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg`}
                >
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
                className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl text-center h-full hover:shadow-2xl transition-shadow rounded-3xl p-6"
                variants={childVariant}
              >
                <div
                  className={`w-12 h-12 bg-gradient-to-r ${target.iconBg} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg`}
                >
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
        className="px-6 py-20 bg-gradient-to-br from-background to-purple-50/50"
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
                gradient: "from-blue-400 to-purple-500",
              },
              {
                step: "2",
                title: "AI Pronunciation Analysis",
                text: "Our AI analyzes every phoneme (individual sound) to identify which letter sounds and word patterns need more practice.",
                gradient: "from-purple-400 to-pink-500",
              },
              {
                step: "3",
                title: "Personalized Phonics Feedback",
                text: "Get instant feedback with pronunciation tips and customized practice sentences targeting specific phonics skills. Guidance is provided through text-to-speech audio.",
                gradient: "from-green-400 to-blue-500",
              },
            ].map((step, i) => (
              <motion.div key={i} variants={childVariant} className="h-full">
                <Card className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl hover:shadow-2xl transition-shadow rounded-3xl h-full p-6">
                  <CardHeader>
                    <div
                      className={`bg-gradient-to-br ${step.gradient} text-white w-12 h-12 flex items-center justify-center rounded-full mb-4 shadow-lg font-bold text-lg`}
                    >
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
