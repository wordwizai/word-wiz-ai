"""
Tests for WWAI_SINGLE_PREPROCESS (Agent 7: "preprocess exactly once") and for the
formerly-dead parameters of OptimizedAudioPreprocessor.preprocess_audio.

Background
----------
A single request used to run core.audio_preprocessing.preprocess_audio TWICE
(once in routers/handlers/audio_processing_handler.py, once again inside
core/process_audio.py) before the ONNX extractor did its own format-conditioning
pass - two rounds of spectral noise reduction and two peak normalizations on
already-normalized audio.

Measured on the synthetic utterance below, the second pass does four things, and
the numbers each test prints are the evidence:

  1. Discards another 50 ms of audio and drifts the timeline another 50 ms,
     because AdaptiveNoiseReducer's crossfade concatenation drops samples.
  2. Costs ~27% of the speech level (-2.7 dB) at the same peak, because a
     processing artifact sets the normalization peak.
  3. Pushes the fricative band (3-8 kHz) a further ~4.7 dB away from the true
     spectral balance. Note the drift is UPWARD, not downward: repeated spectral
     gating injects musical noise into the band that distinguishes /s/, /f/ and
     /th/, rather than erasing it.
  4. With a soft fricative, the loudest high-frequency event in the processed
     audio is not the fricative at all but the crossfade seam - and the second
     pass makes that phantom ~2.7x more prominent.

These tests quantify all of the above, verify the flag suppresses the redundant
pass, verify the flag OFF path is bit-identical to the historical behavior, and
verify a sample-rate mismatch is no longer silently mislabelled.

No network, no models, no pytest. Run from the backend/ directory:

    PYTHONIOENCODING=utf-8 <venv>/python.exe -m unittest tests.test_single_preprocess -v
"""

import contextlib
import io
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.audio_preprocessing import (  # noqa: E402
    SINGLE_PREPROCESS_ENV_VAR,
    mark_preprocessed,
    preprocess_audio,
    reset_preprocessing_state,
    single_preprocess_enabled,
)
from core.audio_optimization import OptimizedAudioPreprocessor  # noqa: E402


