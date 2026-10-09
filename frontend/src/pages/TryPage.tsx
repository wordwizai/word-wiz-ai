import { useContext, useEffect, useRef, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link, Navigate, useParams } from "react-router-dom";
import { Mic, Volume2, ShieldCheck } from "lucide-react";
import PracticeStage from "@/components/practice/PracticeStage";
import type { PronunciationAnalysis } from "@/components/practice/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { wordWizIcon } from "@/assets";
import { AuthContext } from "@/contexts/AuthContext";
import { getPatternBySlug, type PhonicsPattern } from "@/data/phonicsPatterns";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useFeedbackAudio } from "@/hooks/useFeedbackAudio";
import { b64toBlob, type AudioAnalysisEvent } from "@/services/audioTransport";
import { analyzeGuestAudio, GuestAnalysisError } from "@/services/guestAnalysis";
import { getGuestId } from "@/services/guestId";
import { showPracticeErrorToast } from "@/utils/errorHandling";
import { trackSignupClick, trackTryEvent } from "@/utils/analytics";

// /try and /try/:slug let a visitor's child read a few practice sentences out
// loud and get real sound-level feedback before making an account. The
// backend route (routers/guest.py) scores the recording and drops it. The only
// thing kept is one anonymous guest user per browser, so try-mode visitors are
// counted (services/guestId.ts). Kept out of search results (noindex, not
// prerendered); the guide and practice-word pages are the pages meant to rank.

const DEFAULT_SLUG = "at-family";
const SENTENCES_PER_TRY = 3;

type Ending = "finished" | "limit" | "unavailable";

const TryPage = () => {
  const { slug } = useParams();
  const pattern = getPatternBySlug(slug ?? DEFAULT_SLUG);
  if (!pattern) return <Navigate to="/try" replace />;
  return <TrySession key={pattern.slug} pattern={pattern} />;
};

const TrySession = ({ pattern }: { pattern: PhonicsPattern }) => {
  const sentences = pattern.sampleSentences.slice(0, SENTENCES_PER_TRY);
  const [started, setStarted] = useState(false);
  const [index, setIndex] = useState(0);
  const [analysisData, setAnalysisData] = useState<PronunciationAnalysis | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showNext, setShowNext] = useState(false);
  const [ending, setEnding] = useState<Ending | null>(null);
  const feedbackAudio = useFeedbackAudio();
  const { token } = useContext(AuthContext);
  const abortRef = useRef<AbortController | null>(null);
  const nextTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const sentence = sentences[index];

  useEffect(
    () => () => {
      abortRef.current?.abort();
      if (nextTimer.current) clearTimeout(nextTimer.current);
    },
    []
  );

  const handleEvent = (event: AudioAnalysisEvent) => {
    switch (event.type) {
      case "processing_started":
        setIsProcessing(true);
        break;
      case "analysis":
        setIsProcessing(false);
        setShowHighlightedWords(true);
        setAnalysisData(event.data);
        break;
      case "feedback":
        setFeedback(event.data.text);
        // Same pause signed-in practice leaves before offering the arrow, so
        // the spoken feedback gets a moment before the next sentence.
        nextTimer.current = setTimeout(() => setShowNext(true), 1000);
        break;
      case "audio_feedback_file":
        if (event.data && event.mimetype) {
          feedbackAudio.play(URL.createObjectURL(b64toBlob(event.data, event.mimetype)));
        }
        break;
      case "complete":
        setShowNext(true);
        break;
      case "error":
        setIsProcessing(false);
        showPracticeErrorToast(event.data?.message ?? "Please try that sentence again.");
        break;
    }
  };

  const send = async (file: File) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setIsProcessing(true);
    // Old feedback belongs to the last attempt. PracticeStage pairs the next
    // analysis with whatever feedback is set, so it has to go first.
    setFeedback(null);
    trackTryEvent("try_attempt", pattern.slug, "try_page");
    try {
      // Signed-in visitors already have an account, so don't count them again.
      const guestId = token ? undefined : getGuestId();
      await analyzeGuestAudio(file, sentence, handleEvent, controller.signal, guestId);
    } catch (err) {
      if ((err as Error)?.name === "AbortError") return;
      setIsProcessing(false);
      if (err instanceof GuestAnalysisError && err.status === 429) {
        setEnding("limit");
      } else if (err instanceof GuestAnalysisError && err.status === 404) {
        setEnding("unavailable");
      } else {
        showPracticeErrorToast((err as Error)?.message ?? "Please try that sentence again.");
      }
    }
  };

  const { isRecording, startRecording, stopRecording, levelRef } = useAudioRecorder(send);

  const goNext = () => {
    if (nextTimer.current) clearTimeout(nextTimer.current);
    feedbackAudio.reset();
    setAnalysisData(null);
    setFeedback(null);
    setShowHighlightedWords(false);
    setShowNext(false);
    if (index + 1 < sentences.length) {
      setIndex(index + 1);
    } else {
      trackTryEvent("try_completed", pattern.slug, "try_page");
      setEnding("finished");
    }
  };

  const restart = () => {
    setIndex(0);
    setEnding(null);
  };

  return (
    <>
      <Helmet>
        <title>{`Try Word Wiz AI: ${pattern.displayName} Out Loud`}</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      {ending ? (
        <TryEnding ending={ending} pattern={pattern} onRestart={restart} />
      ) : !started ? (
        <TryIntro pattern={pattern} count={sentences.length} onStart={() => setStarted(true)} />
      ) : (
        <PracticeStage
          title={`Try it: ${pattern.displayName}`}
          subtitle={`Sentence ${index + 1} of ${sentences.length}`}
          homeHref={`/practice-words/${pattern.slug}`}
          wordArray={sentence.split(" ")}
          analysisData={analysisData}
          feedback={feedback}
          showHighlightedWords={showHighlightedWords}
          isRecording={isRecording}
          isProcessing={isProcessing}
          isFeedbackPlaying={feedbackAudio.isPlaying}
          audioLevel={levelRef}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onReplayFeedback={feedbackAudio.replay}
          next={{ visible: showNext, onNext: goNext }}
        />
      )}
    </>
  );
};

