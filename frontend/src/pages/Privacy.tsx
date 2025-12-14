import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { wordWizIcon } from "@/assets";
import React from "react";
import { Shield } from "lucide-react";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";
import LandingPageCTA from "@/components/LandingPageCTA";

const fadeUpVariant = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const Privacy = () => {
  // Add structured data for SEO
  React.useEffect(() => {
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "WebPage",
      name: "Privacy Policy",
      description:
        "Word Wiz AI Privacy Policy - Learn how we protect user privacy and personal information",
      url: "https://wordwizai.com/privacy",
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
        className="px-6 py-4 bg-gradient-to-br from-background to-purple-50/50"
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
            <Shield className="w-14 h-14 text-white" />
          </motion.div>
          <motion.h1
            className="text-4xl sm:text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            Privacy Policy
          </motion.h1>
          <motion.p
            className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
            Your privacy and security are our top priorities
          </motion.p>
        </div>
      </motion.section>

      {/* Privacy Content Section */}
      <section className="px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card className="shadow-lg border-2">
              <CardContent className="p-4 md:p-6">
                <div className="prose prose-lg max-w-none">
                  <p className="text-foreground leading-relaxed">
                    Word Wiz AI respects user privacy and is committed to
                    protecting personal information. The product collects only
                    the information necessary to provide phonics practice and
                    pronunciation feedback.
                  </p>

                  <br />
                  <p className="text-foreground leading-relaxed">
                    Word Wiz AI does not sell user or student data and does not
                    use data for advertising purposes. Any data collected is
                    stored securely and accessed only as needed to operate the
                    service.
                  </p>

                  <br />
                  <p className="text-foreground leading-relaxed">
                    If Word Wiz AI experiences a data security incident,
                    reasonable steps will be taken to address the issue in
                    accordance with applicable laws.
                  </p>
                  <br />

                  <p className="text-foreground leading-relaxed">
                    For questions about privacy, please contact:{" "}
                    <a
                      href="mailto:contact@wordwizai.com"
                      className="text-primary hover:underline font-medium"
                    >
                      contact@wordwizai.com
                    </a>
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>
      {/* Footer */}
      <LandingPageFooter />
    </main>
  );
};

export default Privacy;
