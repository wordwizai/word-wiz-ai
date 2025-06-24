#%%
import noisereduce as nr
import librosa
import librosa.display
import matplotlib.pyplot as plt
import IPython.display as ipd

def preprocess_audio(audio, sr=16000):
    audio = nr.reduce_noise(y=audio, sr=sr)
    audio = librosa.util.normalize(audio)
    return audio

def display_spectrogram(audio, sr=16000):
    # Compute MFCCs
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mfccs, x_axis='time', sr=sr)
    plt.colorbar()
    plt.title('MFCC')
    plt.tight_layout()
    plt.show()

def display_playable_audio(audio, sr=16000):
    # Display a playable audio widget
    return ipd.Audio(data=audio, rate=sr)

#%%
if __name__ == "__main__":
    from audio_recording import record_and_process_pronunciation
    # Load the audio file
    audio, sr = librosa.load("temp_audio/output.wav", sr=16000)
    # Display the before audio
    playable_audio = display_playable_audio(audio, sr)
    results_before = record_and_process_pronunciation("the cat jumped on the mat", use_previous_recording=True)
    
    print("Before audio widget:")
    ipd.display(playable_audio)

    # Preprocess the audio
    audio = preprocess_audio(audio, sr)
    results_after = record_and_process_pronunciation("the cat jumped on the mat", use_previous_recording=True)

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

