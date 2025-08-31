# %%
import torch
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import re
import os
import io
import numpy as np
import google.cloud.speech as speech


def default_model_output_processing(transcription):
    # Filter out our transcription
    filtered_transcription = transcription[0]

    # Remove punctuation and convert to lowercase
    filtered_transcription = re.sub(r"[\W_]+", " ", filtered_transcription).lower()

    # Split by words
    filtered_transcription = filtered_transcription.split()

    return filtered_transcription


class WordExtractor:
    def __init__(
        self,
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-english",
        model_output_processing=default_model_output_processing,
    ):
        # Replace with your pre-trained phoneme model identifier from Hugging Face
        self.model_name = model_name
        # Load the phoneme tokenizer and model
        self.processor = Wav2Vec2Processor.from_pretrained(
            self.model_name,
        )

        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)

        self.blank_token_id = self.processor.tokenizer.pad_token_id  # for CTC loss

        self.model_output_processing = model_output_processing

    def extract_words(self, audio, sampling_rate=16000):
        # Load the audio file
        # Tokenize the audio file
        input_values = self.processor(
            audio, sampling_rate=sampling_rate, return_tensors="pt"
        ).input_values
        # retrieve logits from the model
        with torch.no_grad():
            logits = self.model(input_values).logits

        # take the probs
        probs = torch.softmax(logits, dim=-1)
        top2_probs, top2_ids = torch.topk(probs, k=2, dim=-1)

        # take argmax and decode, greedy decoding
        predicted_ids = torch.argmax(logits, dim=-1)

        # Decode the collapsed token sequences to get phoneme transcription strings
        # (The tokenizer's decode method will convert token ids to phoneme symbols)
        transcription = self.processor.batch_decode(predicted_ids)
        transcription = self.model_output_processing(
            transcription
        )  # convert and filter our output

        return transcription


class WordExtractorOnline:
    def __init__(self, model_output_processing=default_model_output_processing):
        """
        Initialize Google Cloud Speech-to-Text client.
        Requires GOOGLE_APPLICATION_CREDENTIALS environment variable to be set.
        """
        # Set up Google Cloud credentials
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        # Initialize the Speech-to-Text client
        self.client = speech.SpeechClient()
        self.model_output_processing = model_output_processing

    def extract_words(self, audio, sampling_rate=16000):
        """
        Extract words from audio using Google Cloud Speech-to-Text API.

        Args:
            audio: numpy array of audio data or bytes
            sampling_rate: sampling rate of the audio (default: 16000)

        Returns:
            List of words extracted from the audio
        """
        try:
            # Convert numpy array to bytes if needed
            if isinstance(audio, np.ndarray):
                # Normalize audio to [-1, 1] range if not already
                if np.max(np.abs(audio)) > 1.0:
                    audio = audio / np.max(np.abs(audio))

                # Ensure audio is in the correct format (16-bit PCM)
                audio_int16 = (audio * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
            else:
                audio_bytes = audio

            # Validate audio length (Google Cloud has limits)
            if len(audio_bytes) == 0:
                print("Warning: Empty audio data received")
                return []

            # Configure the audio settings
            audio_config = speech.RecognitionAudio(content=audio_bytes)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sampling_rate,
                language_code="en-US",
                # Enable automatic punctuation for better word separation
                enable_automatic_punctuation=True,
            )
            print("Sending audio data to Google Cloud for transcription...")

            # Perform the transcription
            response = self.client.recognize(config=config, audio=audio_config)

            # Extract transcription from response
            transcriptions = []
            for result in response.results:
                if result.alternatives:
                    transcriptions.append(result.alternatives[0].transcript)
            print(f"Transcription results: {transcriptions}")

            # If no transcription found, return empty list
            if not transcriptions:
                print("Warning: No transcription results found")
                return []

            # Combine multiple transcription results if present
            combined_transcription = " ".join(transcriptions)

            # Process the transcription to match WordExtractor output format
            transcription = self.model_output_processing([combined_transcription])

            return transcription

        except Exception as e:
            print(f"Error during Google Cloud transcription: {e}")
            return []


# if __name__ == '__main__':
#     from grapheme_to_phoneme import grapheme_to_phoneme
#     from audio_recording import record_and_process_pronunciation
#
#     # Load the audio file
#     audio, sampling_rate = librosa.load("./temp_audio/output.wav", sr=16000)
#     # Create the phoneme extractor
#     extractor = WordExtractor()
#
#     # Extract the phonemes
#     phonemes = extractor.extract_words(audio, sampling_rate)
#     ground_truth_phonemes = grapheme_to_phoneme("zero three five one")
#     # phonemes, ground_truth_phonemes = record_and_process_pronunciation("the quick brown fox jumped over the lazy dog", extractor)
#
#     print(phonemes)
#     print(ground_truth_phonemes)
