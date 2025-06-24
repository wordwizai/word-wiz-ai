import pandas as pd
import librosa
import json
import wave
import os

# Description: Load the dataset from the Hugging Face Datasets library
class SelfSpeechDatasetLoader:
    def __init__(self, dataset_path = os.path.join(os.getcwd(),"dataset")):
        self.audio_path = os.path.join(dataset_path, "audio")
        self.trans_path = os.path.join(dataset_path, "transcriptions")

        self.data = self._load_dataset()

    def _load_dataset(self):
        dataset = []
        # Get all wav file names (without extension)
        audio_files = [f for f in os.listdir(self.audio_path) if f.endswith(".wav")]
        audio_ids = sorted([os.path.splitext(f)[0] for f in audio_files], key=lambda x: int(x))

        for audio_id in audio_ids:
            audio_file = os.path.join(self.audio_path, f"{audio_id}.wav")
            trans_file = os.path.join(self.trans_path, f"{audio_id}.json")

            if not os.path.exists(trans_file):
                print(f"Warning: Missing transcription for {audio_id}")
                continue

            with open(trans_file, "r", encoding="utf-8") as f:
                transcription = json.load(f)

            dataset.append({
                "id": audio_id,
                "audio_path": audio_file,
                "per": transcription["PER"],
                "original_sentence": transcription["Original Sentence"],
                "altered_sentence": transcription["Altered Sentence"],
                "original_phonemes": transcription["Original Phonemes"],
                "altered_phonemes": transcription["Altered Phonemes"],
            })

        return dataset

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def get_audio_bytes(self, index):
        """Optional: Load raw bytes of the .wav file."""
        audio,sr = librosa.load(self.data[index]["audio_path"], sr=16000)
        return audio

    def get_audio_duration(self, index):
        """Optional: Get audio duration in seconds."""
        with wave.open(self.data[index]["audio_path"], "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)

if __name__ == "__main__":
    loader = SelfSpeechDatasetLoader()
    print(loader[30])