"""Quality gates and the single preprocessing pass (core/request_audio.py).

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_request_audio -v
"""

import asyncio
import contextlib
import io
import os
import sys
import unittest
from unittest import mock

import numpy as np
import soundfile as sf

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core import request_audio as R  # noqa: E402

SAMPLE_WAV = os.path.join(BACKEND_ROOT, "tests", "system", "test_case_02", "audio.wav")


def _quiet():
    return contextlib.redirect_stdout(io.StringIO())


class TestGates(unittest.TestCase):
    def setUp(self):
        # Soft gates are the default, so the hard gates have to be asked for.
        self._saved = os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "0"
        self.speech, self.sr = sf.read(SAMPLE_WAV, dtype="float32")

    def tearDown(self):
        os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        if self._saved is not None:
            os.environ["WWAI_SOFT_QUALITY_GATES"] = self._saved

    def test_real_speech_passes_hard_gates(self):
        out = {}
        with _quiet():
            info = R.gate_audio(self.speech, self.sr, quality_out=out)
        self.assertIn("snr_db", info)
        self.assertIs(out["quality_info"], info)

    def test_hard_gates_reject_with_the_exact_message(self):
        # Mocked reports, because the legacy analyzer measures 60 dB SNR and 0% silence on
        # all-zero audio, so real silence never reaches the hard SNR or silence gates.
        # setUp set WWAI_SOFT_QUALITY_GATES=0, so these are the hard gates.
        cases = [
            ("low SNR", 2.0, 0.0, 0.0,
             "It was too noisy to hear the words clearly. Try somewhere quieter, "
             "or hold the device a little closer."),
            ("clipping", 20.0, 12.34, 0.0,
             "That recording came out too loud and fuzzy. Try reading a little softer, "
             "or hold the device a bit farther away."),
            ("silence", 20.0, 0.0, 90.0,
             "We could barely hear you. Read the sentence out loud, close to the microphone."),
        ]
        for gate, snr_db, clipping, silence, expected in cases:
            with self.subTest(gate=gate):
                report = {"quality_level": "poor", "quality_score": 10.0, "snr_db": snr_db,
                          "clipping_percentage": clipping, "silence_percentage": silence,
                          "issues": [], "recommendations": []}
                with mock.patch.object(R.AudioQualityAnalyzer, "analyze_audio_quality", return_value=report), \
                     _quiet(), self.assertRaises(R.AudioRejected) as ctx:
                    R.gate_audio(self.speech, self.sr)
                self.assertEqual(str(ctx.exception), expected)

    def test_digital_silence_rejected_by_soft_gates(self):
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "1"
        with _quiet(), self.assertRaises(R.AudioRejected):
            R.gate_audio(np.zeros(32000, dtype=np.float32), 16000)

    def test_soft_gates_are_the_default(self):
        # A report the hard gates would refuse (2 dB SNR) only gets a warning when the flag is unset.
        os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        report = {"quality_level": "poor", "quality_score": 10.0, "snr_db": 2.0,
                  "clipping_percentage": 0.0, "silence_percentage": 0.0,
                  "issues": [], "recommendations": []}
        out = {}
        with mock.patch.object(R.AudioQualityAnalyzer, "analyze_audio_quality", return_value=report), _quiet():
            self.assertIs(R.gate_audio(self.speech, self.sr, quality_out=out), report)
        self.assertIn("quality_warning", out)

    def test_rejection_is_a_value_error(self):
        self.assertTrue(issubclass(R.AudioRejected, ValueError))

    def test_gate_and_preprocess_runs_the_production_pass(self):
        from core.audio_preprocessing import preprocess_audio

        with _quiet():
            out = R.gate_and_preprocess(self.speech, self.sr)
            direct = preprocess_audio(self.speech, sr=self.sr, audio_length_seconds=len(self.speech) / self.sr,
                                      use_adaptive=True, already_preprocessed=False)
        self.assertTrue(np.array_equal(out, direct))
        self.assertAlmostEqual(float(np.max(np.abs(out))), 1.0, places=5)
        self.assertLessEqual(len(out), len(self.speech))  # preprocessing trims edge audio

    def test_apply_gates_false_skips_the_gates(self):
        with mock.patch.object(R, "gate_audio") as gate, _quiet():
            R.gate_and_preprocess(self.speech, self.sr, apply_gates=False)
        gate.assert_not_called()