SR = 16000


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def quiet(fn, *args, **kwargs):
    """Run fn swallowing its (very chatty) stdout."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*args, **kwargs)


@contextlib.contextmanager
def flag(value):
    """Temporarily set/unset WWAI_SINGLE_PREPROCESS."""
    previous = os.environ.get(SINGLE_PREPROCESS_ENV_VAR)
    if value is None:
        os.environ.pop(SINGLE_PREPROCESS_ENV_VAR, None)
    else:
        os.environ[SINGLE_PREPROCESS_ENV_VAR] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(SINGLE_PREPROCESS_ENV_VAR, None)
        else:
            os.environ[SINGLE_PREPROCESS_ENV_VAR] = previous


def synth_utterance_quiet(seed=1234):
    """Same utterance with the fricatives roughly 25 dB below the vowels."""
    return synth_utterance(seed=seed, fricative_amplitude=0.010)


def synth_utterance(seed=1234, fricative_amplitude=0.055):
    """A deterministic synthetic 'utterance': voiced vowels plus quiet fricatives.

    Layout (2.0 s @ 16 kHz):
        0.00-0.10  silence
        0.10-0.50  voiced vowel   (loud, F0 130 Hz, harmonics to 1040 Hz)
        0.50-0.65  FRICATIVE #1   (quiet, high-pass noise -> /s/-like)
        0.65-1.05  voiced vowel   (F0 172 Hz)
        1.05-1.20  FRICATIVE #2   (quiet, high-pass noise -> /f/-like)
        1.20-1.60  voiced vowel   (F0 209 Hz)
        1.60-2.00  silence + broadband room noise everywhere

    No vowel harmonic reaches 3 kHz, so a 3 kHz high-pass sees only fricative
    energy, noise floor, or processing artifact.

    Returns (audio, list_of_(start_sample, end_sample) fricative windows).
    """
    rng = np.random.RandomState(seed)
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    audio = np.zeros(n, dtype=np.float64)

    # Voiced segments: harmonic stack with a smooth envelope. Each segment gets a
    # DIFFERENT fundamental and level so the clip is non-periodic and its
    # landmarks are unambiguous.
    for (start_s, end_s), f0, gain in (
        ((0.10, 0.50), 130.0, 0.60),
        ((0.65, 1.05), 172.0, 0.45),
        ((1.20, 1.60), 209.0, 0.52),
    ):
        a, b = int(start_s * SR), int(end_s * SR)
        seg_t = t[a:b] - t[a]
        env = np.hanning(b - a)
        voiced = (
            1.00 * np.sin(2 * np.pi * f0 * seg_t)
            + 0.50 * np.sin(2 * np.pi * 2 * f0 * seg_t)
            + 0.25 * np.sin(2 * np.pi * 4 * f0 * seg_t)
            + 0.12 * np.sin(2 * np.pi * 8 * f0 * seg_t)
        )
        audio[a:b] += gain * env * voiced

    # Fricatives: quiet high-frequency noise - the content most at risk from
    # repeated spectral gating.
    fric_windows = []
    for start_s, end_s in ((0.50, 0.65), (1.05, 1.20)):
        a, b = int(start_s * SR), int(end_s * SR)
        noise = rng.randn(b - a)
        # crude high-pass: subtract a 9-tap moving average
        k = 9
        smooth = np.convolve(noise, np.ones(k) / k, mode="same")
        hp = noise - smooth
        hp /= np.max(np.abs(hp))
        audio[a:b] += fricative_amplitude * np.hanning(b - a) * hp
        fric_windows.append((a, b))

    # Low-level stationary room noise across the whole clip.
    audio += 0.004 * rng.randn(n)
    return audio.astype(np.float32), fric_windows


def band_energy(x, lo_hz, hi_hz, sr=SR):
    """Energy of x within [lo_hz, hi_hz) via rFFT."""
    if len(x) == 0:
        return 0.0
    spec = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
    mask = (freqs >= lo_hz) & (freqs < hi_hz)
    return float(np.sum(spec[mask]))


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def hf_envelope(x, cutoff_hz=3000, win=480, sr=SR):
    """Short-time RMS of the signal above `cutoff_hz`.

    The synthetic vowels' highest harmonic is ~1.7 kHz, so everything this
    envelope sees is fricative energy, noise floor, or processing artifact.
    """
    from scipy.signal import butter, filtfilt

    b, a = butter(6, cutoff_hz, btype="highpass", fs=sr)
    y = filtfilt(b, a, np.asarray(x, dtype=np.float64))
    return np.sqrt(np.convolve(y * y, np.ones(win) / win, mode="same"))


def hf_peaks(x, n=2, guard_s=0.30, sr=SR):
    """Sample indices of the `n` strongest, well-separated HF-envelope peaks."""
    env = hf_envelope(x)
    work = env.copy()
    found = []
    for _ in range(n):
        i = int(np.argmax(work))
        found.append(i)
        work[max(0, i - int(guard_s * sr)): min(len(work), i + int(guard_s * sr))] = 0.0
    return sorted(found), env


def hf_peak_prominence(x):
    """(peak indices, prominence of each peak over the surrounding HF floor)."""
    peaks, env = hf_peaks(x)
    mask = np.ones(len(env), dtype=bool)
    for i in peaks:
        mask[max(0, i - int(0.25 * SR)): min(len(env), i + int(0.25 * SR))] = False
    floor = float(np.median(env[mask])) if mask.any() else 1e-12
    return peaks, [float(env[i]) / floor for i in peaks], floor


def measured_shift(processed, original):
    """Sample offset of `processed` w.r.t. `original`, from the fricative peaks.

    Each call to preprocess_audio runs AdaptiveNoiseReducer's edge-preserving
    path, whose crossfade concatenation silently DROPS 800 samples (50 ms), so a
    second pass leaves the audio both altered and time-shifted. Measure the shift
    from landmarks rather than assuming it.
    """
    p_proc, _ = hf_peaks(processed)
    p_orig, _ = hf_peaks(original)
    return int(round(float(np.mean(np.array(p_proc) - np.array(p_orig)))))


def one_pass(audio):
    """The production pipeline with WWAI_SINGLE_PREPROCESS enabled: NR+norm once."""
    with flag("true"):
        reset_preprocessing_state()
        a = quiet(preprocess_audio, audio.copy(), sr=SR, already_preprocessed=False)
        # second (redundant) pass - suppressed by the flag via identity detection
        a = quiet(preprocess_audio, a, sr=SR, already_preprocessed=None)
    return a


def triple_pass(audio):
    """Today's behavior with the flag unset: NR+norm twice."""
    with flag(None):
        reset_preprocessing_state()
        a = quiet(preprocess_audio, audio.copy(), sr=SR)
        a = quiet(preprocess_audio, a, sr=SR)
    return a


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

