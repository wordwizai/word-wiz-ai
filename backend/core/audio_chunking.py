"""
Audio Chunking Module

Intelligently splits long audio recordings into smaller chunks for processing.
This improves model accuracy and prevents timeouts on longer recordings.

Two chunking strategies live in this module:

1. LEGACY (default). ``librosa.effects.split`` finds the non-silent intervals and
   only those intervals are concatenated into a chunk. Every inter-word pause is
   discarded, so words end up acoustically fused at the seams. This destroys the
   very cue wav2vec2 uses to emit ``|`` word-boundary tokens and that Deepgram /
   Whisper use to segment words.

2. PAUSE-PRESERVING (opt-in, ``WWAI_CHUNK_PRESERVE_PAUSES=true``). Silence is used
   only to decide *where to cut*, never *what to keep*: each chunk is a single
   contiguous slice ``audio[start:end]`` so all inter-word silence survives.
   Consecutive chunks additionally overlap by a small lead-in so a phoneme or word
   sitting on a boundary is fully present in at least one chunk;
   :func:`merge_chunk_results` then removes the duplicated words at the seam.

Environment flags (all read at call time, so they can be toggled in tests):

    WWAI_CHUNK_PRESERVE_PAUSES   master switch, default OFF (legacy behavior)
    WWAI_CHUNK_MAX_DURATION      max chunk length in seconds, default 12.0
    WWAI_CHUNK_MIN_DURATION      min distance between cuts in seconds, default 1.0
    WWAI_CHUNK_OVERLAP_SECONDS   overlap lead-in per chunk in seconds, default 0.5
    WWAI_CHUNK_THRESHOLD_SECONDS chunking threshold in seconds, default 15.0
    WWAI_CHUNK_DEDUPE_MAX_WORDS  max words removed at a seam, default 3

With WWAI_CHUNK_PRESERVE_PAUSES unset, every function in this module behaves
exactly as it did before this module gained the flag.
"""

import os

import numpy as np
import librosa


# ---------------------------------------------------------------------------
# Flag / config plumbing
# ---------------------------------------------------------------------------

_TRUTHY = {"1", "true", "yes", "on", "y", "t"}

# Defaults for the pause-preserving path. See module docstring for the env names.
_DEFAULT_MAX_CHUNK_DURATION = 12.0
_DEFAULT_MIN_CHUNK_DURATION = 1.0
_DEFAULT_OVERLAP_SECONDS = 0.5
_DEFAULT_CHUNK_THRESHOLD_SECONDS = 15.0
_DEFAULT_DEDUPE_MAX_WORDS = 3

# Legacy defaults, kept so the flag-off path is byte-identical to the old code.
_LEGACY_MAX_CHUNK_DURATION = 7
_LEGACY_CHUNK_THRESHOLD_SECONDS = 8


def preserve_pauses_enabled():
    """True when WWAI_CHUNK_PRESERVE_PAUSES is set to a truthy value."""
    return os.environ.get("WWAI_CHUNK_PRESERVE_PAUSES", "").strip().lower() in _TRUTHY


def _env_float(name, default):
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        print(f"⚠️  {name}={raw!r} is not a number - falling back to {default}")
        return default