class TestSpeechActivity(unittest.TestCase):
    """check_speech_activity is the handler's second gate, on the preprocessed recording."""

    HINT = "We had trouble hearing all the words - try speaking a little louder."
    MESSAGE = "We could barely hear you. Read the sentence out loud, close to the microphone."

    def setUp(self):
        # Soft gates are the default, so the hard gates have to be asked for.
        self._saved = os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "0"
        self.audio = np.zeros(16000, dtype=np.float32)

    def tearDown(self):
        os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        if self._saved is not None:
            os.environ["WWAI_SOFT_QUALITY_GATES"] = self._saved

    @staticmethod
    def _measured(value):
        # estimate_speech_activity is imported inside the function, so patch its home module.
        return mock.patch("core.audio_chunking.estimate_speech_activity", return_value=value)

    def test_hard_gates_reject_low_speech_with_the_exact_message(self):
        with self._measured(20.0), _quiet(), self.assertRaises(R.AudioRejected) as ctx:
            R.check_speech_activity(self.audio, {})
        self.assertEqual(str(ctx.exception), self.MESSAGE)

    def test_soft_gates_warn_instead_of_rejecting(self):
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "1"
        out = {}
        with self._measured(20.0), _quiet():
            result = R.check_speech_activity(self.audio, out)
        self.assertEqual(result, 20.0)
        self.assertIn(self.HINT, out["quality_warning"]["hints"])
        self.assertEqual(out["quality_warning"]["speech_activity_percentage"], 20.0)

    def test_soft_gates_keep_an_existing_warning(self):
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "1"
        out = {"quality_warning": {"hints": ["Try somewhere quieter."]}}
        with self._measured(20.0), _quiet():
            R.check_speech_activity(self.audio, out)
        self.assertEqual(out["quality_warning"]["hints"], ["Try somewhere quieter.", self.HINT])

    def test_soft_gates_work_without_quality_out(self):
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "1"
        with self._measured(20.0), _quiet():
            self.assertEqual(R.check_speech_activity(self.audio), 20.0)

    def test_low_speech_only_warns_by_default(self):
        os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        out = {}
        with self._measured(20.0), _quiet():
            self.assertEqual(R.check_speech_activity(self.audio, out), 20.0)
        self.assertIn(self.HINT, out["quality_warning"]["hints"])

    def test_enough_speech_passes_in_both_modes_and_leaves_quality_out_alone(self):
        for soft in (False, True):
            with self.subTest(soft=soft):
                os.environ["WWAI_SOFT_QUALITY_GATES"] = "1" if soft else "0"
                out = {}
                with self._measured(45.0), _quiet():
                    self.assertEqual(R.check_speech_activity(self.audio, out), 45.0)
                self.assertEqual(out, {})


class TestHandlerMarksItsPass(unittest.TestCase):
    """The real handler must still mark its preprocessing pass on the event loop.

    asyncio.to_thread runs gate_and_preprocess on a copy of the context. If a future edit
    moved mark_preprocessed() in there, the mark would be silently discarded and later
    stages would preprocess the recording a second time, with nothing else failing.
    """

    @classmethod
    def setUpClass(cls):
        # Same import pattern as TestHandlerGates in test_soft_quality_gates.py.
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        try:
            from routers.handlers.audio_processing_handler import load_and_preprocess_audio_bytes
        except ImportError as exc:
            raise unittest.SkipTest(f"audio_processing_handler not importable ({exc})") from exc
        cls.load = staticmethod(load_and_preprocess_audio_bytes)

    def test_handler_marks_its_preprocessing_pass(self):
        from core.audio_preprocessing import is_marked_preprocessed

        with open(SAMPLE_WAV, "rb") as fh:
            wav_bytes = fh.read()

        async def run():
            arr, _ = await self.load(wav_bytes, "sample.wav", "audio/wav", session_id="test-session")
            return is_marked_preprocessed(arr)  # must be checked inside the same task

        with mock.patch.dict(os.environ, {"WWAI_SINGLE_PREPROCESS": "1"}), _quiet():
            self.assertTrue(asyncio.run(run()))


