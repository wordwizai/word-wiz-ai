import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { wordWizIcon } from "@/assets";
import React from "react";
import {
  Heart,
  Users,
  Target,
  Github,
  Twitter,
  Mail,
  Instagram,
  DollarSign,
} from "lucide-react";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";
import LandingPageCTA from "@/components/LandingPageCTA";

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
  // Add structured data for SEO
  React.useEffect(() => {
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "AboutPage",
      mainEntity: {
        "@type": "Organization",
        name: "Word Wiz AI",
        description:
          "Free AI-powered reading tutor helping children learn to read with phoneme-level pronunciation feedback",
        url: "https://wordwizai.com",
        sameAs: [
          "https://instagram.com/wordwizai",
          "https://github.com/wordwizai",
        ],
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
      <motion.section
        className="px-6 py-20 bg-gradient-to-br from-background to-purple-50/50"
        variants={fadeUpVariant}
        initial="hidden"
        animate="visible"
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <motion.div
            className="w-24 h-24 bg-gradient-to-br from-primary/60 to-purple-300 rounded-3xl flex items-center justify-center shadow-2xl mx-auto mb-8"
            whileHover={{ scale: 1.05, rotate: 5 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <img src={wordWizIcon} alt="Word Wiz AI" className="w-14 h-14" />
          </motion.div>
          <motion.h1
            className="text-4xl sm:text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            About Word Wiz AI
          </motion.h1>
          <motion.p
            className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
            Empowering young readers through AI-powered phonics instruction and
            pronunciation feedback.
          </motion.p>
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
              Every child deserves access to personalized reading support that
              helps them become confident readers.
            </p>
          </div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6 }}
          >
            {[
              {
                icon: <Target className="w-6 h-6 text-blue-600" />,
                iconBg: "from-blue-200 to-purple-200",
                title: "Personalized Learning",
                text: "Our AI adapts to individual reading levels and learning styles to provide targeted support.",
              },
              {
                icon: <DollarSign className="w-6 h-6 text-red-500" />,
                iconBg: "from-red-200 to-pink-200",
                title: "Completely Free",
                text: "Quality reading support for all students and educators, with no cost or subscriptions.",
              },
              {
                icon: <Users className="w-6 h-6 text-green-600" />,
                iconBg: "from-green-200 to-blue-200",
                title: "Empowering Educators",
                text: "Tools and insights to help teachers and parents support their students' reading journey.",
              },
            ].map((mission, i) => (
              <div key={i}>
                <Card className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl text-center h-full hover:shadow-2xl transition-shadow rounded-3xl">
                  <CardHeader className="pb-4">
                    <div
                      className={`w-12 h-12 bg-gradient-to-r ${mission.iconBg} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg`}
                    >
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
              </div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Team Section */}
      {/*}<motion.section
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
              Word Wiz AI is built by a passionate team of educators,
              developers, and AI researchers dedicated to improving reading
              outcomes for all children.
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
                description:
                  "Our diverse team combines expertise in education, artificial intelligence, and child development to create meaningful learning experiences.",
                initials: "WW",
                gradient: "from-blue-400 to-purple-500",
              },
              {
                name: "Passionate Educators",
                role: "Reading Specialists",
                description:
                  "Working with teachers and reading specialists to ensure our platform meets real classroom needs and educational standards.",
                initials: "PE",
                gradient: "from-green-400 to-blue-500",
              },
              {
                name: "AI Researchers",
                role: "Machine Learning Engineers",
                description:
                  "Developing cutting-edge AI technology that understands how children learn and adapts to their individual needs.",
                initials: "AI",
                gradient: "from-purple-400 to-pink-500",
              },
            ].map((member, i) => (
              <motion.div key={i} variants={childVariant}>
                <Card className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl text-center h-full hover:shadow-2xl transition-shadow rounded-3xl">
                  <CardHeader className="pb-4">
                    <div className={`w-16 h-16 bg-gradient-to-br ${member.gradient} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
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
      </motion.section>*/}

      {/* Connect With Us Section */}
      <motion.section
        className="px-6 py-20 bg-muted/50"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-3xl mx-auto text-center space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Connect With Us</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Share feedback or get in touch with our team. We'd love to hear
              from you!
            </p>
          </div>

          <motion.div
            className="grid grid-cols-3 gap-4"
            id="contact"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6 }}
          >
            {[
              {
                icon: <Instagram className="w-6 h-6" />,
                label: "Instagram",
                href: "https://instagram.com/wordwizai",
                color: "from-pink-400 to-purple-600",
              },
              {
                icon: <Github className="w-6 h-6" />,
                label: "GitHub",
                href: "https://github.com/wordwizai",
                color: "from-gray-600 to-gray-800",
              },
              {
                icon: <Mail className="w-6 h-6" />,
                label: "Email",
                href: "mailto:contact@wordwizai.com",
                color: "from-blue-400 to-cyan-600",
              },
            ].map((social, i) => (
              <div key={i}>
                <a
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <motion.div
                    className={`p-6 bg-gradient-to-br ${social.color} rounded-2xl text-white shadow-xl hover:shadow-2xl transition-shadow group`}
                    whileHover={{ scale: 1.05, y: -4 }}
                    whileTap={{ scale: 0.95 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <div className="flex flex-col items-center gap-3">
                      <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
                        {social.icon}
                      </div>
                      <span className="text-sm font-semibold">
                        {social.label}
                      </span>
                    </div>
                  </motion.div>
                </a>
              </div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <LandingPageCTA fadeUpVariant={fadeUpVariant} />

      {/* Footer */}
      <LandingPageFooter />
    </main>
  );
};

export default About;
