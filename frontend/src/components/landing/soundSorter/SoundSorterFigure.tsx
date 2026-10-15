import { useEffect, useRef, type RefObject } from "react";
import { SORTER_DATA, SORTER_SVG } from "./art.generated";
import { mountSoundSorter, type SorterControls, type SorterInfo } from "./live";
import "./sorter.generated.css";

// One object for the life of the page. React re-applies innerHTML whenever this
// prop changes identity, which would swap out the SVG the live code is moving.
const ART = { __html: SORTER_SVG };

interface Props {
  dark: boolean;
  onChange?: (info: SorterInfo) => void;
  /** Filled with play() and destroy() once the machine is running. */
  controlsRef?: RefObject<SorterControls | null>;
}

/**
 * The sound sorter itself, the prebuilt SVG plus the code that moves it.
 * Loaded on its own (React.lazy) because the art is about 60 KB gzipped.
 */
const SoundSorterFigure = ({ dark, onChange, controlsRef }: Props) => {
  const stage = useRef<HTMLDivElement>(null);
  const readout = useRef<HTMLParagraphElement>(null);
  const change = useRef(onChange);

  useEffect(() => {
    change.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!stage.current) return;
    const controls = mountSoundSorter(stage.current, SORTER_DATA, {
      readout: readout.current,
      onChange: (info) => change.current?.(info),
    });
    if (controlsRef) controlsRef.current = controls;
    return () => {
      controls.destroy();
      if (controlsRef) controlsRef.current = null;
    };
  }, [controlsRef]);

  return (
    <div className="iso ss-root" data-theme={dark ? "dark" : "light"}>
      <div
        ref={stage}
        className="iso-stage ss-stage"
        tabIndex={0}
        role="group"
        aria-label="The sound sorter. Press space, or tap it, for the next reading."
        dangerouslySetInnerHTML={ART}
      />
      <p
        ref={readout}
        aria-hidden="true"
        className="mt-1 text-right font-mono text-xs text-muted-foreground"
      />
    </div>
  );
};

export default SoundSorterFigure;
