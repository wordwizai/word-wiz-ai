import tkinter as tk
from tkinter import messagebox
from recorder import Recorder
import os
import threading

class RecorderApp:
    def __init__(self, recorder: Recorder):
        self.recorder = recorder
        self.unrecorded_indexes = sorted(map(int, self.recorder.query_unrecorded_indexes()))
        self.recorded_keys = sorted(map(int, self.recorder.recorded_keys), reverse=True)
        self.current_index = None

        self.root = tk.Tk()
        self.root.title("Recorder App")

        # Recording status
        self.phrase_label = tk.Label(self.root, text="Recording Status:")
        self.phrase_label.grid(row=0, column=0, columnspan=2)

        self.recording_status_label = tk.Label(self.root, text="Not Recording", fg="red")
        self.recording_status_label.grid(row=1, column=0, columnspan=2)

        # Sentence display
        self.original_sentence_label = tk.Label(self.root, text="Original Sentence: None")
        self.original_sentence_label.grid(row=2, column=0, columnspan=2)

        self.altered_sentence_label = tk.Label(self.root, text="Altered Sentence: None")
        self.altered_sentence_label.grid(row=3, column=0, columnspan=2)

        # Unrecorded keys list
        self.unrecorded_label = tk.Label(self.root, text="Unrecorded Keys:")
        self.unrecorded_label.grid(row=4, column=0)

        self.unrecorded_listbox = tk.Listbox(self.root)
        for idx in self.unrecorded_indexes:
            self.unrecorded_listbox.insert(tk.END, idx)
        self.unrecorded_listbox.grid(row=5, column=0)

        # Recorded keys list
        self.recorded_label = tk.Label(self.root, text="Recorded Keys:")
        self.recorded_label.grid(row=4, column=1)

        self.recorded_listbox = tk.Listbox(self.root)
        for key in self.recorded_keys:
            self.recorded_listbox.insert(tk.END, key)
        self.recorded_listbox.grid(row=5, column=1)

        # Buttons
        self.record_button = tk.Button(self.root, text="Record Selected", command=self.start_recording_thread)
        self.record_button.grid(row=6, column=0, columnspan=2)


    def start_recording_thread(self):
        recording_thread = threading.Thread(target=self.record_selected_key)
        recording_thread.start()

    def record_selected_key(self):
        try:
            selected_index = self.unrecorded_listbox.curselection()
            if not selected_index:
                selected_index = self.recorded_listbox.curselection()
                if not selected_index:
                    messagebox.showwarning("Warning", "Please select a key to record.")
                    return
                selected_key = int(self.recorded_listbox.get(selected_index))
            else:
                selected_key = int(self.unrecorded_listbox.get(selected_index))

            entry = self.recorder.retrieve_csv_data(selected_key)

            original_sentence = entry["Original Sentence"]
            altered_sentence = entry["Altered Sentence"]

            self.original_sentence_label.config(text=f"Original Sentence: {original_sentence}")
            self.altered_sentence_label.config(text=f"Altered Sentence: {altered_sentence}")
            self.recording_status_label.config(text="Recording...", fg="green")

            self.recorder.record_index(selected_key, overwrite=True)

            self.recording_status_label.config(text="Not Recording", fg="red")
            messagebox.showinfo("Info", f"Recording for key {selected_key} completed.")

            # Update lists
            if selected_key in self.unrecorded_indexes:
                self.unrecorded_indexes.remove(selected_key)
                self.unrecorded_listbox.delete(selected_index)
            if selected_key not in self.recorded_keys:
                self.recorded_keys.append(selected_key)
                self.recorded_keys.sort(reverse=True)
                self.recorded_listbox.delete(0, tk.END)
                for key in self.recorded_keys:
                    self.recorded_listbox.insert(tk.END, key)

            # Default to the lowest unrecorded key
            if self.unrecorded_indexes:
                self.unrecorded_listbox.selection_set(0)

        except Exception as e:
            self.recording_status_label.config(text="Not Recording", fg="red")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    recorder = Recorder(
        os.path.join(os.getcwd(), "dataset/phoneme_sentences.csv"),
        os.path.join(os.getcwd(), "dataset/")
    )
    app = RecorderApp(recorder)
    app.run()