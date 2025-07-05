from typing import Iterator
from openai import OpenAI
from dotenv import load_dotenv

from ai.grapheme_to_phoneme import grapheme_to_phoneme
from .phoneme_extractor import PhonemeExtractor
from .word_extractor import WordExtractor
from .text_to_audio import ElevenLabsAPIClient
import os
import pandas as pd
from .audio_recording import record_and_process_pronunciation
from .process_audio import analyze_results, process_audio_array
import json
import re
import torch
import io
import base64
import soundfile as sf


class PhonemeAssistant:
    def __init__(self):
        # Load the API keys
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Check if GPU is available and set the device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            print("Using GPU for processing.")
        else:
            self.device = torch.device("cpu")
            print("Using CPU for processing.")

        # load the models
        self.phoneme_extractor = PhonemeExtractor()
        self.word_extractor = WordExtractor()
        self.tts = ElevenLabsAPIClient()

        # load in our prompt
        with open("ai/gpt_prompts/gpt_prompt_v2.txt") as file:
            lines = file.readlines()
            content = [
                line for line in lines if not line.strip().startswith("//")
            ]  # // is how we are going to comments in the txt file
            text = "".join(content)
            self.prompt = text
        self.reset_conversation_history()

    def reset_conversation_history(self):
        self.conversation_history = (
            [  # Reset conversation history to just be the initial system prompt
                {"role": "system", "content": [{"type": "text", "text": self.prompt}]}
            ]
        )

    def extract_json(self, response_text):
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

    def get_gpt_response(
        self,
        attempted_sentence: str,
        pronunciation_data: dict,
        highest_per_word_data: dict,
        problem_summary: dict,
        per_summary: dict,
        stream: bool = False,
    ) -> dict[str, str]:
        user_input = {
            "role": "user",
            "content": (
                "<<ATTEMPTED_SENTENCE>>\n"
                f"{attempted_sentence}"
                "<</ATTEMPTED_SENTENCE>>"
                "<<PER_SUMMARY>>\n"
                f"{per_summary}"
                "<</PER_SUMMARY>>"
                "<<PROBLEM_SUMMARY>>\n"
                f"{problem_summary}\n"
                "<</PROBLEM_SUMMARY>>\n\n"
                "<<PRONUNCIATION>>\n"
                f"{pronunciation_data}\n"
                "<</PRONUNCIATION>>\n\n"
                "<<HIGHEST_PER_WORD>>\n"
                f"{highest_per_word_data}\n"
                "<</HIGHEST_PER_WORD>>\n\n"
                "<<INSTRUCTIONS>>\n"
                "1. THINKING:\n"
                "   a. Review phoneme_error_counts to find the most frequent mispronounced phoneme.\n"
                "   b. If any count > 1, target that phoneme; else use highest_per_word substitution.\n"
                f"   c. sentence_per = {per_summary}; if ≤0.2 use advanced words, else simpler words.\n"
                "   d. Plan 20-30 word fully decodable sentence with varied phoneme positions, check the system prompt for the exact amount of words needed.\n"
                "   e. Plan feedback: compliment, explain phoneme issue, compliment.\n"
                "2. ANSWER in JSON using the earlier reasoning and the system prompt:\n"
                "Make sure to explain all of your thinking by responding to each of these thinking questions before giving your response in json\n"
                "<</INSTRUCTIONS>>"
            ),
        }

        temp_messages = self.conversation_history[:]
        temp_messages.append(user_input)

        # Add the user input to the conversation history
        self.conversation_history.append(
            {"role": "user", "content": (f"{problem_summary}")}
        )

        # Convert messages to the expected format for OpenAI API
        def to_chat_message(msg):
            # Convert dict to OpenAI chat message format if needed
            if isinstance(msg["content"], list):
                return {"role": msg["role"], "content": msg["content"]}
            else:
                return {
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}],
                }

        formatted_messages = [to_chat_message(m) for m in temp_messages]

        # Get the response from the model
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=formatted_messages,
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["</ANSWER>"],
        )

        model_response = response.choices[0].message.content
        if model_response is not None:
            model_response = model_response.strip()
        else:
            model_response = ""
        self.conversation_history.append(
            {"role": "assistant", "content": model_response}
        )
        print(model_response)

        return self.extract_json(model_response)

    def process_audio(
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

        ground_truth_phonemes = grapheme_to_phoneme(attempted_sentence)
        pronunciation_data = process_audio_array(
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
    ) -> dict:
        """Generate feedback audio using Elevenlabs TTS service and return as base64-encoded file

        Args:
            feedback (str): string of feedback to be converted to audio
            save (bool, optional): Whether to save the audio. Defaults to False.
            save_path (str, optional): Path to save the audio. Defaults to "temp_audio/feedback.wav".

        Returns:
            dict: {
                "filename": str,
                "mimetype": str,
                "data": str (base64-encoded)
            }
        """

        audio_generator = self.tts.getAudio(feedback)

        audio_bytes = b"".join(audio_generator)

        sample_rate = getattr(self.tts, "sample_rate", 22050)

        audio_buffer = io.BytesIO()
        try:
            import numpy as np
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            sf.write(audio_buffer, audio_array, sample_rate, format="WAV")
        except Exception:
            # fallback: just write the raw bytes if conversion fails
            audio_buffer.write(audio_bytes)

        audio_buffer.seek(0)
        audio_bytes_final = audio_buffer.read()
        audio_b64 = base64.b64encode(audio_bytes_final).decode("utf-8")

        return {
            "filename": "feedback.wav",
            "mimetype": "audio/wav",
            "data": audio_b64
        }

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
