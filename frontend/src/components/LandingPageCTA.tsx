import { useContext } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { googleLogin } from "@/api";
import { AuthContext } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import { GoogleIcon } from "./GoogleIcon";
import { trackSignupClick } from "@/utils/analytics";
import { PenArrow, PenGroup, PenWords } from "./landing/TeacherPen";
import {
  cardGlow,
  floatingCard,
  penNote,
  sectionTitle,
} from "./landing/styles";

interface LandingPageCTAProps {
  fadeUpVariant: {
    hidden: { opacity: number; y: number };
    visible: { opacity: number; y: number };
  };
}

const LandingPageCTA = ({ fadeUpVariant }: LandingPageCTAProps) => {
  // Signed-in parents get one way back into the app, not more sign-up buttons.
  const signedIn = !!useContext(AuthContext).token;

  return (
    <motion.section
      className="px-4 py-20 sm:px-6 md:py-24"
      variants={fadeUpVariant}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.6 }}
    >
      <div className="relative mx-auto max-w-[900px] p-3 sm:p-6">
        <div aria-hidden="true" className={cardGlow} />
        <PenGroup
          amount={0.6}
          className={cn(
            floatingCard,
            "flex flex-col items-center gap-5 px-5 py-10 text-center sm:px-14 sm:py-16"
          )}
        >
          <h2 className={cn(sectionTitle, "text-balance")}>
            Try one sentence
            <br />
            <span className="text-primary">with your child tonight.</span>
          </h2>
          <p className="max-w-[520px] text-lg text-muted-foreground">
            Sit together, read a few sentences out loud, and see which sounds
            come up.
          </p>

          <div className="relative mt-2 flex w-full flex-col items-center justify-center gap-3 sm:w-auto sm:flex-row">
            {signedIn ? (
              <Button
                asChild
                size="lg"
                className="min-h-[56px] w-full px-8 text-base font-semibold sm:w-auto"
              >
                <Link to="/dashboard">Continue reading</Link>
              </Button>
            ) : (
              <>
                <div
                  aria-hidden="true"
                  className="absolute -top-14 right-[calc(100%+4px)] hidden w-32 flex-col items-end lg:flex"
                >
                  <PenWords
                    as="span"
                    delay={0.4}
                    text="two clicks to start"
                    className={cn(penNote, "text-right -rotate-[4deg]")}
                  />
                  <PenArrow
                    variant="down-right"
                    delay={1.2}
                    className="-mr-1.5 h-11 w-[90px]"
                  />
                </div>
                <Button
                  size="lg"
                  className="min-h-[56px] w-full px-8 text-base font-semibold sm:w-auto"
                  onClick={() => {
                    trackSignupClick("landing_cta", "google");
                    googleLogin();
                  }}
                >
                  <GoogleIcon className="mr-2 h-5 w-5" />
                  Sign in with Google
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="min-h-[56px] w-full px-8 text-base font-semibold sm:w-auto"
                >
                  <Link
                    to="/signup"
                    onClick={() => trackSignupClick("landing_cta", "link")}
                  >
                    Create Account
                  </Link>
                </Button>
              </>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            Free forever · No ads · No card needed
          </p>
        </PenGroup>
      </div>
    </motion.section>
  );
};

export default LandingPageCTA;