class TestSinglePreprocessFlag(unittest.TestCase):

    def setUp(self):
        reset_preprocessing_state()
        self.audio, self.fric = synth_utterance()

    def tearDown(self):
        reset_preprocessing_state()

    def test_flag_default_off(self):
        with flag(None):
            self.assertFalse(single_preprocess_enabled())
        with flag("false"):
            self.assertFalse(single_preprocess_enabled())
        with flag("true"):
            self.assertTrue(single_preprocess_enabled())
        with flag("1"):
            self.assertTrue(single_preprocess_enabled())

    def test_flag_off_runs_every_pass_identically_to_legacy(self):
        """Flag OFF must reproduce today's double-preprocess output EXACTLY.

        The legacy reference below is written out independently (adaptive noise
        reduction + peak normalize, applied twice) rather than reusing the flag
        path, so this is a real regression check on the refactor.
        """
        from core.adaptive_noise_reduction import AdaptiveNoiseReducer
        from core.audio_quality_analyzer import AudioQualityAnalyzer

        def legacy_single(a):
            analyzer = AudioQualityAnalyzer(sr=SR)
            snr = analyzer.calculate_snr(a)
            reducer = AdaptiveNoiseReducer(sr=SR)
            a = reducer.reduce_noise_adaptive(
                a, snr_db=snr, preserve_edges=True,
                audio_length_seconds=len(a) / SR,
            )
            m = np.max(np.abs(a))
            if m > 0:
                a = a / m
            return a

        reference = legacy_single(legacy_single(self.audio.copy()))
        actual = triple_pass(self.audio)

        self.assertEqual(reference.shape, actual.shape)
        np.testing.assert_array_equal(
            reference, actual,
            err_msg="Flag OFF changed the historical double-preprocess output",
        )
        print(f"\n[flag OFF] bit-identical to legacy double pass over "
              f"{len(actual)} samples (max abs diff = "
              f"{np.max(np.abs(reference - actual)):.3e})")

    def test_explicit_already_preprocessed_ignored_when_flag_off(self):
        """already_preprocessed=True must NOT short-circuit while the flag is off."""
        with flag(None):
            reset_preprocessing_state()
            src = self.audio.copy()
            out = quiet(preprocess_audio, src, sr=SR, already_preprocessed=True)
            self.assertFalse(
                np.array_equal(out, src),
                "flag OFF must still preprocess even when told it was already done",
            )

    def test_flag_on_skips_redundant_pass(self):
        with flag("true"):
            reset_preprocessing_state()
            first = quiet(preprocess_audio, self.audio.copy(), sr=SR,
                          already_preprocessed=False)
            second = quiet(preprocess_audio, first, sr=SR, already_preprocessed=None)
            self.assertIs(second, first, "redundant pass should return the same object")

    def test_identity_detection_fails_safe_on_a_copy(self):
        """If something copied the array we cannot prove it is preprocessed."""
        with flag("true"):
            reset_preprocessing_state()
            first = quiet(preprocess_audio, self.audio.copy(), sr=SR,
                          already_preprocessed=False)
            copied = first.copy()
            second = quiet(preprocess_audio, copied, sr=SR, already_preprocessed=None)
            self.assertIsNot(second, copied)

    def test_mark_preprocessed_is_honoured(self):
        """mark_preprocessed() is what the handler calls after its to_thread pass."""
        with flag("true"):
            reset_preprocessing_state()
            processed = quiet(preprocess_audio, self.audio.copy(), sr=SR,
                              already_preprocessed=False)
            reset_preprocessing_state()
            # Without the mark, the next pass reprocesses...
            again = quiet(preprocess_audio, processed, sr=SR, already_preprocessed=None)
            self.assertIsNot(again, processed)
            # ...with the mark, it is skipped.
            reset_preprocessing_state()
            mark_preprocessed(processed)
            skipped = quiet(preprocess_audio, processed, sr=SR, already_preprocessed=None)
            self.assertIs(skipped, processed)


