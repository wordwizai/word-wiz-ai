# %%
import torch
import asyncio
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import re
import os
import numpy as np


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

    async def extract_words(self, audio, sampling_rate=16000):
        # Load the audio file
        # Tokenize the audio file
        input_values = self.processor(
            audio, sampling_rate=sampling_rate, return_tensors="pt"
        ).input_values
        # Simulating asynchronous work for I/O-bound tasks
        await asyncio.sleep(0)  # Placeholder for real async I/O calls

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
        Initialize Deepgram Speech-to-Text client.
        Requires DEEPGRAM_KEY environment variable to be set.
        """
        # Get Deepgram API key from environment
        self.api_key = os.getenv("DEEPGRAM_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_KEY environment variable is not set")
        
        self.model_output_processing = model_output_processing
        self.deepgram_url = "https://api.deepgram.com/v1/listen"

    def extract_words(self, audio, sampling_rate=16000, timeout=15, max_retries=2):
        """
        Extract words from audio using Deepgram Speech-to-Text API.

        Args:
            audio: numpy array of audio data or bytes
            sampling_rate: sampling rate of the audio (default: 16000)
            timeout: timeout in seconds for the API call (default: 15)
            max_retries: maximum number of retry attempts (default: 2)

        Returns:
            List of words extracted from the audio
        """
        import time
        import requests
        
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

        # Validate audio length
        if len(audio_bytes) == 0:
            print("⚠️  Warning: Empty audio data received")
            return []
        
        # Calculate audio duration for logging
        audio_duration = len(audio_bytes) / (sampling_rate * 2)  # 2 bytes per sample (16-bit)
        print(f"📤 Sending {audio_duration:.2f}s audio to Deepgram for transcription...")

        # Prepare headers
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }

        # Prepare query parameters
        params = {
            "model": "nova-2",
            "language": "en-US",
            "punctuate": "true",
            "smart_format": "true",
            "encoding": "linear16",
            "sample_rate": sampling_rate
        }

        # Retry loop
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 Retry attempt {attempt}/{max_retries} for word extraction...")
                    time.sleep(1 * attempt)  # Exponential backoff
                
                # Perform the transcription with timeout
                start_time = time.time()
                response = requests.post(
                    self.deepgram_url,
                    headers=headers,
                    params=params,
                    data=audio_bytes,
                    timeout=timeout
                )
                elapsed_time = time.time() - start_time
                
                # Check if request was successful
                response.raise_for_status()
                
                # Parse the JSON response
                result = response.json()
                
                print(f"✓ Deepgram transcription completed in {elapsed_time:.2f}s")

                # Extract transcription from response
                transcriptions = []
                if result.get("results") and result["results"].get("channels"):
                    for channel in result["results"]["channels"]:
                        if channel.get("alternatives"):
                            transcript = channel["alternatives"][0].get("transcript", "")
                            if transcript:
                                transcriptions.append(transcript)
                
                print(f"📝 Transcription results: {transcriptions}")

                # If no transcription found, return empty list
                if not transcriptions:
                    print("⚠️  Warning: No transcription results found")
                    return []

                # Combine multiple transcription results if present
                combined_transcription = " ".join(transcriptions)

                # Process the transcription to match WordExtractor output format
                transcription = self.model_output_processing([combined_transcription])

                return transcription

            except requests.exceptions.Timeout as e:
                last_error = e
                print(f"⏱️  Timeout after {timeout}s - audio may be too long or network is slow")
                if attempt == max_retries:
                    print(f"❌ All {max_retries + 1} attempts failed due to timeout")
                    return []
            
            except requests.exceptions.HTTPError as e:
                last_error = e
                print(f"❌ Deepgram API error: {e} - {response.text if 'response' in locals() else 'No response'}")
                if attempt == max_retries:
                    print(f"❌ All {max_retries + 1} attempts failed due to API error")
                    return []
            
            except Exception as e:
                last_error = e
                print(f"❌ Unexpected error during Deepgram transcription: {e}")
                if attempt == max_retries:
                    print(f"❌ All {max_retries + 1} attempts failed")
                    return []
        
        # Should not reach here, but just in case
        print(f"❌ Word extraction failed after {max_retries + 1} attempts: {last_error}")
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
