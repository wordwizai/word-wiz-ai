import librosa
import librosa.display
import matplotlib.pyplot as plt
from textgrid import TextGrid
import numpy as np

def plot_spectrogram_with_words(audio_path, textgrid_path):
    """
    Plot a spectrogram of the audio file and overlay word alignments from the TextGrid file.
    
    Args:
        audio_path (str): Path to the audio file.
        textgrid_path (str): Path to the TextGrid file containing word alignments.
    """
    # Load the audio file
    audio, sr = librosa.load(audio_path, sr=None)

    # Compute the spectrogram
    spectrogram = librosa.amplitude_to_db(librosa.stft(audio), ref=np.max)

    # Load the TextGrid file
    tg = TextGrid.fromFile(textgrid_path)
    word_tier = tg.getFirst("words")

    # Plot the spectrogram
    plt.figure(figsize=(12, 6))
    librosa.display.specshow(spectrogram, sr=sr, x_axis="time", y_axis="hz", cmap="magma")
    plt.colorbar(format="%+2.0f dB")
    plt.title("Spectrogram with Word Alignments")

    # Overlay word alignments
    for interval in word_tier:
        if interval.mark.strip():  # Ignore empty intervals
            start, end, word = interval.minTime, interval.maxTime, interval.mark
            plt.axvline(x=start, color="cyan", linestyle="--", linewidth=1)
            plt.axvline(x=end, color="cyan", linestyle="--", linewidth=1)
            plt.text((start + end) / 2, sr / 2, word, color="white", ha="center", va="center", fontsize=10, bbox=dict(facecolor="black", alpha=0.5))

    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.show()

if __name__ == "__main__":
    # Example usage
    audio_path = "./temp_audio/output.wav"  # Path to the audio file
    textgrid_path = "./mfa_output/output.TextGrid"  # Path to the TextGrid file

    plot_spectrogram_with_words(audio_path, textgrid_path)
