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
import { trackSignupClick, trackTryEvent } from "@/utils/analytics";
import { AuthContext } from "@/contexts/AuthContext";
import { ORGANIZATION_ID, ORGANIZATION_SCHEMA } from "@/data/organization";
import LandingSection from "@/components/landing/LandingSection";
import ScrollCue from "@/components/landing/ScrollCue";
import SoundBoxesSection from "@/components/landing/SoundBoxesSection";
import SessionStepsSection from "@/components/landing/SessionStepsSection";
import RecordingSection from "@/components/landing/RecordingSection";
import {
  PenGroup,
  PenMark,
  PenStroke,
} from "@/components/landing/TeacherPen";
import { sectionTitle } from "@/components/landing/styles";
import { PEN_PATHS } from "@/components/landing/penPaths";

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
  // Signed-in parents get one button back into the app instead of sign-up
  // buttons. The prerendered HTML is the signed-out version.
  const signedIn = !!React.useContext(AuthContext).token;

  return (
    <MotionConfig reducedMotion="user">
      <main className="scroll-smooth bg-background text-foreground">
        <SeoHead
          title="Word Wiz AI - Free AI Reading Tutor for Kids | Learn Phonics & Pronunciation"
          description="Help your child learn to read with Word Wiz AI, a 100% free AI-powered reading tutor. Get personalized phonics practice with pronunciation feedback using advanced speech recognition. Perfect for kids ages 5-8."
          canonicalPath="/"
          structuredData={{
            "@context": "https://schema.org",
            "@graph": [
              ORGANIZATION_SCHEMA,
              {
                "@type": "SoftwareApplication",
                name: "Word Wiz AI",
                applicationCategory: "EducationalApplication",
                operatingSystem: "Any (web browser)",
                description:
                  "A free AI-powered reading tutor that listens to children read aloud and gives phoneme-level pronunciation feedback.",
                url: "https://wordwizai.com/",
                publisher: { "@id": ORGANIZATION_ID },
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
              },
            ],
          }}
        />

        {/* Navbar */}
        <LandingPageNavbar />

        {/* Hero Section */}
        <section className="relative px-4 sm:px-6 pt-16 pb-16 sm:pt-20 sm:pb-20 md:pt-24 md:pb-24 lg:pb-10 bg-background text-foreground">
          {/* Content */}
          <div className="relative z-10 max-w-7xl mx-auto">
            <div className="flex flex-col lg:flex-row items-center gap-8 md:gap-12 lg:gap-16">
              {/* Left side - Text and CTAs */}
              <motion.div
                className="flex-1 w-full min-w-0 space-y-6 md:space-y-8 text-center lg:text-left max-w-2xl"
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
                  {signedIn ? (
                    <Button
                      asChild
                      size="lg"
                      className="w-full sm:w-auto min-h-[56px] px-8 text-base font-semibold"
                    >
                      <Link to="/dashboard">Continue reading</Link>
                    </Button>
                  ) : (
                    <>
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
                    </>
                  )}
                </div>

                {/* The no-account demo, for parents who want to see it work
                    before signing up. Nothing on the home page linked to it. */}
                {!signedIn && (
                  <p className="text-sm text-muted-foreground">
                    Not ready to sign up?{" "}
                    <Link
                      to="/try"
                      onClick={() =>
                        trackTryEvent("try_link_click", "at-family", "home_hero")
                      }
                      className="font-semibold text-primary underline-offset-4 hover:underline"
                    >
                      Try three sentences first, no account needed
                    </Link>
                  </p>
                )}

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
            <ScrollCue href="#how-it-hears" />
          </div>
        </section>

        <SoundBoxesSection id="how-it-hears" />

        <SessionStepsSection id="how-it-works-section" />

        {/* Who It's For */}
        <LandingSection className="bg-muted/50 px-4 py-20 sm:px-6 md:py-24">
          <div className="max-w-6xl mx-auto">
            <PenGroup>
              <h2 className={sectionTitle}>
                Who it&rsquo;s{" "}
                <span className="relative inline-block text-primary">
                  for
                  <PenMark
                    viewBox="0 0 100 14"
                    strokeWidth={3.5}
                    className="absolute -bottom-2.5 -left-[8%] h-3.5 w-[120%]"
                  >
                    <PenStroke
                      d={PEN_PATHS.underlineBold}
                      delay={0.3}
                      duration={0.37}
                    />
                  </PenMark>
                </span>
              </h2>
            </PenGroup>

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
        </LandingSection>

        <RecordingSection />

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
