#%%
from openai import OpenAI
import sounddevice as sd
import numpy as np
from dotenv import load_dotenv
from .phoneme_extractor import PhonemeExtractor
from .word_extractor import WordExtractor
from .text_to_audio import ElevenLabsAPIClient
from .audio_preprocessing import preprocess_audio
import os
import pandas as pd
from .audio_recording import record_and_process_pronunciation
from .process_audio import analyze_results
import json
import re
import torch

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
            content = [line for line in lines if not line.strip().startswith("//")] # // is how we are going to comments in the txt file
            text = "".join(content)
            self.prompt = text
        self.reset_conversation_history()

    
    def reset_conversation_history(self):
        self.conversation_history = [ # Reset conversation history to just be the initial system prompt
            {
                "role": "system",
                "content": [
                {
                    "type": "text",
                    "text": self.prompt
                    }
                ]
            }
        ]
    
    def getPhonemes(self, text):
        phonemes = self.client.text_to_phonemes.convert(
            text=text,
            voice_id="nPczCjzI2devNBz1zQrb",
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",)
        return phonemes

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

    def get_response(self, attempted_sentence:str, results:list, highest_per_word: pd.Series, problem_summary: dict, per_summary: dict) -> dict:
        # format the user input for our model
        # user_input = {
        #     "attempted_sentence": attempted_sentence,
        #     "per_summary": per_summary,
        #     "problem_summary": problem_summary,
        #     "pronunciation": results,
        #     "highest_per_word": highest_per_word.to_dict(),
        # }
        user_input = {"role": "user", "content": (
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
            f"{results}\n"
            "<</PRONUNCIATION>>\n\n"
            "<<HIGHEST_PER_WORD>>\n"
            f"{highest_per_word.to_dict()}\n"
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
        )}

        temp_messages = self.conversation_history[:]
        temp_messages.append(user_input)

        # add the user input to the conversation history
        self.conversation_history.append({
            "role": "user",
            "content": (f"{problem_summary}")
        })

        # get the response from the model
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=temp_messages,
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["</ANSWER>"]
        )
        
        model_response = response.choices[0].message.content.strip()
        self.conversation_history.append({
            "role": "assistant",
            "content": model_response})
        print(model_response)
        
        return self.extract_json(model_response)
    
    # def get_dataset_index_and_get_response(self):

    def record_audio_and_get_response(self, attempted_sentence, verbose=False, status_callback=None, audio_array=None):
        """Record or process specific audio and get the model's response.

        Args:
            attempted_sentence (str): The sentence to analyze.
            verbose (bool, optional): Whether to print detailed logs. Defaults to False.
            status_callback (callable, optional): Callback for status updates. Defaults to None.
            audio_path (str, optional): Path to a specific audio file to process. Defaults to None.

        Returns:
            tuple: Model response, DataFrame, highest_per_word, problem_summary, per_summary.
        """
        if audio_array is not None:
            # Use the provided audio file
            if status_callback:
                status_callback("Loading audio from file...")
            results, ground_truth_phonemes = record_and_process_pronunciation(
                attempted_sentence,
                phoneme_extraction_model=self.phoneme_extractor,
                word_extraction_model=self.word_extractor,
                audio_array=audio_array,
                status_callback=status_callback,
            )
        else:
            # Record audio
            recorded = False
            while not recorded:
                try:
                    results, ground_truth_phonemes = record_and_process_pronunciation(
                        attempted_sentence,
                        phoneme_extraction_model=self.phoneme_extractor,
                        word_extraction_model=self.word_extractor,
                        status_callback=status_callback,
                    )
                    recorded = True
                except ValueError:
                    print("No audio detected, you must speak again")

        if status_callback:
            status_callback("Analyzing results...")

        df, highest_per_word, problem_summary, per_summary = analyze_results(results)

        if verbose:
            print("Dataframe: ")
            print(df)
            print(f"Results: \n{results}")
            print(f"Highest error word: \n{highest_per_word}")
            print(f"Problem Summary \n{problem_summary}")
            print(f"PER Summary \n{per_summary}")

        if status_callback:
            status_callback("Crafting feedback...")

        model_response = self.get_response(
            attempted_sentence=attempted_sentence,
            results=results,
            highest_per_word=highest_per_word,
            problem_summary=problem_summary,
            per_summary=per_summary,
        )

        return model_response, df, highest_per_word, problem_summary, per_summary

    
    def feedback_to_audio(self, feedback: str, save: bool = False, save_path: str = "temp_audio/feedback.wav"):
        """Generate feedback audio using Elevenlabs TTS service

        Args:
            feedback (str): string of feedback to be converted to audio
            save (bool, optional): Whether to save the audio. Defaults to False.
            save_path (str, optional): Path to save the audio. Defaults to "temp_audio/feedback.wav".

        Returns:
            audio data: audio generated by the TTS service
        """
        import soundfile as sf
        import io
        
        audio_data = self.tts.getAudio(feedback)
        
        if save:
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save the audio as WAV file - this is more compatible than numpy arrays
            # If your TTS returns audio as bytes or numpy array with sample rate
            if hasattr(self.tts, 'sample_rate'):
                sample_rate = self.tts.sample_rate
            else:
                sample_rate = 22050  # Default sample rate if not specified
                
            # Check if audio_data is bytes or numpy array
            if isinstance(audio_data, bytes):
                # Convert bytes to numpy array if needed
                try:
                    import numpy as np
                    # This assumes the bytes are in the right format, may need adjustment
                    audio_array = np.frombuffer(audio_data, dtype=np.float32)
                    sf.write(save_path, audio_array, sample_rate)
                except:
                    # If conversion fails, save raw bytes
                    with open(save_path.replace('.wav', '.raw'), 'wb') as f:
                        f.write(audio_data)
            else:
                # Assume it's already a numpy array or something sf.write can handle
                sf.write(save_path, audio_data, sample_rate)
        
        return audio_data

    def load_audio(self, audio_path: str):
        """Load audio from a specific path

        Args:
            audio_path (str): the path of the audio you want to load

        Returns:
            tuple: audio data and sample rate
        """
        import soundfile as sf
        data, samplerate = sf.read(audio_path)
        return data, samplerate

    def play_audio(self, audio_data, sr=22050):
        """Play the audio through the computer's speakers

        Args:
            audio_data: audio to be played (numpy array or tuple from load_audio)
            sr (int, optional): sample rate of the audio. Defaults to 22050.
        """
        import sounddevice as sd
        
        # Check if audio_data is a tuple (from load_audio)
        if isinstance(audio_data, tuple) and len(audio_data) == 2:
            data, samplerate = audio_data
            sd.play(data, samplerate=samplerate)
        else:
            # Assume it's just the audio data
            sd.play(audio_data, samplerate=sr)
        
        sd.wait()  # Wait until audio finishes playing


# Default running behavior
if __name__ == "__main__":

    # DEFAULT BEHAVIOR:
    # - MAKE MODEL
    # - GETS SENTENCE FROM USER
    # - LOOP

    # AI models
    phoneme_assistant = PhonemeAssistant()

    print("Welcome to the Phonics Assistant! Let's get started.")

    attempted_sentence = input("Enter sentence to start with: ").lower()

    # user loop
    while True:
        output,_,_,_,_ = phoneme_assistant.record_audio_and_get_response(attempted_sentence, verbose=True)

        output_json = output
        print("\nFeedback: ")
        print(output_json['feedback'])

        print("\n New sentence to say: ")
        print(output_json['sentence'])

        attempted_sentence = output_json['sentence'].replace(".", "").lower()

        audio_feedback = f'{output_json["feedback"]}'
        phoneme_assistant.feedback_to_audio(audio_feedback, save=True)
        phoneme_assistant.play_audio(phoneme_assistant.load_audio("temp_audio/feedback.wav"))

        if input("Do you want to continue? (yes/no): ") != "yes":
            break