class TestAsyncRequestShape(unittest.TestCase):
    """Mirror the real request shape: to_thread pass, then a downstream pass.

    load_and_preprocess_audio_bytes runs preprocess_audio via asyncio.to_thread,
    which executes on a COPY of the context - so a mark set inside the worker is
    thrown away. The handler therefore calls mark_preprocessed() itself, and this
    test proves that arrangement actually reaches process_audio_array's pass.
    """

    def setUp(self):
        reset_preprocessing_state()
        self.audio, _ = synth_utterance()

    def tearDown(self):
        reset_preprocessing_state()

    @staticmethod
    async def _request(audio, call_mark):
        import asyncio

        # --- audio_processing_handler.load_and_preprocess_audio_bytes ---
        processed = await asyncio.to_thread(
            quiet, preprocess_audio, audio, sr=SR,
            audio_length_seconds=len(audio) / SR, use_adaptive=True,
            already_preprocessed=False,
        )
        if call_mark:
            mark_preprocessed(processed)

        # --- core.process_audio.process_audio_array ---
        async def downstream(arr):
            return quiet(preprocess_audio, arr, sr=SR, already_preprocessed=None)

        return processed, await downstream(processed)

    def test_mark_survives_to_thread_and_suppresses_downstream_pass(self):
        import asyncio

        with flag("true"):
            reset_preprocessing_state()
            first, second = asyncio.run(self._request(self.audio.copy(), True))
            self.assertIs(second, first,
                          "handler mark must suppress the downstream pass")

    def test_without_the_handler_mark_the_context_copy_loses_it(self):
        """Documents WHY mark_preprocessed is called in the handler, not the worker."""
        import asyncio

        with flag("true"):
            reset_preprocessing_state()
            first, second = asyncio.run(self._request(self.audio.copy(), False))
            self.assertIsNot(second, first)

    def test_flag_off_always_runs_both_passes(self):
        import asyncio

        with flag(None):
            reset_preprocessing_state()
            first, second = asyncio.run(self._request(self.audio.copy(), True))
            self.assertIsNot(second, first)
            self.assertLess(len(second), len(first),
                            "flag OFF keeps today's double pass, including its "
                            "50 ms of extra truncation")


