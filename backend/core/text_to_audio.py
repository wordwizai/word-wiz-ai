import os

from dotenv import load_dotenv
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
from google.cloud import texttospeech_v1 as texttospeech


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
        self.client = texttospeech.TextToSpeechClient()

    def getAudio(self, text, is_ssml=False):
        # Check if text contains SSML tags or if explicitly marked as SSML
        if is_ssml or self._contains_ssml_tags(text):
            # Wrap in SSML root element if not already wrapped
            if not text.strip().startswith('<speak>'):
                text = f'<speak>{text}</speak>'
            synthesis_input = texttospeech.SynthesisInput(ssml=text)
        else:
            synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Chirp3-HD-Charon",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return [response.audio_content]
    
    def _contains_ssml_tags(self, text):
        """Check if text contains SSML tags"""
        import re
        # Look for common SSML tags
        ssml_pattern = r'<(phoneme|emphasis|break|say-as|prosody|voice|speak)\b[^>]*>'
        return bool(re.search(ssml_pattern, text, re.IGNORECASE))


# if __name__ == "__main__":
#     client = ElevenLabsAPIClient()
#     audio = client.getAudio(text="Hello, World!", playAudio=True)
#     print(audio)