class TestHandlerErrorMessages(unittest.TestCase):
    """What a child is told when analyze_audio_file_event_stream fails after preprocessing."""

    FRIENDLY = "We couldn't hear the words clearly. Read the sentence out loud, close to the microphone."
    GENERIC = "Something went wrong while checking your reading. Please try again."

    @classmethod
    def setUpClass(cls):
        # Same import pattern as TestHandlerMarksItsPass above.
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        try:
            from routers.handlers import audio_processing_handler as handler
        except ImportError as exc:
            raise unittest.SkipTest(f"audio_processing_handler not importable ({exc})") from exc
        cls.handler = handler

    def _stream(self, error):
        """Run the stream with the server analysis raising ``error``. Returns (events, stdout)."""
        import json
        from types import SimpleNamespace

        class FakeAssistant:
            word_extractor = None

            async def process_audio(self, *_args, **_kwargs):
                raise error

        async def fake_load(*_args, **_kwargs):
            return np.ones(16000, dtype=np.float32), "cache-id"

        async def collect():
            return [chunk async for chunk in self.handler.analyze_audio_file_event_stream(
                phoneme_assistant=FakeAssistant(), activity_object=None,
                audio_bytes=b"x", audio_filename="a.wav", audio_content_type="audio/wav",
                attempted_sentence="the cat sat", db=None, current_user=SimpleNamespace(id=1),
                session=SimpleNamespace(id=7),
            )]

        out = io.StringIO()
        with mock.patch.object(self.handler, "load_and_preprocess_audio_bytes", fake_load),              mock.patch.object(self.handler, "check_speech_activity", return_value=80.0),              contextlib.redirect_stdout(out):
            chunks = asyncio.run(collect())
        events = [json.loads(c[len("data: "):]) for c in chunks if c.startswith("data: ")]
        return events, out.getvalue()

    def _error_message(self, events):
        errors = [e for e in events if e["type"] == "error"]
        self.assertEqual(len(errors), 1, events)
        self.assertEqual(events[-1]["type"], "error")
        return errors[0]["data"]["message"]

    def test_no_speech_gets_a_kind_instruction(self):
        for text in ("The audio provided has no speech inside", "No valid words extracted from audio"):
            with self.subTest(error=text):
                events, log = self._stream(ValueError(text))
                self.assertEqual(self._error_message(events), self.FRIENDLY)
                self.assertIn(text, log)  # the original still reaches the log

    @staticmethod
    def _extractor_errors():
        """The errors both phoneme extractors raise for a too-short and a silent recording."""
        from types import SimpleNamespace
        from core.phoneme_extractor import PhonemeExtractor
        from core.phoneme_extractor_onnx import PhonemeExtractorONNX

        errors = []
        for validate in (PhonemeExtractorONNX.extract_logits, PhonemeExtractor.extract_phoneme):
            for audio in (np.zeros(1000, dtype=np.float32), np.zeros(16000, dtype=np.float32)):
                try:
                    validate(SimpleNamespace(_performance_logging=False), audio, 16000)
                except ValueError as exc:
                    errors.append(exc)
        return errors

    def test_silent_or_too_short_recordings_get_a_kind_instruction(self):
        errors = self._extractor_errors()
        self.assertEqual(len(errors), 4)
        self.assertEqual(sum("Audio too short" in str(e) for e in errors), 2)
        self.assertEqual(sum("Audio appears to be silent" in str(e) for e in errors), 2)
        for error in errors:
            with self.subTest(error=str(error)):
                events, log = self._stream(error)
                self.assertEqual(self._error_message(events), self.FRIENDLY)
                self.assertIn(str(error), log)  # the original still reaches the log

    def test_other_errors_keep_the_generic_message(self):
        for error in (ValueError("something else broke"), RuntimeError("The audio provided has no speech inside?"),
                      RuntimeError("❌ Audio too short (0.06s) - need at least 0.3s")):
            with self.subTest(error=repr(error)):
                events, log = self._stream(error)
                self.assertEqual(self._error_message(events), self.GENERIC)
                self.assertIn(str(error), log)

    def test_http_errors_keep_their_own_message(self):
        from fastapi import HTTPException

        events, _log = self._stream(HTTPException(status_code=400, detail="Try a shorter sentence."))
        self.assertEqual(self._error_message(events), "Try a shorter sentence.")


