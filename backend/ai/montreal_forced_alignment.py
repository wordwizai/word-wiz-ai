import os
import shutil
import subprocess
import pandas as pd

class MontrealForcedAligner:
    def __init__(self, mfa_path="mfa", acoustic_model="english_mfa", dictionary_path="english_us_arpa"):
        """
        Initialize the Montreal Forced Aligner wrapper.
        Args:
            mfa_path (str): Path to the MFA executable.
            acoustic_model (str): Pre-trained acoustic model to use.
            dictionary_path (str): Path to the pronunciation dictionary.
        """
        self.mfa_path = mfa_path
        self.acoustic_model = acoustic_model
        self.dictionary_path = dictionary_path

    def validate_corpus(self, corpus_directory):
        """
        Validate that the corpus directory contains matching .wav and .txt files.
        Args:
            corpus_directory (str): Directory containing audio and transcript files.
        """
        audio_files = [f for f in os.listdir(corpus_directory) if f.endswith(".wav")]
        transcript_files = [f for f in os.listdir(corpus_directory) if f.endswith(".txt")]

        if not audio_files:
            raise FileNotFoundError("No .wav files found in the corpus directory.")
        if not transcript_files:
            raise FileNotFoundError("No .txt files found in the corpus directory.")

        for audio_file in audio_files:
            base_name = os.path.splitext(audio_file)[0]
            if f"{base_name}.txt" not in transcript_files:
                raise FileNotFoundError(f"Missing transcript file for {audio_file}.")

    def clean_temp_files(self, temp_dir):
        """
        Clean up temporary files from previous MFA runs.
        Args:
            temp_dir (str): Path to the temporary directory used by MFA.
        """
        if os.path.exists(temp_dir):
            print(f"Cleaning up temporary files in {temp_dir}...")
            shutil.rmtree(temp_dir)

    def align(self, corpus_directory, output_dir="mfa_output"):
        """
        Run MFA to align audio and transcript.
        Args:
            corpus_directory (str): Directory containing audio and transcript files.
            output_dir (str): Directory to store alignment results.
        Returns:
            str: Path to the TextGrid file with alignment results.
        """
        self.validate_corpus(corpus_directory)

        # Clean up temporary files
        temp_dir = os.path.join(os.path.expanduser("~"), "Documents", "MFA", corpus_directory)
        self.clean_temp_files(temp_dir)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        command = [
            self.mfa_path, "align",
            corpus_directory, self.dictionary_path, self.acoustic_model, output_dir
        ]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"MFA alignment failed: {e}")
        
        return os.path.join(output_dir, "output.TextGrid")  # Adjust based on MFA output

    def parse_textgrid(self, textgrid_path):
        """
        Parse the TextGrid file to extract phoneme and word alignments.
        Args:
            textgrid_path (str): Path to the TextGrid file.
        Returns:
            pd.DataFrame: DataFrame containing word and phoneme alignments with start and end times.
        """
        from textgrid import TextGrid
        tg = TextGrid.fromFile(textgrid_path)
        word_tier = tg.getFirst("words")
        phoneme_tier = tg.getFirst("phones")

        words = [{"type": "word", "text": interval.mark, "start": interval.minTime, "end": interval.maxTime}
                 for interval in word_tier if interval.mark.strip()]
        phonemes = [{"type": "phoneme", "text": interval.mark, "start": interval.minTime, "end": interval.maxTime}
                    for interval in phoneme_tier if interval.mark.strip()]

        return pd.DataFrame(words + phonemes)

if __name__ == "__main__":
    # Example usage of MontrealForcedAligner
    mfa = MontrealForcedAligner(
        mfa_path="mfa",  # Path to the MFA executable
        acoustic_model="english_mfa",  # Correct acoustic model name
        dictionary_path="english_us_arpa"  # Correct dictionary name
    )

    # Paths to input directories
    corpus_directory = "./temp_audio"  # Directory containing audio and transcript files

    # Align the audio and transcript
    try:
        print("Running Montreal Forced Aligner...")
        textgrid_path = mfa.align(corpus_directory)

        # Parse the TextGrid file
        print("Parsing TextGrid file...")
        alignment_df = mfa.parse_textgrid(textgrid_path)

        # Display the alignment results
        print("Alignment Results:")
        print(alignment_df)
    except Exception as e:
        print(f"Error: {e}")
