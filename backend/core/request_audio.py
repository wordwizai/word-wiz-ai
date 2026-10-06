"""Quality gates and the single preprocessing pass for an uploaded recording.

Lifted out of routers/handlers/audio_processing_handler.py so the request path and the
accuracy benchmark (backend/tests/benchmark) run exactly the same gates. Raises
AudioRejected instead of an HTTP error, and the handler turns that into a 400.
"""

import time

import numpy as np

from .audio_preprocessing import preprocess_audio
from .audio_quality_analyzer import (
    AudioQualityAnalyzer,
    assess_processability,
    build_quality_warning,
    soft_quality_gates_enabled,
)


class AudioRejected(ValueError):
    """The recording cannot be analyzed. ``str(exc)`` is the message shown to the child."""


def gate_audio(audio_array: np.ndarray, sample_rate: int, quality_out: dict | None = None) -> dict:
    """Analyze recording quality and apply the soft or hard gates. Returns the quality report."""
    print("🔍 Analyzing audio quality...")
    quality_start = time.time()
    analyzer = AudioQualityAnalyzer(sr=sample_rate)
    quality_info = analyzer.analyze_audio_quality(audio_array)
    print(f"⏱️  Quality analysis took {time.time() - quality_start:.3f}s")

    # Log quality metrics
    print(f"📊 Audio Quality Report:")
    print(f"   - Quality Level: {quality_info['quality_level'].upper()}")
    print(f"   - Quality Score: {quality_info['quality_score']:.1f}/100")
    print(f"   - SNR: {quality_info['snr_db']:.1f} dB")
    print(f"   - Clipping: {quality_info['clipping_percentage']:.2f}%")
    print(f"   - Silence: {quality_info['silence_percentage']:.1f}%")
    print(f"   - Metrics mode: {quality_info.get('metrics_mode', 'legacy')}")

    if quality_out is not None:
        quality_out['quality_info'] = quality_info

    if soft_quality_gates_enabled():
        # SOFT GATES (WWAI_SOFT_QUALITY_GATES=1)
        #
        # Reject only audio we genuinely cannot process: nothing received, or
        # true digital silence. A noisy, clipped or pause-heavy recording is
        # still a child's honest attempt -- analyze it and pass a gentle hint
        # back to the frontend instead of refusing it.
        is_processable, reason = assess_processability(audio_array)
        if not is_processable:
            raise AudioRejected(reason)

        quality_warning = build_quality_warning(quality_info)
        if quality_warning is not None:
            print("⚠️  Soft quality gate: proceeding with a quality warning attached")
            for hint in quality_warning['hints']:
                print(f"   - {hint}")
            if quality_out is not None:
                quality_out['quality_warning'] = quality_warning
    else:
        # HARD GATES (default). Unchanged behavior.
        if quality_info['snr_db'] < 5.0:
            raise AudioRejected(
                "It was too noisy to hear the words clearly. Try somewhere quieter, "
                "or hold the device a little closer."
            )

        if quality_info['clipping_percentage'] > 10.0:
            raise AudioRejected(
                "That recording came out too loud and fuzzy. Try reading a little softer, "
                "or hold the device a bit farther away."
            )

        if quality_info['silence_percentage'] > 85.0:
            raise AudioRejected(
                "We could barely hear you. Read the sentence out loud, close to the microphone."
            )

    # Warn about quality issues but continue processing
    if quality_info['issues']:
        print(f"⚠️  Quality issues detected:")
        for issue in quality_info['issues']:
            print(f"   - {issue}")

    if quality_info['recommendations']:
        print(f"💡 Recommendations:")
        for rec in quality_info['recommendations']:
            print(f"   - {rec}")

    return quality_info


def gate_and_preprocess(audio_array: np.ndarray, sample_rate: int, audio_duration: float | None = None,
                        quality_out: dict | None = None, apply_gates: bool = True) -> np.ndarray:
    """Gate the recording, then run THE preprocessing pass for this request.

    The caller must ``mark_preprocessed()`` the result in its own context
    (asyncio.to_thread runs on a copied context, so a mark set in here is lost).
    ``apply_gates=False`` is for the benchmark's cache builder, which records model
    outputs for every clip and applies the gates later at scoring time.
    """
    if apply_gates:
        gate_audio(audio_array, sample_rate, quality_out)
    if audio_duration is None:
        audio_duration = len(audio_array) / sample_rate
    print("🔊 Starting audio preprocessing...")
    return preprocess_audio(
        audio_array, sr=sample_rate, audio_length_seconds=audio_duration,
        use_adaptive=True, already_preprocessed=False,
    )
