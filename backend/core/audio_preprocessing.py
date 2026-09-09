# %%
import os
import time
import weakref
from contextvars import ContextVar

import numpy as np
import IPython.display as ipd
import librosa
import librosa.display
import matplotlib.pyplot as plt
import noisereduce as nr
from .audio_quality_analyzer import AudioQualityAnalyzer
from .adaptive_noise_reduction import AdaptiveNoiseReducer


# ---------------------------------------------------------------------------
# Single-preprocessing-pass support
#
# Historically a single request ran `preprocess_audio` TWICE: once in
# routers/handlers/audio_processing_handler.py and once again inside
# core/process_audio.py. That means two rounds of spectral noise reduction and
# two peak normalizations on already-normalized audio, which erodes low-energy
# high-frequency content (unvoiced stops and fricatives such as /s/, /f/, /θ/).
#
# This module is now the single entry point for noise reduction + normalization.
# Redundant passes are suppressed via an explicit `already_preprocessed` flag,
# which callers may pass directly or leave as None to auto-detect: the exact
# array object produced by a previous pass is remembered (by weak reference,
# per-request via a ContextVar) and recognised on the way back in.
#
# Gated behind WWAI_SINGLE_PREPROCESS. With the flag unset every historical pass
# still runs, byte-for-byte as before.
# ---------------------------------------------------------------------------

SINGLE_PREPROCESS_ENV_VAR = "WWAI_SINGLE_PREPROCESS"

_TRUTHY = {"1", "true", "yes", "on"}

# Holds a weakref to the most recent array this module produced, scoped to the
# current asyncio task / thread context. Weak so it never keeps audio alive.
_last_preprocessed: ContextVar = ContextVar("wwai_last_preprocessed_audio", default=None)


def single_preprocess_enabled() -> bool:
    """True when WWAI_SINGLE_PREPROCESS is set to a truthy value.

    Read at call time (not import time) so tests and operators can toggle it.
    """
    return os.getenv(SINGLE_PREPROCESS_ENV_VAR, "").strip().lower() in _TRUTHY


def mark_preprocessed(audio) -> None:
    """Record `audio` as the output of a completed preprocessing pass.

    Call this at any site that ran `preprocess_audio` in a worker thread
    (``asyncio.to_thread`` copies the context, so a mark set inside the thread
    is discarded when the thread finishes).
    """
    try:
        _last_preprocessed.set(weakref.ref(audio))
    except TypeError:
        # Not weak-referenceable (e.g. a plain list) - fail safe by forgetting.
        _last_preprocessed.set(None)


def is_marked_preprocessed(audio) -> bool:
    """True only if `audio` is *the same object* a previous pass produced.

    Identity based on purpose: if anything copied or transformed the array in
    between we cannot prove it is still preprocessed, so we fall back to
    preprocessing it again (today's behavior). Fails safe, never silently.
    """
    ref = _last_preprocessed.get()
    if ref is None:
        return False
    return ref() is audio


def reset_preprocessing_state() -> None:
    """Forget any recorded preprocessing pass (used by tests and long-lived loops)."""
    _last_preprocessed.set(None)


