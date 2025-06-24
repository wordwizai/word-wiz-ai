import os
import json
import csv
from audio_recording import run_vad 

class Recorder:
    def __init__(self, dataset_csv: str, recordings_dir: str):
        """
        Initializes the Recorder class.

        Args:
            dataset_csv (str): Path to the dataset CSV file.
            recordings_dir (str): Directory to store recordings and metadata.
        """
        self.dataset_csv = dataset_csv
        self.recordings_dir = recordings_dir
        self.recorded_keys = self._load_recorded_keys()

        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)

    def _load_recorded_keys(self) -> set:
        """
        Loads the keys of already recorded entries.

        Returns:
            set: A set of recorded keys.
        """
        recorded_keys_file = os.path.join(self.recordings_dir, "recorded_keys.json")
        if os.path.exists(recorded_keys_file):
            with open(recorded_keys_file, "r", encoding="utf-8") as file:
                return set(json.load(file))
        return set()

    def _save_recorded_keys(self):
        """
        Saves the keys of recorded entries to a JSON file.
        """
        recorded_keys_file = os.path.join(self.recordings_dir, "recorded_keys.json")
        with open(recorded_keys_file, "w", encoding="utf-8") as file:
            json.dump(list(self.recorded_keys), file)

    def query_unrecorded_indexes(self) -> list[int]:
        """
        Queries the indexes of entries that have not been recorded.

        Returns:
            list[int]: List of unrecorded indexes.
        """
        unrecorded_indexes = []
        with open(self.dataset_csv, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for idx, row in enumerate(reader, start=1):
                if row["Key"] not in self.recorded_keys:
                    unrecorded_indexes.append(idx)
        return unrecorded_indexes

    def record_index(self, index: int):
        """
        Records the data for a specific index and stores it in the dataset.

        Args:
            index (int): The index to record.
        """
        with open(self.dataset_csv, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        if index < 1 or index > len(rows):
            raise ValueError(f"Index {index} is out of range.")

        entry = rows[index - 1]
        key = entry["Key"]

        if key in self.recorded_keys:
            print(f"Index {index} (Key: {key}) has already been recorded.")
            return

        # Simulate recording process
        print(f"Recording for index {index} (Key: {key})...")
        recording_path = os.path.join(self.recordings_dir,"/audio/", f"{key}.wav")
        metadata_path = os.path.join(self.recordings_dir, "/transcriptions/", f"{key}.json")

        # Simulate saving a recording file
        run_vad(recording_path)

        # Save metadata as JSON
        with open(metadata_path, "w", encoding="utf-8") as metadata_file:
            json.dump(entry, metadata_file, indent=4)

        # Mark the key as recorded
        self.recorded_keys.add(key)
        self._save_recorded_keys()
        print(f"Recording and metadata saved for index {index} (Key: {key}).")

if __name__ == "__main__":
    print('Init recorder')
    recorder = Recorder(os.path.join(os.getcwd(), "dataset/phoneme_sentences.csv"), os.path.join(os.getcwd(),"/dataset/"))
    print('called recording')
    recorder.record_index(1)