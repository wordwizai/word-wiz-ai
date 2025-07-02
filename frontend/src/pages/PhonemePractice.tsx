import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Mic, RotateCcw, SkipForward } from "lucide-react";

const PhonemePractice = () => {
  const [currentSentence, setCurrentSentence] = useState(
    "The quick brown fox jumps over the lazy dog.",
  );

  return (
    <div className="p-6 min-h-screen flex flex-col w-full">
      <header className="text-center text-neutral-900">
        <h1 className="scroll-m-20 text-center text-4xl font-extrabold tracking-tight text-balance">
          Phoneme Practice
        </h1>
        <p className="text-sm">
          Focus on your target sounds with real-time feedback.
        </p>
      </header>

      <main className="flex-1 flex items-center justify-center">
        <Card className="bg-white p-6 shadow-soft max-w-2xl w-full">
          <CardHeader>
            <CardTitle className="text-center border-b pb-2 text-2xl font-semibold tracking-tight first:mt-0">
              Practice Sentence
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center text-xl font-semibold flex flex-wrap justify-center gap-2">
              {currentSentence.split(" ").map((word, index) => (
                <Button key={index} variant="secondary" className="p-2">
                  {word}
                </Button>
              ))}
            </div>
            <div className="flex justify-center space-x-4">
              <Button className="bg-fuchsia-400 text-white hover:opacity-90">
                <Mic className="mr-2 h-4 w-4" />
                Record
              </Button>
              <Button variant="outline">
                <RotateCcw className="mr-2 h-4 w-4" />
                Replay
              </Button>
              <Button variant="ghost">
                <SkipForward className="mr-2 h-4 w-4" />
                Skip
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default PhonemePractice;
