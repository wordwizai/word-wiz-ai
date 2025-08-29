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
              Your Personal Reading Companion
            </h1>
            <p className="text-sm sm:text-base md:text-lg lg:text-xl text-muted-foreground max-w-full sm:max-w-xl mx-auto md:mx-0">
              Word Wiz AI helps kids learn how to read by analyzing thier
              mistakes and generating customized passages tailored to their
              strengths and weaknesses.
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
                alt="Word Wiz AI Demo"
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
                icon: <BarChart3 className="w-6 h-6 text-blue-600" />,
                iconBg: "from-blue-200 to-purple-200",
                title: "Efficient reading practice",
                text: "Get customized practice sentences based on specific struggle areas.",
              },
              {
                icon: <WholeWord className="w-6 h-6 text-rose-500" />,
                iconBg: "from-rose-200 to-pink-200",
                title: "Improve Pronunciation",
                text: "Receive tailored pronunciation tips to enhance fluency.",
              },
              {
                icon: <CircleDollarSign className="w-6 h-6 text-green-600" />,
                iconBg: "from-green-200 to-blue-200",
                title: "Completely Free",
                text: "No ads, no subscriptions. Our mission is to help kids across the country read better for free",
              },
            ].map((feature, i) => (
              <motion.div
                key={i}
                className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl text-center h-full hover:shadow-2xl hover:-translate-y-2 hover:scale-105 transition-all duration-300 rounded-3xl p-6"
                variants={childVariant}
                whileHover={{ scale: 1.05, y: -4 }}
                transition={{ type: "spring", stiffness: 300 }}
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
                title: "Young Readers",
                text: "Boost reading confidence with personalized practice and feedback.",
              },
              {
                icon: <GraduationCap className="w-6 h-6 text-blue-600" />,
                iconBg: "from-blue-200 to-cyan-200",
                title: "Educators",
                text: "Integrate AI powered reading practice into your classroom reading programs.",
              },
              {
                icon: <User className="w-6 h-6 text-green-600" />,
                iconBg: "from-green-200 to-emerald-200",
                title: "Parents",
                text: "Empower your kids with personalized reading practice.",
              },
            ].map((target, i) => (
              <motion.div
                key={i}
                className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl text-center h-full hover:shadow-2xl hover:-translate-y-2 hover:scale-105 transition-all duration-300 rounded-3xl p-6"
                variants={childVariant}
                whileHover={{ scale: 1.05, y: -4 }}
                transition={{ type: "spring", stiffness: 300 }}
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
                text: "Practice reading passages aloud and let Word Wiz listen.",
                gradient: "from-blue-400 to-purple-500",
              },
              {
                step: "2",
                title: "AI Analysis",
                text: "We highlight misread words and analyze what sounds and types of words you misread or stuggle on the most",
                gradient: "from-purple-400 to-pink-500",
              },
              {
                step: "3",
                title: "Personal Feedback",
                text: "You get feedback, guidance, and customized practice sentences to target areas where you struggle. Vocalized through text to speech technology",
                gradient: "from-green-400 to-blue-500",
              },
            ].map((step, i) => (
              <motion.div 
                key={i} 
                variants={childVariant} 
                className="h-full"
                whileHover={{ scale: 1.05, y: -4 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Card className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl hover:shadow-2xl hover:-translate-y-2 hover:scale-105 transition-all duration-300 rounded-3xl h-full p-6">
                  <CardHeader>
                    <div className={`bg-gradient-to-br ${step.gradient} text-white w-12 h-12 flex items-center justify-center rounded-full mb-4 shadow-lg font-bold text-lg`}>
                      {step.step}
                    </div>
                    <CardTitle className="text-xl font-semibold">{step.title}</CardTitle>
                    <CardDescription className="text-muted-foreground">{step.text}</CardDescription>
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
      </motion.section>*}

      {/* CTA button */}
      <LandingPageCTA fadeUpVariant={fadeUpVariant} />
      {/* Footer */}
      <LandingPageFooter />
    </main>
  );
};

export default LandingPage;