def preprocess_audio(audio, sr=16000, audio_length_seconds=None, use_adaptive=True,
                     already_preprocessed=None):
    """
    Preprocess audio with adaptive noise reduction based on audio quality.
    
    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        audio_length_seconds: Duration of audio in seconds. If None, calculated from audio length.
        use_adaptive: If True, uses new adaptive noise reduction with SNR-based parameters.
                     If False, uses legacy noise reduction (for compatibility).
        already_preprocessed: Tri-state. True  -> this array has already been through a
                     preprocessing pass, skip noise reduction and normalization.
                     False -> force a pass. None (default) -> auto-detect by object
                     identity against the previous pass. Only honoured when
                     WWAI_SINGLE_PREPROCESS is enabled; otherwise ignored and every
                     pass runs exactly as it always has.

    Returns:
        Preprocessed audio array

    Note:
        New adaptive mode (default) analyzes audio quality (SNR) and adjusts noise
        reduction parameters accordingly. It also preserves edges better to avoid
        cutting off initial/final phonemes.
        
        Legacy mode uses the old length-based approach for backward compatibility.
    """
    preprocess_start = time.time()

    # Suppress redundant passes (flag-gated; no-op when the flag is unset).
    if single_preprocess_enabled():
        skip = (
            is_marked_preprocessed(audio)
            if already_preprocessed is None
            else bool(already_preprocessed)
        )
        if skip:
            print("⏭️  Skipping redundant preprocessing pass (WWAI_SINGLE_PREPROCESS)")
            mark_preprocessed(audio)
            return audio

    if audio_length_seconds is None:
        audio_length_seconds = len(audio) / sr

    if use_adaptive:
        # NEW: Adaptive noise reduction based on SNR
        print(f"🎯 Using adaptive noise reduction for {audio_length_seconds:.1f}s audio")
        
        # Analyze audio quality
        analyzer = AudioQualityAnalyzer(sr=sr)
        snr_db = analyzer.calculate_snr(audio)
        print(f"📊 Measured SNR: {snr_db:.1f} dB")
        
        # Apply adaptive noise reduction
        noise_start = time.time()
        reducer = AdaptiveNoiseReducer(sr=sr)
        audio = reducer.reduce_noise_adaptive(
            audio,
            snr_db=snr_db,
            preserve_edges=True,  # Preserve initial/final phonemes
            audio_length_seconds=audio_length_seconds
        )
        print(f"⏱️  Adaptive noise reduction took {time.time() - noise_start:.3f}s")
    else:
        # LEGACY: Length-based noise reduction (for backward compatibility)
        print(f"⚠️  Using legacy noise reduction for {audio_length_seconds:.1f}s audio")
        
        # Lighter noise reduction for longer audio to avoid distortion
        if audio_length_seconds > 8:
            print(f"⚠️  Long audio detected ({audio_length_seconds:.1f}s) - using lighter noise reduction")
            # Less aggressive noise reduction for long audio
            noise_start = time.time()
            audio = nr.reduce_noise(
                y=audio,
                sr=sr,
                stationary=True,
                prop_decrease=0.5  # Reduce by 50% instead of 100%
            )
            print(f"⏱️  Noise reduction took {time.time() - noise_start:.3f}s")
        else:
            # Standard noise reduction for shorter audio
            noise_start = time.time()
            audio = nr.reduce_noise(y=audio, sr=sr, stationary=True, prop_decrease=1.0)
            print(f"⏱️  Noise reduction took {time.time() - noise_start:.3f}s")
    
    norm_start = time.time()
    # Replace slow librosa.util.normalize with fast numpy normalization
    # librosa.util.normalize is calling scipy peak normalization which is extremely slow
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    print(f"⏱️  Normalization took {time.time() - norm_start:.3f}s")
    
    print(f"⏱️  Total preprocessing took {time.time() - preprocess_start:.3f}s")

    # Remember this exact array so a later pass in the same request can detect
    # that it has already been preprocessed. Read only when the flag is enabled.
    mark_preprocessed(audio)
    return audio


def display_spectrogram(audio, sr=16000):
    # Compute MFCCs
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mfccs, x_axis="time", sr=sr)
    plt.colorbar()
    plt.title("MFCC")
    plt.tight_layout()
    plt.show()


def display_playable_audio(audio, sr=16000):
    # Display a playable audio widget
    return ipd.Audio(data=audio, rate=sr)


# %%
if __name__ == "__main__":
    from audio_recording import record_and_process_pronunciation

    # Load the audio file
    audio, sr = librosa.load("temp_audio/output.wav", sr=16000)
    # Display the before audio
    playable_audio = display_playable_audio(audio, sr)
    results_before = record_and_process_pronunciation(
        "the cat jumped on the mat", use_previous_recording=True
    )

    print("Before audio widget:")
    ipd.display(playable_audio)

    # Preprocess the audio
    audio = preprocess_audio(audio, sr)
    results_after = record_and_process_pronunciation(
        "the cat jumped on the mat", use_previous_recording=True
    )

    # Display the spectrogram
    display_spectrogram(audio, sr)

    # Display the after audio
    playable_audio = display_playable_audio(audio, sr)
    print("After audio widget:")
    ipd.display(playable_audio)

    print("results before:")
    print(results_before)
    print("results after")
    print(results_after)