// For the parent: what's about to happen, before the mic prompt appears.
const TryIntro = ({
  pattern,
  count,
  onStart,
}: {
  pattern: PhonicsPattern;
  count: number;
  onStart: () => void;
}) => (
  <main className="flex min-h-dvh items-center justify-center bg-gradient-to-br from-background to-purple-50/50 px-4 py-10">
    <Card className="w-full max-w-lg rounded-3xl shadow-lg">
      <CardContent className="space-y-6 p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <img src={wordWizIcon} alt="" className="size-10" />
          <div>
            <p className="text-sm text-muted-foreground">Try Word Wiz AI</p>
            <h1 className="text-xl font-bold text-foreground sm:text-2xl">
              {pattern.displayName}
            </h1>
          </div>
        </div>
        <ul className="space-y-4 text-muted-foreground">
          <li className="flex gap-3">
            <Mic className="mt-0.5 size-5 shrink-0 text-primary" />
            <span>
              Your child reads {count} short sentences out loud. Tap the mic to
              start and tap it again when they're done.
            </span>
          </li>
          <li className="flex gap-3">
            <Volume2 className="mt-0.5 size-5 shrink-0 text-primary" />
            <span>
              After each one, Word Wiz shows which sounds came out wrong and
              says what to fix, out loud.
            </span>
          </li>
          <li className="flex gap-3">
            <ShieldCheck className="mt-0.5 size-5 shrink-0 text-primary" />
            <span>
              No account needed. Your browser will ask to use the microphone,
              and Word Wiz doesn't save recordings from this page.
            </span>
          </li>
        </ul>
        <Button size="lg" className="w-full rounded-2xl" onClick={onStart}>
          Start
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Works best with a quiet room and a decent microphone.
        </p>
      </CardContent>
    </Card>
  </main>
);

const ENDING_COPY: Record<Ending, { heading: string; body: string }> = {
  finished: {
    heading: "Nice reading!",
    body: "With a free account, Word Wiz writes each next sentence around the exact sounds your child missed and keeps track of how they're doing over time.",
  },
  limit: {
    heading: "That's all the free tries for now",
    body: "Make a free account to keep practicing. Word Wiz will pick up from the sounds your child is working on.",
  },
  unavailable: {
    heading: "Trying without an account isn't available right now",
    body: "You can still make a free account and start practicing right away.",
  },
};

const TryEnding = ({
  ending,
  pattern,
  onRestart,
}: {
  ending: Ending;
  pattern: PhonicsPattern;
  onRestart: () => void;
}) => (
  <main className="flex min-h-dvh items-center justify-center bg-gradient-to-br from-background to-purple-50/50 px-4 py-10">
    <Card className="w-full max-w-lg rounded-3xl shadow-lg">
      <CardContent className="space-y-6 p-6 text-center sm:p-8">
        <img src={wordWizIcon} alt="" className="mx-auto size-14" />
        <h1 className="text-2xl font-bold text-foreground">
          {ENDING_COPY[ending].heading}
        </h1>
        <p className="text-muted-foreground">{ENDING_COPY[ending].body}</p>
        <Button asChild size="lg" className="w-full rounded-2xl">
          <Link
            to="/signup"
            onClick={() => trackSignupClick("try_page", "link", pattern.slug)}
          >
            Create a free account
          </Link>
        </Button>
        <div className="flex flex-col gap-2 text-sm sm:flex-row sm:justify-center sm:gap-6">
          {ending === "finished" && (
            <button
              type="button"
              onClick={onRestart}
              className="text-primary underline-offset-4 hover:underline"
            >
              Read these again
            </button>
          )}
          <Link
            to={`/practice-words/${pattern.slug}`}
            className="text-primary underline-offset-4 hover:underline"
          >
            See the {pattern.displayName} word list
          </Link>
        </div>
      </CardContent>
    </Card>
  </main>
);

export default TryPage;
