# %%
import time
import numpy as np
import IPython.display as ipd
import librosa
import librosa.display
import matplotlib.pyplot as plt
import noisereduce as nr


def preprocess_audio(audio, sr=16000, audio_length_seconds=None):
    """
    Preprocess audio with adaptive noise reduction based on audio length.
    
    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        audio_length_seconds: Duration of audio in seconds. If None, calculated from audio length.
        
    Returns:
        Preprocessed audio array
        
    Note:
        For longer audio (>8 seconds), uses lighter noise reduction to avoid distortion.
        This improves model accuracy on longer recordings.
    """
    preprocess_start = time.time()
    
    if audio_length_seconds is None:
        audio_length_seconds = len(audio) / sr
    
    # Lighter noise reduction for longer audio to avoid distortion
    if audio_length_seconds > 8:
        print(f"⚠️  Long audio detected ({audio_length_seconds:.1f}s) - using lighter noise reduction")
        # Less aggressive noise reduction for long audio
        noise_start = time.time()
        audio = nr.reduce_noise(
            y=audio,
            sr=sr,
            stationary=True,
            prop_decrease=0.5  # Reduce by 50% instead of 100%
        )
        print(f"⏱️  Noise reduction took {time.time() - noise_start:.3f}s")
    else:
        # Standard noise reduction for shorter audio
        noise_start = time.time()
        audio = nr.reduce_noise(y=audio, sr=sr, stationary=True, prop_decrease=1.0)
        print(f"⏱️  Noise reduction took {time.time() - noise_start:.3f}s")
    
    norm_start = time.time()
    # Replace slow librosa.util.normalize with fast numpy normalization
    # librosa.util.normalize is calling scipy peak normalization which is extremely slow
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    print(f"⏱️  Normalization took {time.time() - norm_start:.3f}s")
    
    print(f"⏱️  Total preprocessing took {time.time() - preprocess_start:.3f}s")
    return audio


def display_spectrogram(audio, sr=16000):
    # Compute MFCCs
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mfccs, x_axis="time", sr=sr)
    plt.colorbar()
    plt.title("MFCC")
    plt.tight_layout()
    plt.show()


def display_playable_audio(audio, sr=16000):
    # Display a playable audio widget
    return ipd.Audio(data=audio, rate=sr)


# %%
if __name__ == "__main__":
    from audio_recording import record_and_process_pronunciation

    # Load the audio file
    audio, sr = librosa.load("temp_audio/output.wav", sr=16000)
    # Display the before audio
    playable_audio = display_playable_audio(audio, sr)
    results_before = record_and_process_pronunciation(
        "the cat jumped on the mat", use_previous_recording=True
    )

    print("Before audio widget:")
    ipd.display(playable_audio)

    # Preprocess the audio
    audio = preprocess_audio(audio, sr)
    results_after = record_and_process_pronunciation(
        "the cat jumped on the mat", use_previous_recording=True
    )

    # Display the spectrogram
    display_spectrogram(audio, sr)

    # Display the after audio
    playable_audio = display_playable_audio(audio, sr)
    print("After audio widget:")
    ipd.display(playable_audio)

    print("results before:")
    print(results_before)
    print("results after")
    print(results_after)