class TestDoublePreprocessDamage(unittest.TestCase):
    """Quantify what the redundant preprocessing pass actually does.

    Measured on a deterministic synthetic utterance, so the numbers printed here
    are reproducible without any model, audio fixture or network access.
    """

    @classmethod
    def setUpClass(cls):
        reset_preprocessing_state()
        cls.audio, cls.fric = synth_utterance()
        cls.single = one_pass(cls.audio)
        cls.triple = triple_pass(cls.audio)
        cls.shift_single = measured_shift(cls.single, cls.audio)
        cls.shift_triple = measured_shift(cls.triple, cls.audio)
        reset_preprocessing_state()

    def _window(self, sig, shift, a, b):
        return np.asarray(sig, dtype=np.float64)[a + shift: b + shift]

    # -- 1. audio is truncated and time-shifted, once per pass ---------------

    def test_redundant_pass_truncates_and_time_shifts_audio(self):
        """AdaptiveNoiseReducer's crossfade silently drops samples on every pass."""
        n0, n1, n2 = len(self.audio), len(self.single), len(self.triple)
        print("\n--- length / timing damage ----------------------------------")
        print(f"  original                   : {n0} samples ({n0 / SR:.4f}s)")
        print(f"  after one pass             : {n1} samples ({n1 / SR:.4f}s, "
              f"-{(n0 - n1) * 1000.0 / SR:.1f} ms); landmarks moved "
              f"{self.shift_single} samples ({self.shift_single * 1000.0 / SR:+.1f} ms)")
        print(f"  after two passes           : {n2} samples ({n2 / SR:.4f}s, "
              f"-{(n0 - n2) * 1000.0 / SR:.1f} ms); landmarks moved "
              f"{self.shift_triple} samples ({self.shift_triple * 1000.0 / SR:+.1f} ms)")
        print(f"  COST OF THE REDUNDANT PASS : {n1 - n2} extra samples "
              f"({(n1 - n2) * 1000.0 / SR:.1f} ms) discarded and "
              f"{abs(self.shift_triple - self.shift_single)} samples "
              f"({abs(self.shift_triple - self.shift_single) * 1000.0 / SR:.1f} ms) "
              f"of extra timeline drift")

        self.assertLess(n2, n1, "the second pass drops additional samples")
        self.assertLess(abs(self.shift_triple), abs(self.shift_single) * 3)
        self.assertGreater(abs(self.shift_triple), abs(self.shift_single),
                           "the second pass shifts the timeline further")

    # -- 2. the two outputs measurably differ --------------------------------

    def test_outputs_measurably_differ(self):
        """RMS of the difference, after undoing the measured timeline drift."""
        s = np.asarray(self.single, dtype=np.float64)
        t = np.asarray(self.triple, dtype=np.float64)
        drift = self.shift_triple - self.shift_single
        if drift < 0:
            s_al, t_al = s[-drift:], t
        else:
            s_al, t_al = s, t[drift:]
        n = min(len(s_al), len(t_al))
        s_al, t_al = s_al[:n], t_al[:n]

        diff = s_al - t_al
        d_rms = rms(diff)
        s_rms = rms(s_al)

        print("\n--- one pass vs two passes (time-aligned) -------------------")
        print(f"  compared over              : {n} samples ({n / SR:.3f}s)")
        print(f"  RMS(one pass)              : {s_rms:.6f}")
        print(f"  RMS(two passes)            : {rms(t_al):.6f}")
        print(f"  RMS(difference)            : {d_rms:.6f}")
        print(f"  difference as % of signal  : {100.0 * d_rms / s_rms:.2f}%")
        print(f"  peak abs difference        : {float(np.max(np.abs(diff))):.6f}")

        self.assertGreater(d_rms, 1e-5,
                           "the second preprocessing pass should measurably change audio")

    # -- 3. dynamic range into the model -------------------------------------

    def test_second_pass_costs_dynamic_range(self):
        """Both outputs are peak-normalized, so lower RMS = quieter real speech.

        A processing artifact sets the peak on the second pass, and the peak
        normalization that follows scales the actual speech down with it.
        """
        r1, r2 = rms(self.single), rms(self.triple)
        p1 = float(np.max(np.abs(self.single)))
        p2 = float(np.max(np.abs(self.triple)))
        print("\n--- dynamic range at unit peak ------------------------------")
        print(f"  one pass  : peak={p1:.4f}  RMS={r1:.6f}  crest={p1 / r1:.2f}")
        print(f"  two passes: peak={p2:.4f}  RMS={r2:.6f}  crest={p2 / r2:.2f}")
        print(f"  speech level lost to the redundant pass: "
              f"{100.0 * (r1 - r2) / r1:.2f}%  "
              f"({20 * np.log10(r2 / r1):+.2f} dB)")
        self.assertAlmostEqual(p1, 1.0, places=5)
        self.assertAlmostEqual(p2, 1.0, places=5)
        self.assertLess(r2, r1,
                        "the second pass leaves less speech energy at the same peak")

    # -- 4. fricative band is pushed further from the true spectrum ----------

    def test_fricative_band_balance_distorted_more_by_second_pass(self):
        """How far the fricative band drifts from the ORIGINAL spectral balance.

        Metric: energy in the fricative bursts at 3-8 kHz, divided by the voiced
        (0-1.5 kHz) energy of the whole clip - a scale-free description of the
        spectral balance the acoustic model sees. Distance is measured in dB from
        the original, so both attenuation and artifact inflation count as damage.
        """
        def balance(sig, shift):
            hf = sum(band_energy(self._window(sig, shift, a, b), 3000, 8000)
                     for a, b in self.fric)
            lf = band_energy(np.asarray(sig, dtype=np.float64), 0, 1500)
            return hf / lf if lf > 0 else 0.0

        b_orig = balance(self.audio, 0)
        b_single = balance(self.single, self.shift_single)
        b_triple = balance(self.triple, self.shift_triple)

        d_single = abs(10 * np.log10(b_single / b_orig))
        d_triple = abs(10 * np.log10(b_triple / b_orig))

        print("\n--- fricative 3-8 kHz energy / voiced 0-1.5 kHz energy ------")
        print(f"  original                   : {b_orig:.6e}")
        print(f"  one preprocessing pass     : {b_single:.6e}  "
              f"({10 * np.log10(b_single / b_orig):+.2f} dB from true)")
        print(f"  two preprocessing passes   : {b_triple:.6e}  "
              f"({10 * np.log10(b_triple / b_orig):+.2f} dB from true)")
        print(f"  the redundant pass pushes the fricative band a further "
              f"{d_triple - d_single:.2f} dB away from the real spectrum")
        print("  (the drift is UPWARD: repeated spectral gating injects musical "
              "noise into exactly the band that distinguishes /s/, /f/ and /th/)")

        self.assertLess(
            d_single, d_triple,
            "one pass must land closer to the original fricative-band balance",
        )

    def test_per_fricative_burst_balance(self):
        print("\n--- per-burst 3-8 kHz energy / voiced band ------------------")
        lf0 = band_energy(np.asarray(self.audio, dtype=np.float64), 0, 1500)
        lf1 = band_energy(np.asarray(self.single, dtype=np.float64), 0, 1500)
        lf2 = band_energy(np.asarray(self.triple, dtype=np.float64), 0, 1500)
        for i, (a, b) in enumerate(self.fric, start=1):
            e0 = band_energy(self._window(self.audio, 0, a, b), 3000, 8000) / lf0
            e1 = band_energy(self._window(self.single, self.shift_single, a, b), 3000, 8000) / lf1
            e2 = band_energy(self._window(self.triple, self.shift_triple, a, b), 3000, 8000) / lf2
            print(f"  burst #{i} ({a / SR:.2f}-{b / SR:.2f}s): true={e0:.4e}  "
                  f"1-pass={e1:.4e} ({10 * np.log10(e1 / e0):+.2f} dB)  "
                  f"2-pass={e2:.4e} ({10 * np.log10(e2 / e0):+.2f} dB)")
        self.assertTrue(True)

    # -- 5. quiet fricatives: the second pass amplifies a phantom -----------

    def test_quiet_fricative_replaced_by_seam_artifact(self):
        """With a soft fricative the loudest HF event stops being the fricative.

        Both pipelines lose a quiet /f/-like burst into the noise floor, but the
        crossfade seam of AdaptiveNoiseReducer leaves a broadband transient
        behind - and running the pass twice makes that phantom substantially more
        prominent, which is exactly the kind of thing an acoustic model reads as
        a consonant that was never spoken.
        """
        quiet_audio, quiet_fric = synth_utterance_quiet()
        s = one_pass(quiet_audio)
        t = triple_pass(quiet_audio)
        reset_preprocessing_state()

        true_centres = [((a + b) / 2) / SR for a, b in quiet_fric]

        def describe(name, sig):
            peaks, prom, floor = hf_peak_prominence(sig)
            centres = [p / SR for p in peaks]
            on_target = all(
                min(abs(c - tc) for tc in true_centres) < 0.12 for c in centres
            )
            print(f"  {name:11s} loudest HF events at "
                  f"{[f'{c:.3f}s' for c in centres]} "
                  f"prominence {[f'{p:.2f}x' for p in prom]} "
                  f"-> {'fricatives' if on_target else 'NOT the fricatives'}")
            return max(prom), on_target

        print("\n--- quiet fricative (25 dB below the vowels) ----------------")
        print(f"  true fricative centres at {[f'{c:.3f}s' for c in true_centres]}")
        describe("original", quiet_audio)
        prom_single, on_single = describe("one pass", s)
        prom_triple, on_triple = describe("two passes", t)
        print(f"  phantom prominence grows {prom_single:.2f}x -> {prom_triple:.2f}x "
              f"({100.0 * (prom_triple - prom_single) / prom_single:.0f}% stronger) "
              f"purely from running preprocessing a second time")

        self.assertFalse(on_single, "sanity: the quiet fricative should be lost")
        self.assertFalse(on_triple, "sanity: the quiet fricative should be lost")
        self.assertGreater(prom_triple, prom_single,
                           "the redundant pass makes the phantom HF event louder")



