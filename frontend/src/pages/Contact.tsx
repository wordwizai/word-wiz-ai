import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Heart,
  MapPin,
  Mail,
  Github,
  Twitter,
  Instagram,
  Send,
  MessageCircle,
} from "lucide-react";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";
import LandingPageCTA from "@/components/LandingPageCTA";
import React from "react";

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

const Contact = () => {
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [subject, setSubject] = React.useState("");
  const [message, setMessage] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    alert(
      "This system is not yet implemented. Please feel free to reach out to us via email. We look forward to hearing form you!"
    );
    // setLoading(true);
    //
    // // Simulate form submission
    // await new Promise((resolve) => setTimeout(resolve, 1000));
    //
    // setSubmitted(true);
    // setLoading(false);
    //
    // // Reset form after 3 seconds
    // setTimeout(() => {
    //   setSubmitted(false);
    //   setName("");
    //   setEmail("");
    //   setSubject("");
    //   setMessage("");
    // }, 3000);
  };

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
            <MessageCircle className="w-14 h-14 text-white" />
          </motion.div>
          <motion.h1
            className="text-4xl sm:text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            Contact Us
          </motion.h1>
          <motion.p
            className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
            Have questions or feedback? We'd love to hear from you! Reach out to
            our team and we'll get back to you as soon as possible.
          </motion.p>
        </div>
      </motion.section>

      {/* Contact Form & Info Section */}
      <motion.section
        className="px-6 py-20 bg-muted/50"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Contact Form */}
            <motion.div
              variants={childVariant}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              <Card className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl rounded-3xl">
                <CardHeader>
                  <CardTitle className="text-2xl font-bold flex items-center gap-2">
                    <Send className="w-6 h-6 text-primary" />
                    Send us a Message
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {submitted ? (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="text-center py-8 space-y-4"
                    >
                      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                        <Heart className="w-8 h-8 text-green-600" />
                      </div>
                      <h3 className="text-xl font-semibold text-green-700">
                        Message Sent!
                      </h3>
                      <p className="text-muted-foreground">
                        Thank you for reaching out. We'll get back to you soon!
                      </p>
                    </motion.div>
                  ) : (
                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Name</Label>
                          <Input
                            id="name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Your full name"
                            required
                            className="rounded-xl"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="email">Email</Label>
                          <Input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your.email@example.com"
                            required
                            className="rounded-xl"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="subject">Subject</Label>
                        <Input
                          id="subject"
                          value={subject}
                          onChange={(e) => setSubject(e.target.value)}
                          placeholder="What's this about?"
                          required
                          className="rounded-xl"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="message">Message</Label>
                        <textarea
                          id="message"
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          placeholder="Tell us more about your question or feedback..."
                          required
                          rows={6}
                          className="w-full px-3 py-2 border border-input bg-background rounded-xl text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                        />
                      </div>
                      <Button
                        type="submit"
                        disabled={loading}
                        className="w-full rounded-xl py-3 text-base font-semibold"
                        size="lg"
                      >
                        {loading ? "Sending..." : "Send Message"}
                      </Button>
                    </form>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Contact Information */}
            <motion.div
              variants={childVariant}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="space-y-8"
            >
              <div>
                <h2 className="text-3xl font-bold mb-6">Get in Touch</h2>
                <p className="text-muted-foreground text-lg leading-relaxed">
                  Whether you're a teacher looking for reading support tools, a
                  parent wanting to help your child, or a fellow educator with
                  ideas, we're here to listen and help.
                </p>
              </div>

              <div className="space-y-6">
                {[
                  {
                    icon: <Mail className="w-6 h-6" />,
                    title: "Email",
                    content: "contact@wordwizai.com",
                    action: "mailto:contact@wordwizai.com",
                    color: "from-blue-400 to-cyan-600",
                  },
                ].map((item, i) => (
                  <motion.div key={i} variants={childVariant}>
                    <Card className="bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl">
                      <CardContent className="p-6">
                        <div className="flex items-start gap-4">
                          <div
                            className={`p-3 bg-gradient-to-br ${item.color} rounded-xl text-white shadow-lg`}
                          >
                            {item.icon}
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg">
                              {item.title}
                            </h3>
                            {item.action ? (
                              <a
                                href={item.action}
                                className="text-muted-foreground hover:text-primary transition-colors"
                              >
                                {item.content}
                              </a>
                            ) : (
                              <p className="text-muted-foreground">
                                {item.content}
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Social Media Section */}
      <motion.section
        className="px-6 py-20 bg-background"
        variants={fadeUpVariant}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-4xl mx-auto text-center space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">
              Follow Our Journey
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Stay connected with Word Wiz AI on social media for updates,
              educational tips, and community highlights.
            </p>
          </div>

          <motion.div
            className="grid grid-cols-2 gap-6 max-w-2xl mx-auto"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            {[
              {
                icon: <Instagram className="w-8 h-8" />,
                label: "Instagram",
                href: "https://instagram.com/wordwizai",
                color: "from-pink-400 to-purple-600",
                description: "Educational tips & updates",
              },
              {
                icon: <Github className="w-8 h-8" />,
                label: "GitHub",
                href: "https://github.com/wordwizai",
                color: "from-gray-600 to-gray-800",
                description: "Open source contributions",
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
                    className={`p-6 bg-gradient-to-br ${social.color} rounded-3xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 group h-full`}
                    whileHover={{ scale: 1.05, y: -6 }}
                    whileTap={{ scale: 0.95 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <div className="flex flex-col items-center gap-4 text-center">
                      <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-sm">
                        {social.icon}
                      </div>
                      <div>
                        <h3 className="text-lg font-bold mb-1">
                          {social.label}
                        </h3>
                        <p className="text-xs opacity-90">
                          {social.description}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                </a>
              </motion.div>
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

export default Contact;
