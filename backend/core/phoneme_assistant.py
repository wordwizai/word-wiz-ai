"""
Phoneme Assistant - Main pipeline orchestrator.

Coordinates the full pronunciation analysis pipeline: audio processing,
phoneme extraction, GPT feedback generation, and TTS response.
"""

import os
import torch
from dotenv import load_dotenv

from .audio_analysis import analyze_results
from .audio_encoder import feedback_to_audio_base64
from .gpt_client import GPTClient
from .grapheme_to_phoneme import grapheme_to_phoneme
from .logging_config import get_logger
from .optimization_config import config
from .phoneme_extractor import PhonemeExtractor
from .phoneme_extractor_onnx import PhonemeExtractorONNX
from .process_audio import process_audio_array
from .prompt_manager import PromptManager
from .text_to_audio import GoogleTTSAPIClient
from .word_extractor import WordExtractorOnline

logger = get_logger(__name__)


class PhonemeAssistant:
    """
    Main orchestrator for pronunciation analysis pipeline.

    Manages model initialization, audio processing, GPT feedback generation,
    and TTS audio response.
    """

    def __init__(self, use_optimized_model: bool = None):
        """
        Initialize PhonemeAssistant with ML models and API clients.

        Args:
            use_optimized_model: Whether to use optimized models (default: from config).
        """
        load_dotenv()

        # Initialize GPT client
        self.gpt_client = GPTClient(model="gpt-4o-mini")
        self.prompt_manager = PromptManager()

        # Check if GPU is available and set the device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            logger.info("Using GPU for processing")
        else:
            self.device = torch.device("cpu")
            logger.info("Using CPU for processing")

        # Use all available CPU cores for better performance
        num_cores = os.cpu_count() or 4
        torch.set_num_threads(num_cores)
        torch.set_num_interop_threads(num_cores)
        logger.info(f"Using {num_cores} CPU threads for PyTorch inference")

        # Determine optimization settings
        if use_optimized_model is None:
            use_optimized_model = config.get('use_optimized_model', True)

        # Initialize phoneme extractor (ONNX or PyTorch)
        use_onnx = os.getenv("USE_ONNX_BACKEND", "true").lower() == "true"

        if use_onnx:
            logger.info("Initializing ONNX-based PhonemeExtractor for faster inference")
            try:
                self.phoneme_extractor = PhonemeExtractorONNX()
                logger.info("ONNX Runtime backend loaded successfully")
            except Exception as e:
                logger.warning(f"ONNX loading failed ({e}), falling back to PyTorch")
                self.phoneme_extractor = PhonemeExtractor()
        elif use_optimized_model:
            logger.info("Initializing optimized PyTorch PhonemeExtractor")
            if config.get('enable_performance_logging', False):
                logger.debug(config.summary())
            self.phoneme_extractor = PhonemeExtractor()
        else:
            logger.info("Using standard PhonemeExtractor")
            self.phoneme_extractor = PhonemeExtractor(
                use_quantization=False,
                use_fast_model=False
            )

        # Initialize word extractor and TTS
        self.word_extractor = WordExtractorOnline()
        self.tts = GoogleTTSAPIClient()

    def get_performance_info(self) -> dict:
        """Get performance information about the current configuration."""
        model_info = self.phoneme_extractor.get_model_info()
        return {
            'device': str(self.device),
            'cuda_available': torch.cuda.is_available(),
            'model_info': model_info,
            'config_summary': config.summary()
        }

    def load_prompt(self, prompt_path: str) -> str:
        """
        Load a prompt from file.

        Args:
            prompt_path: Path to prompt file.

        Returns:
            str: Loaded prompt text.
        """
        return self.prompt_manager.load_prompt(prompt_path)

    def extract_json(self, response_text: str) -> dict:
        """
        Extract JSON object from GPT response text.

        Args:
            response_text: Text containing JSON object.

        Returns:
            dict: Extracted JSON object.
        """
        return self.gpt_client.extract_json(response_text)

    def query_gpt(self, conversation_history: list) -> str:
        """
        Query GPT model with conversation history.

        Args:
            conversation_history: List of messages in the conversation.

        Returns:
            str: GPT model response.
        """
        return self.gpt_client.query_gpt(conversation_history)

    async def process_audio(
        self, attempted_sentence, audio_array, verbose=False, status_callback=None
    ):
        """
        Process audio and get pronunciation analysis.

        Args:
            attempted_sentence: The sentence to analyze.
            audio_array: Audio signal as numpy array.
            verbose: Whether to print detailed logs.
            status_callback: Callback for status updates.

        Returns:
            tuple: (DataFrame, highest_per_word, problem_summary, per_summary).
        """
        if status_callback:
            status_callback("Loading audio from file...")

        # Clean the sentence
        attempted_sentence = (
            (attempted_sentence.strip().lower().replace(".", "").replace(",", ""))
            .replace("?", "")
            .replace("!", "")
            .replace("'", "")
        )

        ground_truth_phonemes = grapheme_to_phoneme(attempted_sentence)
        pronunciation_data = await process_audio_array(
            ground_truth_phonemes=ground_truth_phonemes,
            audio_array=audio_array,
            sampling_rate=16000,
            phoneme_extraction_model=self.phoneme_extractor,
            word_extraction_model=self.word_extractor,
        )

        if status_callback:
            status_callback("Analyzing results...")

        pronunciation_dataframe, highest_per_word, problem_summary, per_summary = (
            analyze_results(pronunciation_data)
        )

        if verbose:
            print("Dataframe: ")
            print(pronunciation_dataframe)
            print(f"Results: \n{pronunciation_data}")
            print(f"Highest error word: \n{highest_per_word}")
            print(f"Problem Summary \n{problem_summary}")
            print(f"PER Summary \n{per_summary}")

        return pronunciation_dataframe, highest_per_word, problem_summary, per_summary

    def feedback_to_audio(
        self,
        feedback: str,
        feedback_ssml: str = None,
    ) -> dict:
        """
        Generate feedback audio using TTS service and return as base64-encoded file.

        Args:
            feedback: Plain text feedback (fallback if no SSML).
            feedback_ssml: SSML version of feedback for better pronunciation.

        Returns:
            dict: {
                "filename": str,
                "mimetype": str,
                "data": str (base64-encoded)
            }
        """
        # Use SSML version if available, otherwise use plain text
        text_to_convert = feedback_ssml if feedback_ssml else feedback
        is_ssml = feedback_ssml is not None

        audio_generator = self.tts.getAudio(text_to_convert, is_ssml=is_ssml)
        audio_bytes = b"".join(audio_generator)

        return feedback_to_audio_base64(audio_bytes, target_sample_rate=24000)
