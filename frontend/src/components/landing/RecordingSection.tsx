import { Link } from "react-router-dom";
import LandingSection from "./LandingSection";
import { PEN_PATHS } from "./penPaths";
import { PenGroup, PenMark, PenNumeral, PenStroke } from "./TeacherPen";

// Keep in step with the privacy policy and the FAQ's data answer.
const STEPS = [
  {
    title: "Recorded only while reading",
    text: "The microphone runs while your child reads a sentence, and stops.",
  },
  {
    title: "Scored on our own server",
    text: "OpenAI writes the feedback from the scores as text. It never hears your child.",
  },
  {
    title: "Then thrown away",
    text: "We keep scores and which sounds were hard. No ads, and nothing is sold.",
    circled: true,
  },
];

/** What happens to a child's recording, in three plain steps. */
const RecordingSection = () => (
  <LandingSection className="px-4 py-16 sm:px-6 md:py-20">
    <PenGroup className="mx-auto max-w-6xl space-y-9 rounded-3xl border border-border bg-card p-7 shadow-sm sm:p-12">
      <div className="flex flex-wrap items-end justify-between gap-x-12 gap-y-4">
        <div className="max-w-xl space-y-2.5">
          <h2 className="text-2xl font-bold leading-tight tracking-tight md:text-[34px]">
            What happens to the recording
          </h2>
          <p className="text-[17px] text-muted-foreground">
            It&rsquo;s used to check the reading, then it&rsquo;s gone.
          </p>
        </div>
        <Link
          to="/privacy"
          className="inline-flex min-h-11 items-center text-[15px] font-semibold text-primary underline-offset-4 hover:underline"
        >
          Read the privacy policy
        </Link>
      </div>
      <ol className="grid grid-cols-1 gap-x-10 gap-y-7 md:grid-cols-3">
        {STEPS.map((step, i) => (
          <li key={step.title} className="flex items-start gap-3.5">
            <PenNumeral
              digit={String(i + 1) as "1" | "2" | "3"}
              delay={0.1 + i * 0.2}
              strokeWidth={4}
              className="mt-0.5 h-9 w-6 flex-none"
            />
            <div className="space-y-2.5">
              <h3 className="text-lg font-semibold">
                {step.circled ? (
                  <span className="relative inline-block">
                    {step.title}
                    <PenMark
                      viewBox="0 0 200 56"
                      strokeWidth={2.5}
                      className="absolute -left-[9%] -top-[30%] h-[160%] w-[118%]"
                    >
                      <PenStroke
                        d={PEN_PATHS.loopWide}
                        delay={0.8}
                        duration={0.9}
                      />
                    </PenMark>
                  </span>
                ) : (
                  step.title
                )}
              </h3>
              <p className="text-[15px] text-muted-foreground">{step.text}</p>
            </div>
          </li>
        ))}
      </ol>
    </PenGroup>
  </LandingSection>
);

export default RecordingSection;
