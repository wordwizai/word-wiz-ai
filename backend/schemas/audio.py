from pydantic import BaseModel


class AudioAnalysisRequest(BaseModel):
    attempted_sentence: str
    audio_file: bytes  # Assuming the audio file is sent as bytes