class TestHandlerClientGroundTruth(unittest.TestCase):
    """The client phoneme branch builds its ground truth the way the server path does."""

    @classmethod
    def setUpClass(cls):
        # Same import pattern as TestHandlerMarksItsPass above.
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        try:
            from routers.handlers import audio_processing_handler as handler
        except ImportError as exc:
            raise unittest.SkipTest(f"audio_processing_handler not importable ({exc})") from exc
        cls.handler = handler

    def _client_ground_truth(self, sentence, client_phonemes, client_words):
        """Run the stream down the client branch and return the ground truth it scored against."""
        from types import SimpleNamespace

        seen = {}

        async def fake_client_scoring(**kwargs):
            seen.update(kwargs)
            raise RuntimeError("stop here")

        async def fake_load(*_args, **_kwargs):
            return np.ones(16000, dtype=np.float32), "cache-id"

        async def collect():
            return [chunk async for chunk in self.handler.analyze_audio_file_event_stream(
                phoneme_assistant=SimpleNamespace(word_extractor=None), activity_object=None,
                audio_bytes=b"x", audio_filename="a.wav", audio_content_type="audio/wav",
                attempted_sentence=sentence, db=None, current_user=SimpleNamespace(id=1),
                session=SimpleNamespace(id=7), client_phonemes=client_phonemes, client_words=client_words,
            )]

        with mock.patch.object(self.handler, "load_and_preprocess_audio_bytes", fake_load), \
                mock.patch.object(self.handler, "check_speech_activity", return_value=80.0), \
                mock.patch.object(self.handler, "process_audio_with_client_phonemes", fake_client_scoring), \
                _quiet():
            asyncio.run(collect())
        return seen["ground_truth_phonemes"]

    def test_the_sentence_is_cleaned_before_g2p(self):
        from core.grapheme_to_phoneme import clean_sentence, grapheme_to_phoneme

        for sentence in ("The cat sat.", "Is it the CAT, or the dog?", "  The dog's toy!  "):
            with self.subTest(sentence=sentence):
                truth = self._client_ground_truth(
                    sentence, [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]], ["the", "cat", "sat"])
                # What PhonemeAssistant.process_audio builds for the server path.
                self.assertEqual(truth, grapheme_to_phoneme(clean_sentence(sentence)))
                self.assertEqual([w for w, _ in truth], clean_sentence(sentence).split())
                for _word, phonemes in truth:
                    self.assertFalse(set(phonemes) & set(".,?!'"), truth)

    def test_hybrid_mode_cleans_it_too(self):
        from core.grapheme_to_phoneme import clean_sentence, grapheme_to_phoneme

        truth = self._client_ground_truth("The cat sat.", [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]], None)
        self.assertEqual(truth, grapheme_to_phoneme(clean_sentence("The cat sat.")))


