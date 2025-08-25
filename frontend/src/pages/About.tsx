import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { wordWizIcon } from "@/assets";
import { Link } from "react-router-dom";
import { Heart, Users, Target, Github, Twitter, Mail, Linkedin } from "lucide-react";

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

const About = () => {
  return (
    <main className="scroll-smooth bg-background text-foreground">
      {/* Navbar */}
      <nav className="w-full px-4 sm:px-6 py-4 sticky top-0 z-50 bg-background/70 backdrop-blur border-b border-border flex flex-row items-center justify-between gap-3 sm:gap-0">
        <Link className="flex items-center gap-2" to="/">
          <img src={wordWizIcon} alt="Word Wiz Icon" className="h-8 w-8" />
          <span className="text-lg sm:text-xl font-semibold">Word Wiz AI</span>
        </Link>
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

      {/* Hero Section */}
      <motion.section
        className="px-6 py-20 bg-background"
        variants={fadeUpVariant}
        initial="hidden"
        animate="visible"
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <motion.div
            className="w-20 h-20 bg-gradient-to-br from-primary/60 to-purple-300 rounded-2xl flex items-center justify-center shadow-lg mx-auto mb-8"
            whileHover={{ scale: 1.05 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <img src={wordWizIcon} alt="Word Wiz AI" className="w-12 h-12" />
          </motion.div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold">
            About Word Wiz AI
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Empowering young readers to achieve their full potential through
            personalized AI-powered reading assistance.
          </p>
        </div>
      </motion.section>

      {/* Mission Statement Section */}
      <motion.section
        className="px-6 py-20 bg-muted/50"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto space-y-10">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Our Mission</h2>
            <p className="text-muted-foreground max-w-3xl mx-auto">
              We believe every child deserves access to personalized reading
              support that helps them grow into confident, capable readers.
            </p>
          </div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                icon: <Target className="w-6 h-6 text-blue-600" />,
                title: "Personalized Learning",
                text: "Every child learns differently. Our AI adapts to individual reading levels and learning styles to provide targeted support.",
              },
              {
                icon: <Heart className="w-6 h-6 text-red-500" />,
                title: "Completely Free",
                text: "Reading support shouldn't be a privilege. We're committed to providing our platform free of charge to all students and educators.",
              },
              {
                icon: <Users className="w-6 h-6 text-green-600" />,
                title: "Empowering Educators",
                text: "We provide teachers and parents with insights and tools to better support their students' reading journey.",
              },
            ].map((mission, i) => (
              <motion.div key={i} variants={childVariant}>
                <Card className="bg-card p-6 rounded-2xl shadow-md text-center h-full hover:shadow-lg transition-shadow duration-300">
                  <CardHeader className="pb-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-200 to-pink-200 rounded-xl flex items-center justify-center mx-auto mb-4">
                      {mission.icon}
                    </div>
                    <CardTitle className="text-xl font-semibold">
                      {mission.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">{mission.text}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Team Section */}
      <motion.section
        className="px-6 py-20 bg-background"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto space-y-10">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Our Team</h2>
            <p className="text-muted-foreground max-w-3xl mx-auto">
              Word Wiz AI is built by a passionate team of educators, developers,
              and AI researchers dedicated to improving reading outcomes for all children.
            </p>
          </div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                name: "The Word Wiz Team",
                role: "Education & Technology Experts",
                description: "Our diverse team combines expertise in education, artificial intelligence, and child development to create meaningful learning experiences.",
                initials: "WW",
              },
              {
                name: "Passionate Educators",
                role: "Reading Specialists",
                description: "Working with teachers and reading specialists to ensure our platform meets real classroom needs and educational standards.",
                initials: "PE",
              },
              {
                name: "AI Researchers",
                role: "Machine Learning Engineers",
                description: "Developing cutting-edge AI technology that understands how children learn and adapts to their individual needs.",
                initials: "AI",
              },
            ].map((member, i) => (
              <motion.div key={i} variants={childVariant}>
                <Card className="bg-card p-6 rounded-2xl shadow-md text-center h-full hover:shadow-lg transition-shadow duration-300">
                  <CardHeader className="pb-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <span className="text-white font-bold text-lg">
                        {member.initials}
                      </span>
                    </div>
                    <CardTitle className="text-xl font-semibold">
                      {member.name}
                    </CardTitle>
                    <p className="text-sm text-primary font-medium">
                      {member.role}
                    </p>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground text-sm">
                      {member.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Connect With Us Section */}
      <motion.section
        className="px-6 py-20 bg-muted/50"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-4xl mx-auto text-center space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Connect With Us</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Stay updated on our progress, share feedback, or get in touch with
              our team. We'd love to hear from you!
            </p>
          </div>

          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                icon: <Mail className="w-5 h-5" />,
                label: "Email",
                href: "mailto:hello@wordwiz.ai",
                color: "from-blue-400 to-blue-600",
              },
              {
                icon: <Github className="w-5 h-5" />,
                label: "GitHub",
                href: "https://github.com/wordwizai",
                color: "from-gray-600 to-gray-800",
              },
              {
                icon: <Twitter className="w-5 h-5" />,
                label: "Twitter",
                href: "https://twitter.com/wordwizai",
                color: "from-blue-400 to-blue-600",
              },
              {
                icon: <Linkedin className="w-5 h-5" />,
                label: "LinkedIn",
                href: "https://linkedin.com/company/wordwizai",
                color: "from-blue-600 to-blue-800",
              },
            ].map((social, i) => (
              <motion.div key={i} variants={childVariant}>
                <a
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <motion.div
                    className={`p-4 bg-gradient-to-br ${social.color} rounded-2xl text-white shadow-md hover:shadow-lg transition-all duration-300 group`}
                    whileHover={{ scale: 1.05, y: -2 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <div className="flex flex-col items-center gap-2">
                      {social.icon}
                      <span className="text-sm font-medium">{social.label}</span>
                    </div>
                  </motion.div>
                </a>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section
        className="px-6 py-20 bg-background"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold">
            Ready to Start Reading Smarter?
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Join thousands of students already improving their reading skills with Word Wiz AI.
          </p>
          <Link to="/signup">
            <motion.div
              className="inline-block bg-primary text-primary-foreground py-3 px-8 rounded-2xl font-semibold transition-all duration-300 hover:shadow-md"
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              📖 Get Started for Free
            </motion.div>
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
            {[
              { name: "About", path: "/about" },
              { name: "Contact", path: "#" },
              { name: "Privacy", path: "#" },
              { name: "Terms", path: "#" },
              { name: "For Educators", path: "#" },
            ].map((link, index) => (
              <Link
                key={index}
                to={link.path}
                className="hover:underline text-primary-foreground"
                onClick={(e) => {
                  if (link.path === "#") {
                    e.preventDefault();
                    alert("This page is not available yet.");
                  }
                }}
              >
                {link.name}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    </main>
  );
};

export default About;
