from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os

class ElevenLabsAPIClient:
    def __init__(self):
        load_dotenv()
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    
    def getAudio(self, text, playAudio=False):
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id="nPczCjzI2devNBz1zQrb",
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",)
        if playAudio:
            self.playAudio(audio)
        return audio
    
    def playAudio(self, audio):
        play(audio)

if __name__ == "__main__":
    client = ElevenLabsAPIClient()
    audio = client.getAudio(text="Hello, World!", playAudio=True)
    print(audio)