class TestSampleRateContract(unittest.TestCase):
    """OptimizedAudioPreprocessor used to accept `sr` and never resample."""

    def setUp(self):
        self.audio_44k = np.sin(
            2 * np.pi * 220 * np.arange(int(1.0 * 44100)) / 44100
        ).astype(np.float32) * 0.5

    def test_mismatch_no_longer_silently_mislabelled(self):
        """44.1 kHz in -> genuinely 16 kHz out, not 'call it 16 kHz and hope'."""
        p = OptimizedAudioPreprocessor(target_sr=16000, use_phoneme_aware_trim=False)
        out, out_sr = p.preprocess_audio(self.audio_44k, sr=44100)
        self.assertEqual(out_sr, 16000)
        expected = len(self.audio_44k) * 16000 / 44100
        # Trimming removes a little; the point is it is ~16k-rate, not 44.1k-rate.
        print(f"\n[sample rate] 44100 Hz input of {len(self.audio_44k)} samples "
              f"-> {len(out)} samples @ {out_sr} Hz "
              f"(un-resampled would have been ~{len(self.audio_44k)})")
        self.assertLess(len(out), expected * 1.05)
        self.assertGreater(len(out), expected * 0.5)
        # Duration must be preserved to within trimming tolerance.
        self.assertAlmostEqual(len(out) / out_sr, len(self.audio_44k) / 44100,
                               delta=0.25)

    def test_mismatch_can_raise_instead(self):
        p = OptimizedAudioPreprocessor(target_sr=16000, sample_rate_policy="error",
                                       use_phoneme_aware_trim=False)
        with self.assertRaises(ValueError) as ctx:
            p.preprocess_audio(self.audio_44k, sr=44100)
        self.assertIn("Sample rate mismatch", str(ctx.exception))

        # per-call override works too
        p2 = OptimizedAudioPreprocessor(target_sr=16000, use_phoneme_aware_trim=False)
        with self.assertRaises(ValueError):
            p2.preprocess_audio(self.audio_44k, sr=44100, sample_rate_policy="error")

    def test_unknown_policy_rejected(self):
        with self.assertRaises(ValueError):
            OptimizedAudioPreprocessor(sample_rate_policy="shrug")

    def test_matching_sample_rate_is_untouched_by_the_new_code(self):
        """Every real caller passes 16 kHz; that path must be unchanged."""
        audio = synth_utterance()[0]
        p = OptimizedAudioPreprocessor(target_sr=16000, use_phoneme_aware_trim=False)
        out, out_sr = p.preprocess_audio(audio.copy(), sr=16000)
        self.assertEqual(out_sr, 16000)
        # No normalization by default -> peak is untouched by this stage.
        self.assertAlmostEqual(float(np.max(np.abs(out))),
                               float(np.max(np.abs(audio))), places=6)

    def test_normalize_parameter_actually_works_now(self):
        audio = (synth_utterance()[0] * 0.25).astype(np.float32)
        p = OptimizedAudioPreprocessor(target_sr=16000, use_phoneme_aware_trim=False)
        plain, _ = p.preprocess_audio(audio.copy(), sr=16000, normalize=False)
        normed, _ = p.preprocess_audio(audio.copy(), sr=16000, normalize=True)
        self.assertLess(float(np.max(np.abs(plain))), 0.99)
        self.assertAlmostEqual(float(np.max(np.abs(normed))), 1.0, places=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
