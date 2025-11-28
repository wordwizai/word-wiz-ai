import base64
import io
import json
import logging
import os
import re

import pandas as pd
import soundfile as sf
import torch
from core.grapheme_to_phoneme import grapheme_to_phoneme
from core.optimization_config import config
from dotenv import load_dotenv
from openai import OpenAI

from .audio_validation import log_audio_characteristics, validate_audio_output
from .phoneme_extractor import PhonemeExtractor
from .phoneme_extractor_onnx import PhonemeExtractorONNX
from .process_audio import analyze_results, process_audio_array
from .text_to_audio import ElevenLabsAPIClient, GoogleTTSAPIClient
from .word_extractor import WordExtractor, WordExtractorOnline

# Configure logging
logger = logging.getLogger(__name__)


class PhonemeAssistant:
    def __init__(self, use_optimized_model: bool = None):
        # Load the API keys and environment variables
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Check if GPU is available and set the device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            print("Using GPU for processing.")
        else:
            self.device = torch.device("cpu")
            print("Using CPU for processing.")

        # Use all available CPU cores for better performance
        num_cores = os.cpu_count() or 4
        torch.set_num_threads(num_cores)
        torch.set_num_interop_threads(num_cores)
        print(f"Using {num_cores} CPU threads for PyTorch inference")

        # Determine optimization settings from environment or parameter
        if use_optimized_model is None:
            use_optimized_model = config.get('use_optimized_model', True)

        # Check if we should use ONNX Runtime (faster)
        use_onnx = os.getenv("USE_ONNX_BACKEND", "true").lower() == "true"
        
        # Load optimized models for better performance
        if use_onnx:
            print("Initializing ONNX-based PhonemeExtractor for faster inference...")
            try:
                self.phoneme_extractor = PhonemeExtractorONNX()
                print("✅ ONNX Runtime backend loaded successfully")
            except Exception as e:
                print(f"⚠️  ONNX loading failed ({e}), falling back to PyTorch")
                self.phoneme_extractor = PhonemeExtractor()
        elif use_optimized_model:
            print("Initializing optimized PyTorch PhonemeExtractor...")
            if config.get('enable_performance_logging', False):
                print(config.summary())
            self.phoneme_extractor = PhonemeExtractor()
        else:
            print("Using standard PhonemeExtractor...")
            self.phoneme_extractor = PhonemeExtractor(
                use_quantization=False,
                use_fast_model=False
            )
            
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

        # load in our prompt

    def load_prompt(self, prompt_path: str) -> str:
        # Always resolve prompt_path relative to backend root
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resolved_prompt_path = (
            prompt_path if os.path.isabs(prompt_path)
            else os.path.join(backend_root, prompt_path)
        )
        with open(resolved_prompt_path, encoding="utf-8") as file:
            lines = file.readlines()
            content = [
                line for line in lines if not line.strip().startswith("//")
            ]
            text = "".join(content)

        # Automatically append SSML instruction to all prompts
        ssml_instruction_rel = "core/gpt_prompts/ssml_instruction.txt"
        ssml_instruction_path = os.path.join(backend_root, ssml_instruction_rel)
        try:
            with open(ssml_instruction_path, encoding="utf-8") as ssml_file:
                ssml_lines = ssml_file.readlines()
                ssml_content = [
                    line for line in ssml_lines if not line.strip().startswith("//")
                ]
                ssml_text = "".join(ssml_content)
                text += "\n\n" + ssml_text
        except FileNotFoundError:
            # If SSML instruction file is missing, continue without it
            pass
        
        return text

    def extract_json(self, response_text):
        """
        Extracts a JSON object from a given response text.

        This method uses a regular expression to search for the first JSON object
        (delimited by curly braces) within the response text. If found, it attempts
        to parse and return the JSON object as a Python dictionary. If no JSON object
        is found, or if decoding fails, a ValueError is raised.

        Args:
            response_text (str): The text containing the JSON object.

        Returns:
            dict: The extracted JSON object.

        Raises:
            ValueError: If no JSON object is found or if decoding fails.
        """
        try:
            # Use regex to find the JSON object in the response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_content = json_match.group(0)
                return json.loads(json_content)
            else:
                raise ValueError("No JSON object found in the response.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

    def query_gpt(self, conversation_history: list) -> str:
        """Queries the GPT model with the conversation history and returns the response.

        Args:
            conversation_history (list): List of messages in the conversation.

        Returns:
            str: The response from the GPT model.
        """

        # Convert messages to the expected format for OpenAI API
        def to_chat_message(msg):
            if isinstance(msg["content"], list):
                return {"role": msg["role"], "content": msg["content"]}
            else:
                return {
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}],
                }

        formatted_messages = [to_chat_message(m) for m in conversation_history]

        # Get the response from the model
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=formatted_messages,
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        model_response = response.choices[0].message.content
        if model_response is not None:
            model_response = model_response.strip()
        else:
            model_response = ""

        return model_response

    # def get_gpt_feedback(
    #     self,
    #     attempted_sentence: str,
    #     pronunciation_data: dict,
    #     highest_per_word_data: dict,
    #     problem_summary: dict,
    #     per_summary: dict,
    # ) -> dict[str, str]:
    #
    #     temp_messages = self.conversation_history[:]
    #     temp_messages.append(user_input)
    #
    #     # Add the user input to the conversation history
    #     self.conversation_history.append(
    #         {"role": "user", "content": (f"{problem_summary}")}
    #     )
    #
    #     # Convert messages to the expected format for OpenAI API
    #     def to_chat_message(msg):
    #         # Convert dict to OpenAI chat message format if needed
    #         if isinstance(msg["content"], list):
    #             return {"role": msg["role"], "content": msg["content"]}
    #         else:
    #             return {
    #                 "role": msg["role"],
    #                 "content": [{"type": "text", "text": msg["content"]}],
    #             }
    #
    #     formatted_messages = [to_chat_message(m) for m in temp_messages]
    #
    #     # Get the response from the model
    #     response = self.client.chat.completions.create(
    #         model="gpt-4o-mini",
    #         messages=formatted_messages,
    #         temperature=1,
    #         max_tokens=2048,
    #         top_p=1,
    #         frequency_penalty=0,
    #         presence_penalty=0,
    #         stop=["</ANSWER>"],
    #     )
    #
    #     model_response = response.choices[0].message.content
    #     if model_response is not None:
    #         model_response = model_response.strip()
    #     else:
    #         model_response = ""
    #     self.conversation_history.append(
    #         {"role": "assistant", "content": model_response}
    #     )
    #     print(model_response)
    #
    #     return self.extract_json(model_response)

    async def process_audio(
        self, attempted_sentence, audio_array, verbose=False, status_callback=None
    ):
        """Record or process specific audio and get the model's response.

        Args:
            attempted_sentence (str): The sentence to analyze.
            verbose (bool, optional): Whether to print detailed logs. Defaults to False.
            status_callback (callable, optional): Callback for status updates. Defaults to None.
            audio_path (str, optional): Path to a specific audio file to process. Defaults to None.

        Returns:
            tuple: Model response, DataFrame, highest_per_word, problem_summary, per_summary.
        """

        # Use the provided audio file
        if status_callback:
            status_callback("Loading audio from file...")

        # clean the sentence
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
        """Generate feedback audio using Google TTS service and return as base64-encoded file

        Args:
            feedback (str): string of feedback to be converted to audio (plain text fallback)
            feedback_ssml (str, optional): SSML version of feedback for better pronunciation
            save (bool, optional): Whether to save the audio. Defaults to False.
            save_path (str, optional): Path to save the audio. Defaults to "temp_audio/feedback.wav".

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

        # Target sample rate for consistent mobile playback (24kHz is standard for TTS)
        TARGET_SAMPLE_RATE = 24000

        audio_buffer = io.BytesIO()
        try:
            import librosa
            import numpy as np

            # Properly decode MP3 audio first using librosa
            # This handles the MP3 format correctly instead of treating it as raw PCM
            audio_array, original_sr = librosa.load(
                io.BytesIO(audio_bytes), 
                sr=None,  # Keep original sample rate initially
                mono=True
            )
            
            # Resample to target sample rate if needed
            if original_sr != TARGET_SAMPLE_RATE:
                audio_array = librosa.resample(
                    audio_array, 
                    orig_sr=original_sr, 
                    target_sr=TARGET_SAMPLE_RATE
                )
            
            # Normalize audio to prevent clipping
            audio_array = librosa.util.normalize(audio_array)
            
            # Write as WAV with explicit format (PCM 16-bit for maximum compatibility)
            sf.write(
                audio_buffer, 
                audio_array, 
                TARGET_SAMPLE_RATE, 
                format='WAV', 
                subtype='PCM_16'
            )
            
        except Exception as e:
            print(f"Audio processing error: {str(e)}")
            print(f"Attempting fallback conversion...")
            # Fallback: try to write directly as WAV (may not work properly but better than nothing)
            try:
                import numpy as np
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                sf.write(audio_buffer, audio_array, TARGET_SAMPLE_RATE, format="WAV", subtype='PCM_16')
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
                # Last resort: just write the raw bytes
                audio_buffer.write(audio_bytes)

        audio_buffer.seek(0)
        audio_bytes_final = audio_buffer.read()
        
        # Validate and log audio characteristics before sending
        is_valid, validation_info = validate_audio_output(audio_bytes_final)
        
        if not is_valid:
            logger.warning(f"Audio validation failed: {validation_info['errors']}")
        
        if validation_info.get('warnings'):
            logger.info(f"Audio validation warnings: {validation_info['warnings']}")
        
        # Log audio characteristics for debugging
        log_audio_characteristics(audio_bytes_final, context="TTS feedback")
        
        audio_b64 = base64.b64encode(audio_bytes_final).decode("utf-8")

        return {"filename": "feedback.wav", "mimetype": "audio/wav", "data": audio_b64}


# Default running behavior
# if __name__ == "__main__":
#
#     # DEFAULT BEHAVIOR:
#     # - MAKE MODEL
#     # - GETS SENTENCE FROM USER
#     # - LOOP
#
#     # AI models
#     phoneme_assistant = PhonemeAssistant()
#
#     print("Welcome to the Phonics Assistant! Let's get started.")
#
#     attempted_sentence = input("Enter sentence to start with: ").lower()
#
#     # user loop
#     while True:
#         output,_,_,_,_ = phoneme_assistant.process_audio(attempted_sentence, verbose=True)
#
#         output_json = output
#         print("\nFeedback: ")
#         print(output_json['feedback'])
#
#         print("\n New sentence to say: ")
#         print(output_json['sentence'])
#
#         attempted_sentence = output_json['sentence'].replace(".", "").lower()
#
#         audio_feedback = f'{output_json["feedback"]}'
#         phoneme_assistant.feedback_to_audio(audio_feedback, save=True)
#         phoneme_assistant.play_audio(phoneme_assistant.load_audio("temp_audio/feedback.wav"))
#
#         if input("Do you want to continue? (yes/no): ") != "yes":
#             break
