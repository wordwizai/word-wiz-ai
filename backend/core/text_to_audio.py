import os
import io
import wave

from dotenv import load_dotenv
from elevenlabs import play, stream
from elevenlabs.client import ElevenLabs
from google import genai
from google.genai import types


class ElevenLabsAPIClient:
    def __init__(self):
        load_dotenv()
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    def getAudio(self, text):
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id="nPczCjzI2devNBz1zQrb",
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )
        return audio


class GoogleTTSAPIClient:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(
            api_key=os.getenv("GOOGLE_CLOUD_AI_API_KEY"),
        )

    def wave_file_bytesio(self, pcm, channels=1, rate=24000, sample_width=2):
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)
        buffer.seek(0)
        return buffer

    def getAudio(self, text):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents="Say cheerfully: " + text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore",
                        )
                    )
                ),
            ),
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        wave_bytes = self.wave_file_bytesio(data)
        return wave_bytes


# if __name__ == "__main__":
#     client = ElevenLabsAPIClient()
#     audio = client.getAudio(text="Hello, World!", playAudio=True)
#     print(audio)
