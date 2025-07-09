import os
import queue

# from .grapheme_to_phoneme import grapheme_to_phoneme
# from .process_audio import process_audio_array
import threading
import time
import wave

import librosa
import numpy as np

# import IPython.display as ipd
import sounddevice as sd
import webrtcvad


def run_vad(
    output_file="ai/temp_audio/output.wav",
    fs=16000,
    chunk_duration=0.03,
    vad_mode=3,
    silence_threshold=20,
    status_callback=(lambda v: None),
):
    chunk_size = int(fs * chunk_duration)
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(status)
        audio_queue.put(indata.copy())

    def record_audio():
        with sd.InputStream(
            samplerate=fs,
            channels=1,
            dtype="int16",
            blocksize=chunk_size,
            callback=audio_callback,
        ):
            print("Recording started...")
            while not stop_event.is_set():
                time.sleep(0.1)
            print("Recording stopped.")

    def process_vad():
        vad = webrtcvad.Vad(vad_mode)
        silent_chunks = 0
        frames = []

        while not stop_event.is_set():
            try:
                chunk = audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            is_speech = vad.is_speech(chunk.tobytes(), fs)
            frames.append(chunk)

            if not is_speech:
                silent_chunks += 1
                if silent_chunks > silence_threshold:
                    stop_event.set()
            else:
                silent_chunks = 0

        # Save recorded audio to a WAV file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        audio_data = np.concatenate(frames)
        with wave.open(output_file, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(fs)
            wf.writeframes(audio_data.tobytes())
        print(f"Audio saved to {output_file}")

    # Start threads
    recording_thread = threading.Thread(target=record_audio)
    vad_thread = threading.Thread(target=process_vad)

    recording_thread.start()
    vad_thread.start()

    if status_callback:
        status_callback("Recording...")

    recording_thread.join()
    vad_thread.join()


# Combining everything into a single function
def record_and_process_pronunciation(
    text,
    phoneme_extraction_model=None,
    use_previous_recording=False,
    word_extraction_model=None,
    status_callback=None,
    audio_file="temp_audio/output.wav",
    audio_array=None,
):
    """Does all of the work for recording and processing the pronunciation of phonemes

    Args:
        text (_type_): _description_
        phoneme_extraction_model (_type_): _description_
        use_previous_recording (bool, optional): _description_. Defaults to False.
        word_extraction_model (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    if not use_previous_recording and audio_array is None:
        run_vad("temp_audio/output.wav", status_callback=status_callback)

    if status_callback:
        status_callback("Translating to phoneme...")

    # ground_truth_phonemes = grapheme_to_phoneme(text)

    if audio_array is None:
        audio_array, sr = librosa.load(audio_file, sr=16000)

    # if status_callback:
    #     status_callback("Processing audio...")
    # output = process_audio_array(ground_truth_phonemes=ground_truth_phonemes, audio_array=audio_array, sampling_rate=16000, phoneme_extraction_model=phoneme_extraction_model, word_extraction_model=word_extraction_model)
    return output, ground_truth_phonemes


# %%
if __name__ == "__main__":
    from phoneme_extractor import PhonemeExtractor

    extractor = PhonemeExtractor()
    sentence = "the quick brown fox jumped over the lazy dog"

    print(f"Say: {sentence}")
    output, ground_truth_phonemes = record_and_process_pronunciation(sentence)
    print(f"Output: {output}")
    print(f"Ground truth: {ground_truth_phonemes}")

    # GPT stuff
    print(f"Attempted scentence: {sentence}")
    print(f"Ground truth phonemes: {ground_truth_phonemes}")

    # %%
    print(output)