class TestHandlerFullClientWithoutAudio(unittest.TestCase):
    """The frontend sends an empty recording whenever it has client phonemes and client words.

    That includes client_words == [] when the browser's ASR heard nothing. The real handler
    and the real scoring must still score the reading instead of failing on the empty audio.
    """

    GROUPS = [["ð", "ə"], ["t", "æ", "t"], ["s", "æ", "t"]]   # "the cat sat" read as "the tat sat"

    @classmethod
    def setUpClass(cls):
        # Same import pattern as TestHandlerMarksItsPass above.
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        try:
            from routers.handlers import audio_processing_handler as handler
        except ImportError as exc:
            raise unittest.SkipTest(f"audio_processing_handler not importable ({exc})") from exc
        cls.handler = handler

    def _events(self, client_phonemes, client_words, db=None):
        """The stream's events. Without ``db`` the feedback entry is not stored."""
        import base64
        import json
        from types import SimpleNamespace

        class FakeActivity:
            async def get_next_sentence(self, **_kwargs):
                return {"sentence": "The dog ran."}

        assistant = SimpleNamespace(
            word_extractor=None,
            feedback_to_audio=lambda _text, _ssml=None: {
                "data": base64.b64encode(b"mp3").decode(), "filename": "f.mp3", "mimetype": "audio/mpeg"},
        )

        async def collect():
            return [chunk async for chunk in self.handler.analyze_audio_file_event_stream(
                phoneme_assistant=assistant, activity_object=FakeActivity(),
                audio_bytes=b"", audio_filename="empty.wav", audio_content_type="audio/wav",
                attempted_sentence="The cat sat.", db=db, current_user=SimpleNamespace(id=1),
                session=SimpleNamespace(id=7), client_phonemes=client_phonemes, client_words=client_words,
            )]

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.dict(os.environ))
            if db is None:
                stack.enter_context(mock.patch.object(self.handler, "create_feedback_entry"))
            stack.enter_context(mock.patch.object(self.handler.audio_cache, "save_feedback_audio"))
            stack.enter_context(_quiet())
            os.environ.pop("WWAI_GT_ANCHORED_ALIGNMENT", None)
            chunks = asyncio.run(collect())
        return [json.loads(c[len("data: "):]) for c in chunks if c.startswith("data: ")]

    @staticmethod
    def _column(df, name):
        return [df[name][k] for k in sorted(df[name], key=int)]

    def test_each_word_carries_its_clear_mistake_decision(self):
        # "the cat sat" read as "the dog sat": three wrong sounds in "cat" is a clear mistake,
        # the one wrong sound in "tat" is not.
        for groups, expected in (([["ð", "ə"], ["d", "ɔ", "g"], ["s", "æ", "t"]], [False, True, False]),
                                 (self.GROUPS, [False, False, False])):
            with self.subTest(groups=groups):
                events = self._events(groups, ["the", "cat", "sat"])
                df = next(e for e in events if e["type"] == "analysis")["data"]["pronunciation_dataframe"]
                self.assertEqual(self._column(df, "clear_mistake"), expected)
                self.assertIn("per", df)  # the existing columns are still there

    def test_the_new_column_is_stored_with_the_feedback_entry(self):
        # A throwaway in-memory database, never the app's configured one.
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import models
        from database import Base

        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        self.addCleanup(engine.dispose)
        self.addCleanup(db.close)

        events = self._events([["ð", "ə"], ["d", "ɔ", "g"], ["s", "æ", "t"]], ["the", "cat", "sat"], db=db)
        self.assertNotIn("error", [e["type"] for e in events], events)
        entries = db.query(models.FeedbackEntry).all()
        self.assertEqual(len(entries), 1)
        stored = entries[0].phoneme_analysis["pronunciation_dataframe"]
        self.assertEqual(self._column(stored, "clear_mistake"), [False, True, False])

    def test_an_empty_transcript_without_audio_is_scored(self):
        events = self._events(self.GROUPS, [])
        types = [e["type"] for e in events]
        self.assertNotIn("error", types, events)
        self.assertIn("analysis", types)
        self.assertEqual(next(e for e in events if e["type"] == "processing_mode")["data"]["mode"], "client")
        df = next(e for e in events if e["type"] == "analysis")["data"]["pronunciation_dataframe"]
        words = [df["ground_truth_word"][k] for k in sorted(df["ground_truth_word"], key=int)]
        self.assertEqual(words, ["the", "cat", "sat"])
        errors = [df["total_errors"][k] for k in sorted(df["total_errors"], key=int)]
        self.assertEqual(errors, [0, 1, 0])

    def test_too_few_phonemes_without_audio_is_no_speech(self):
        events = self._events([["ð"]], [])
        self.assertEqual(events[-1]["type"], "error")
        self.assertEqual(events[-1]["data"]["message"], self.handler.NO_SPEECH_MESSAGE)


if __name__ == "__main__":
    unittest.main()
