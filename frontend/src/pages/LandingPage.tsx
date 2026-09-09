import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { motion, MotionConfig } from "framer-motion";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import SeoHead from "@/components/SeoHead";
import LandingPageFooter from "@/components/LandingPageFooter";
import LandingPageCTA from "@/components/LandingPageCTA";
import FAQ from "@/components/FAQ";
import React from "react";
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
    <MotionConfig reducedMotion="user">
      <main className="scroll-smooth bg-background text-foreground">
        <SeoHead
          title="Word Wiz AI - Free AI Reading Tutor for Kids | Learn Phonics & Pronunciation"
          description="Help your child learn to read with Word Wiz AI, a 100% free AI-powered reading tutor. Get personalized phonics practice with pronunciation feedback using advanced speech recognition. Perfect for kids ages 5-8."
          canonicalPath="/"
          structuredData={{
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            name: "Word Wiz AI",
            applicationCategory: "EducationalApplication",
            operatingSystem: "Any (web browser)",
            description:
              "A free AI-powered reading tutor that listens to children read aloud and gives phoneme-level pronunciation feedback.",
            url: "https://wordwizai.com/",
            offers: {
              "@type": "Offer",
              price: "0",
              priceCurrency: "USD",
            },
            audience: {
              "@type": "EducationalAudience",
              educationalRole: "student",
              suggestedMinAge: 5,
              suggestedMaxAge: 8,
            },
          }}
        />

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
                      trackSignupClick("hero", "google");
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
                      onClick={() => trackSignupClick("hero", "link")}
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
          className="px-6 py-20 bg-gradient-to-b from-primary/5 to-background"
          variants={fadeUpVariant}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6 }}
        >
          <div className="max-w-6xl mx-auto">
            <div className="max-w-2xl space-y-4">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                What Makes Word Wiz Unique?
              </h2>
              <p className="text-muted-foreground text-lg">
                Most reading apps can tell your child a word was wrong. Word Wiz
                tells them which sound was wrong.
              </p>
            </div>

            <motion.div
              className="mt-12 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
            >
              {/* Lead claim, shown rather than described */}
              <motion.div
                className="lg:col-span-7 rounded-2xl border border-border bg-card p-6 sm:p-8"
                variants={childVariant}
              >
                <h3 className="text-xl font-semibold">
                  Feedback down to a single sound
                </h3>
                <p className="mt-2 text-muted-foreground">
                  Speech recognition breaks each word into its phonemes, so
                  practice targets the exact sound that slipped rather than the
                  whole word.
                </p>

                <div className="mt-7 rounded-xl bg-muted/50 p-5 sm:p-6">
                  <div className="flex flex-wrap items-end gap-2">
                    {[
                      { chunk: "b", sound: "/b/" },
                      { chunk: "r", sound: "/r/" },
                      { chunk: "ow", sound: "/aʊ/", missed: true },
                      { chunk: "n", sound: "/n/" },
                    ].map((part) => (
                      <div key={part.chunk} className="text-center">
                        <div
                          className={
                            part.missed
                              ? "rounded-lg border-2 border-rose-400 bg-rose-400/15 px-3.5 py-2 text-2xl font-semibold text-rose-700 dark:text-rose-300"
                              : "rounded-lg border-2 border-border bg-background px-3.5 py-2 text-2xl font-semibold"
                          }
                        >
                          {part.chunk}
                        </div>
                        <div className="mt-1.5 text-xs text-muted-foreground">
                          {part.sound}
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="mt-5 text-sm text-muted-foreground">
                    Reading{" "}
                    <span className="font-medium text-foreground">brown</span>,
                    your reader said the vowel team as{" "}
                    <span className="font-medium text-foreground">
                      /o&#650;/
                    </span>
                    . The next few sentences quietly work that sound back in.
                  </p>
                </div>
              </motion.div>

              {/* Supporting claims, grouped by a rule instead of boxed in cards */}
              <div className="lg:col-span-5 divide-y divide-border">
                {[
                  {
                    title: "Practice that follows the reader",
                    text: "Sentences are generated around the letter sounds and phonics patterns your child keeps missing, so no two sessions look alike.",
                  },
                  {
                    title: "Free, and staying that way",
                    text: "No ads, no subscription, no card on file. Word Wiz exists to help more children read, which does not work if it costs money.",
                  },
                ].map((item) => (
                  <motion.div
                    key={item.title}
                    className="py-6 first:pt-0 last:pb-0 lg:first:pt-2"
                    variants={childVariant}
                  >
                    <h3 className="text-lg font-semibold">{item.title}</h3>
                    <p className="mt-2 text-muted-foreground">{item.text}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </motion.section>

        {/* Who It's For Section */}
        <motion.section
          className="px-6 py-20 bg-background"
          variants={fadeUpVariant}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6 }}
        >
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Who It&apos;s For
            </h2>

            <motion.dl
              className="mt-10 border-t border-border"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
            >
              {[
                {
                  title: "Young readers, ages 5 to 8",
                  meta: "Kindergarten through 3rd grade",
                  text: "Short sessions that build confidence, with instant pronunciation help the moment a sound goes sideways.",
                },
                {
                  title: "Teachers and reading specialists",
                  meta: "Classroom and small group",
                  text: "Run reading practice alongside your own instruction, then see which phonics patterns a student keeps missing.",
                },
                {
                  title: "Parents and homeschoolers",
                  meta: "At home, no training needed",
                  text: "Sit with your child through a few sentences a day. Word Wiz handles the phonics coaching you may not have been taught yourself.",
                },
              ].map((target) => (
                <motion.div
                  key={target.title}
                  className="grid grid-cols-1 gap-x-10 gap-y-2 border-b border-border py-7 sm:grid-cols-12"
                  variants={childVariant}
                >
                  <dt className="sm:col-span-5">
                    <span className="block text-xl font-semibold">
                      {target.title}
                    </span>
                    <span className="mt-1 block text-sm text-muted-foreground">
                      {target.meta}
                    </span>
                  </dt>
                  <dd className="text-muted-foreground sm:col-span-7">
                    {target.text}
                  </dd>
                </motion.div>
              ))}
            </motion.dl>
          </div>
        </motion.section>

        {/* How It Works */}
        <motion.section
          id="how-it-works-section"
          className="px-6 py-20 bg-gradient-to-b from-background to-primary/5"
          variants={fadeUpVariant}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6 }}
        >
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-center">
              How It Works
            </h2>

            <motion.ol
              className="relative mt-12 grid grid-cols-1 gap-10 md:grid-cols-3 md:gap-8"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
            >
              {[
                {
                  step: "1",
                  title: "Your child reads aloud",
                  text: "A practice sentence appears and Word Wiz listens through the microphone. Nothing is kept for anyone else to hear.",
                },
                {
                  step: "2",
                  title: "Every sound gets checked",
                  text: "The audio is split into phonemes and compared against how the sentence should sound, word by word.",
                },
                {
                  step: "3",
                  title: "Feedback, then a new sentence",
                  text: "Your child hears what to try differently, and the next sentence is built around the sounds that need the practice.",
                },
              ].map((step, i, steps) => (
                <motion.li
                  key={step.step}
                  className="relative flex gap-4 md:block"
                  variants={childVariant}
                >
                  {/* Connector to the next step. Decorative, so the last step has none. */}
                  {i < steps.length - 1 && (
                    <span
                      aria-hidden="true"
                      className="pointer-events-none absolute left-[1.0625rem] top-10 h-[calc(100%+1.25rem-2.5rem)] w-px bg-border md:left-10 md:top-[1.0625rem] md:h-px md:w-[calc(100%-2.5rem+2rem)]"
                    />
                  )}
                  <span className="relative z-10 flex h-9 w-9 flex-none items-center justify-center rounded-full border border-primary/25 bg-primary/10 text-sm font-semibold text-primary">
                    {step.step}
                  </span>
                  <div className="md:mt-5">
                    <h3 className="text-lg font-semibold">{step.title}</h3>
                    <p className="mt-2 text-muted-foreground">{step.text}</p>
                  </div>
                </motion.li>
              ))}
            </motion.ol>
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
    </MotionConfig>
  );
};

export default LandingPage;