def _env_int(name, default):
    value = _env_float(name, None)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def plan_chunk_boundaries(audio, sr=16000, max_chunk_duration=None,
                          min_chunk_duration=None, top_db=30):
    """
    Choose sample positions at which to cut the audio, using silence as the guide.

    Unlike the legacy path this returns *cut positions*, not "keep" regions: the
    caller slices contiguous spans between consecutive boundaries, so all the
    silence between words stays inside the chunks.

    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        max_chunk_duration: Maximum chunk length in seconds (None -> env/default)
        min_chunk_duration: Minimum distance between two cuts in seconds
        top_db: Threshold in dB below reference for silence detection

    Returns:
        list[int]: strictly increasing boundaries, starting at 0 and ending at
        len(audio). Consecutive pairs describe one chunk's nominal span.
    """
    audio = np.asarray(audio)
    n = int(len(audio))

    if max_chunk_duration is None:
        max_chunk_duration = _env_float("WWAI_CHUNK_MAX_DURATION", _DEFAULT_MAX_CHUNK_DURATION)
    if min_chunk_duration is None:
        min_chunk_duration = _env_float("WWAI_CHUNK_MIN_DURATION", _DEFAULT_MIN_CHUNK_DURATION)

    max_len = max(1, int(round(float(max_chunk_duration) * sr)))
    min_len = max(1, int(round(float(min_chunk_duration) * sr)))
    if min_len >= max_len:
        min_len = max(1, max_len // 3)

    if n <= max_len:
        return [0, n]

    # Candidate cuts sit in the MIDDLE of each silence gap, so both neighbouring
    # words keep roughly half of the pause that surrounds them.
    intervals = librosa.effects.split(audio, top_db=top_db)
    candidates = []
    for i in range(len(intervals) - 1):
        gap_start = int(intervals[i][1])
        gap_end = int(intervals[i + 1][0])
        if gap_end > gap_start:
            candidates.append(((gap_start + gap_end) // 2, gap_end - gap_start))

    boundaries = [0]
    pos = 0
    # Leaving up to max_len + min_len for the tail avoids emitting a sliver chunk
    # at the very end of the recording.
    while n - pos > max_len + min_len:
        window_lo = pos + min_len
        window_hi = pos + max_len
        best_cut = None
        best_gap = -1
        for cut, gap in candidates:
            if window_lo < cut <= window_hi:
                # Longest pause wins; ties break toward the later cut so chunks
                # stay as long as possible (fewer seams = fewer seam artifacts).
                if gap > best_gap or (gap == best_gap and cut > best_cut):
                    best_cut = cut
                    best_gap = gap
        cut = best_cut if best_cut is not None else window_hi
        boundaries.append(int(cut))
        pos = int(cut)

    boundaries.append(n)
    return boundaries


def _chunk_audio_preserving_pauses(audio, sr, max_chunk_duration, top_db,
                                   overlap_seconds=None, min_chunk_duration=None):
    """
    Pause-preserving chunker: contiguous slices with a small overlapping lead-in.

    Returns the same ``(chunks, chunk_metadata)`` pair as the legacy path. Each
    metadata dict carries the four required keys (``start_time``, ``end_time``,
    ``duration``, ``num_samples``) describing the ACTUAL returned array, plus two
    extra keys used by :func:`merge_chunk_results` to undo the overlap:
    ``overlap_start_seconds`` and ``nominal_start_time``.
    """
    audio = np.asarray(audio)
    n = int(len(audio))

    if overlap_seconds is None:
        overlap_seconds = _env_float("WWAI_CHUNK_OVERLAP_SECONDS", _DEFAULT_OVERLAP_SECONDS)
    overlap_samples = max(0, int(round(float(overlap_seconds) * sr)))

    boundaries = plan_chunk_boundaries(
        audio,
        sr=sr,
        max_chunk_duration=max_chunk_duration,
        min_chunk_duration=min_chunk_duration,
        top_db=top_db,
    )

    chunks = []
    chunk_metadata = []

    for i in range(len(boundaries) - 1):
        nominal_start = boundaries[i]
        nominal_end = boundaries[i + 1]
        if nominal_end <= nominal_start:
            continue

        lead_in = 0 if i == 0 else min(overlap_samples, nominal_start)
        actual_start = nominal_start - lead_in

        # Contiguous slice: inter-word silence is INSIDE the chunk, not removed.
        chunk_audio = audio[actual_start:nominal_end]
        chunks.append(chunk_audio)

        start_time = actual_start / sr
        end_time = nominal_end / sr
        duration = len(chunk_audio) / sr
        chunk_metadata.append({
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "num_samples": int(len(chunk_audio)),
            # Extra keys (ignored by process_audio.py, used by merge_chunk_results)
            "overlap_start_seconds": lead_in / sr,
            "nominal_start_time": nominal_start / sr,
        })
        print(
            f"  Chunk {len(chunks)}: {start_time:.2f}s - {end_time:.2f}s "
            f"({duration:.2f}s, {lead_in / sr:.2f}s overlap, pauses preserved)"
        )

    if not chunks:
        return [], []

    return chunks, chunk_metadata


def chunk_audio_at_silence(audio, sr=16000, max_chunk_duration=None, top_db=30):
    """
    Split audio into chunks at silence points.

    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        max_chunk_duration: Maximum duration of each chunk in seconds. ``None``
            (the default) resolves to 7 with the flag off, or to
            ``WWAI_CHUNK_MAX_DURATION`` (default 12.0) with the flag on.
        top_db: Threshold in dB below reference for silence detection (default 30)

    Returns:
        List of audio chunks (numpy arrays)
        List of chunk metadata dicts with keys ``start_time``, ``end_time``,
        ``duration``, ``num_samples`` (the pause-preserving path adds
        ``overlap_start_seconds`` and ``nominal_start_time``).

    Note:
        Default behavior (``WWAI_CHUNK_PRESERVE_PAUSES`` unset) is the legacy one:
        only the non-silent intervals are concatenated, so every inter-word pause
        is DROPPED from the chunk. With the flag on, each chunk is a single
        contiguous slice, silence included, and consecutive chunks overlap by
        ``WWAI_CHUNK_OVERLAP_SECONDS``.

        In both cases, if no suitable silence is found the audio is split at the
        max_chunk_duration boundary.
    """
    if preserve_pauses_enabled():
        return _chunk_audio_preserving_pauses(
            audio,
            sr=sr,
            max_chunk_duration=max_chunk_duration,
            top_db=top_db,
        )

    if max_chunk_duration is None:
        max_chunk_duration = _LEGACY_MAX_CHUNK_DURATION

    # --- legacy path: unchanged behavior -----------------------------------
    # Find silence intervals
    intervals = librosa.effects.split(audio, top_db=top_db)

    chunks = []
    chunk_metadata = []
    current_chunk_start = 0
    current_chunk_samples = []
    current_chunk_duration = 0

    for start, end in intervals:
        segment = audio[start:end]
        segment_duration = len(segment) / sr

        if current_chunk_duration + segment_duration > max_chunk_duration:
            # Save current chunk if it has content
            if current_chunk_samples:
                chunk_audio = np.concatenate(current_chunk_samples)
                chunks.append(chunk_audio)
                chunk_end_time = current_chunk_start + current_chunk_duration
                chunk_metadata.append({
                    "start_time": current_chunk_start,
                    "end_time": chunk_end_time,
                    "duration": current_chunk_duration,
                    "num_samples": len(chunk_audio)
                })
                print(f"  Chunk {len(chunks)}: {current_chunk_start:.2f}s - {chunk_end_time:.2f}s ({current_chunk_duration:.2f}s)")

            # Start new chunk
            current_chunk_start = start / sr
            current_chunk_samples = [segment]
            current_chunk_duration = segment_duration
        else:
            # Add segment to current chunk
            current_chunk_samples.append(segment)
            current_chunk_duration += segment_duration

    # Don't forget the last chunk
    if current_chunk_samples:
        chunk_audio = np.concatenate(current_chunk_samples)
        chunks.append(chunk_audio)
        chunk_end_time = current_chunk_start + current_chunk_duration
        chunk_metadata.append({
            "start_time": current_chunk_start,
            "end_time": chunk_end_time,
            "duration": current_chunk_duration,
            "num_samples": len(chunk_audio)
        })
        print(f"  Chunk {len(chunks)}: {current_chunk_start:.2f}s - {chunk_end_time:.2f}s ({current_chunk_duration:.2f}s)")

    return chunks, chunk_metadata


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------

def _normalize_word(word):
    """Lowercase, strip punctuation - used only to compare words across a seam."""
    return "".join(ch for ch in str(word).lower() if ch.isalnum())


def _seam_overlap_length(previous_words, incoming_words, max_words):
    """
    Number of leading words of ``incoming_words`` that repeat the tail of
    ``previous_words``. Returns 0 when there is no match.
    """
    limit = min(max_words, len(previous_words), len(incoming_words))
    for k in range(limit, 0, -1):
        tail = [_normalize_word(w) for w in previous_words[-k:]]
        head = [_normalize_word(w) for w in incoming_words[:k]]
        if all(tail) and tail == head:
            return k
    return 0


def merge_chunk_results(chunk_phonemes, chunk_words, chunk_metadata):
    """
    Merge phoneme and word extraction results from multiple audio chunks.

    Args:
        chunk_phonemes: List of phoneme arrays (one per chunk) - each chunk returns list of word phonemes
        chunk_words: List of word arrays (one per chunk)
        chunk_metadata: List of chunk metadata dicts

    Returns:
        merged_phonemes: Combined phoneme array (list of lists, one per word)
        merged_words: Combined word array

    Note:
        Default behavior (``WWAI_CHUNK_PRESERVE_PAUSES`` unset) is a plain
        concatenation: there is NO overlap handling and NO deduplication, because
        the legacy chunker produces no overlap to handle.

        With the flag on, chunks overlap by ``WWAI_CHUNK_OVERLAP_SECONDS`` and this
        function removes the duplicated words at each seam. A chunk is only
        de-duplicated when its metadata reports ``overlap_start_seconds > 0`` and
        its word and phoneme lists are the same length (so entries can be dropped
        in lockstep); otherwise that seam falls back to plain concatenation.

        Phoneme predictions are nested: [[word1_phonemes], [word2_phonemes], ...]
    """
    if not chunk_phonemes:
        return [], []

    if not preserve_pauses_enabled():
        # Concatenate results from all chunks
        # phonemes is a list of lists (one list per word), so we extend the outer list
        merged_phonemes = []
        merged_words = []

        for i, (phonemes, words) in enumerate(zip(chunk_phonemes, chunk_words)):
            # phonemes is already a list of lists (e.g., [['h','ɛ','l','oʊ'], ['w','ɜː','l','d']])
            # words is a list of strings (e.g., ['hello', 'world'])
            if phonemes and isinstance(phonemes, list):
                merged_phonemes.extend(phonemes)
            if words and isinstance(words, list):
                merged_words.extend(words)

        return merged_phonemes, merged_words

    # --- pause-preserving path: undo the overlap at each seam ---------------
    max_dedupe_words = max(0, _env_int("WWAI_CHUNK_DEDUPE_MAX_WORDS", _DEFAULT_DEDUPE_MAX_WORDS))
    metadata = chunk_metadata if isinstance(chunk_metadata, (list, tuple)) else []

    merged_phonemes = []
    merged_words = []

    for i, (phonemes, words) in enumerate(zip(chunk_phonemes, chunk_words)):
        chunk_ph = list(phonemes) if isinstance(phonemes, list) else []
        chunk_wd = list(words) if isinstance(words, list) else []

        drop = 0
        if i > 0 and max_dedupe_words and chunk_wd and merged_words:
            meta = metadata[i] if i < len(metadata) and isinstance(metadata[i], dict) else {}
            has_overlap = float(meta.get("overlap_start_seconds", 0.0) or 0.0) > 0.0
            # Only safe to drop phonemes alongside words when they line up 1:1.
            aligned = len(chunk_ph) == len(chunk_wd)
            if has_overlap and aligned:
                drop = _seam_overlap_length(merged_words, chunk_wd, max_dedupe_words)
                if drop:
                    print(f"  ↔ Seam {i}: dropping {drop} duplicated word(s) from chunk {i + 1}: {chunk_wd[:drop]}")

        if chunk_ph:
            merged_phonemes.extend(chunk_ph[drop:])
        if chunk_wd:
            merged_words.extend(chunk_wd[drop:])

    return merged_phonemes, merged_words


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

def should_use_chunking(audio, sr=16000, threshold_seconds=8):
    """
    Determine if audio should be chunked based on duration.

    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        threshold_seconds: Duration threshold for chunking (default 8)

    Returns:
        bool: True if audio should be chunked, False otherwise

    Note:
        When ``WWAI_CHUNK_PRESERVE_PAUSES`` is on, ``threshold_seconds`` is
        OVERRIDDEN by ``WWAI_CHUNK_THRESHOLD_SECONDS`` (default 15.0). The
        override is deliberate: the only caller
        (``process_audio.process_audio_array``) passes ``threshold_seconds=8``
        positionally, so an argument default could never take effect.

        Why 15s rather than 8s: chunking exists to bound model latency/memory, but
        every seam costs accuracy. With the legacy chunker each seam also fused two
        words together, and 8s meant most slow readers on a long sentence got
        chunked. With pauses preserved and a 12s max chunk, a 15s threshold means a
        typical read-aloud sentence (well under 15s even for a struggling reader)
        goes through the model in ONE pass with zero seams, while genuinely long
        recordings still get split.
    """
    audio_duration = len(audio) / sr
    if preserve_pauses_enabled():
        threshold_seconds = _env_float(
            "WWAI_CHUNK_THRESHOLD_SECONDS", _DEFAULT_CHUNK_THRESHOLD_SECONDS
        )
    return audio_duration > threshold_seconds


def estimate_speech_activity(audio, sr=16000, frame_length=2048, hop_length=512, top_db=30):
    """
    Estimate the percentage of audio that contains speech (vs silence).

    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        frame_length: Length of each frame for RMS calculation
        hop_length: Number of samples between frames
        top_db: Threshold in dB for silence detection

    Returns:
        float: Percentage of audio containing speech (0-100)
    """
    # Compute RMS energy for each frame
    rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]

    # Convert to dB
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)

    # Count frames above threshold
    speech_frames = np.sum(rms_db > -top_db)
    total_frames = len(rms_db)

    speech_percentage = (speech_frames / total_frames) * 100
    return speech_percentage


if __name__ == "__main__":
    # Test chunking with sample audio
    import soundfile as sf

    # Load a test audio file
    audio, sr = librosa.load("temp_audio/output.wav", sr=16000)

    print(f"Audio duration: {len(audio)/sr:.2f}s")

    # Test speech activity estimation
    speech_pct = estimate_speech_activity(audio, sr)
    print(f"Speech activity: {speech_pct:.1f}%")

    # Test chunking
    if should_use_chunking(audio, sr):
        print("Audio should be chunked")
        chunks, metadata = chunk_audio_at_silence(audio, sr)
        print(f"Created {len(chunks)} chunks")
    else:
        print("Audio is short enough - no chunking needed")
