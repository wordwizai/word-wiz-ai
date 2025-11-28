import tkinter as tk
from tkinter import filedialog, messagebox
import sounddevice as sd
import soundfile as sf
import threading
import os

SAMPLE_RATE = 16000
CHANNELS = 1


class RecorderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Test Case Recorder")
        self.is_recording = False
        self.audio = []

        tk.Label(root, text="Mode:").pack()
        self.mode_var = tk.StringVar(value="system")
        modes = ["system", "analysis", "extraction", "gpt"]
        self.mode_menu = tk.OptionMenu(root, self.mode_var, *modes, command=self.update_mode)
        self.mode_menu.pack(pady=5)

        self.sentence_label = tk.Label(root, text="Sentence:")
        self.sentence_label.pack()
        self.sentence_entry = tk.Entry(root, width=60)
        self.sentence_entry.pack(pady=5)

        # For analysis/gpt modes, allow JSON input
        self.json_label = tk.Label(root, text="Input JSON:")
        self.json_entry = tk.Text(root, width=60, height=8)

        self.record_btn = tk.Button(root, text="Record", command=self.start_recording)
        self.record_btn.pack(pady=5)
        self.stop_btn = tk.Button(root, text="Stop", command=self.stop_recording, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        tk.Button(root, text="Save Test Case", command=self.save_test_case).pack(pady=10)

        self.status = tk.Label(root, text="Idle", fg="blue")
        self.status.pack(pady=5)

        self.update_mode("system")

    def update_mode(self, mode):
        if mode == "system" or mode == "extraction":
            self.sentence_label.pack()
            self.sentence_entry.pack(pady=5)
            self.record_btn.pack(pady=5)
            self.stop_btn.pack(pady=5)
            self.json_label.pack_forget()
            self.json_entry.pack_forget()
        else:
            self.sentence_label.pack_forget()
            self.sentence_entry.pack_forget()
            self.record_btn.pack_forget()
            self.stop_btn.pack_forget()
            self.json_label.pack()
            self.json_entry.pack(pady=5)

    def start_recording(self):
        self.is_recording = True
        self.audio = []
        self.status.config(text="Recording...", fg="red")
        self.record_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=self._record).start()

    def _record(self):
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.audio.append(indata.copy())
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
            while self.is_recording:
                sd.sleep(100)

    def stop_recording(self):
        self.is_recording = False
        self.status.config(text="Recording stopped", fg="green")
        self.record_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)


    def save_test_case(self):
        mode = self.mode_var.get()
        if mode == "system":
            sentence = self.sentence_entry.get().strip()
            if not sentence:
                messagebox.showerror("Error", "Please enter a sentence.")
                return
            if not self.audio:
                messagebox.showerror("Error", "No audio recorded.")
                return
            # Auto-create new test_case_XX folder
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "system"))
            os.makedirs(base_dir, exist_ok=True)
            # Find next available test_case_XX
            existing = [d for d in os.listdir(base_dir) if d.startswith("test_case_")]
            nums = [int(d.split("_")[-1]) for d in existing if d.split("_")[-1].isdigit()]
            next_num = max(nums) + 1 if nums else 1
            folder = os.path.join(base_dir, f"test_case_{next_num:02d}")
            os.makedirs(folder, exist_ok=True)
            # Save sentence.txt
            with open(os.path.join(folder, "sentence.txt"), "w", encoding="utf-8") as f:
                f.write(sentence)
            # Save audio.wav
            import numpy as np
            audio_np = np.concatenate(self.audio, axis=0)
            sf.write(os.path.join(folder, "audio.wav"), audio_np, SAMPLE_RATE)
            self.status.config(text=f"Saved to {folder}", fg="blue")
            messagebox.showinfo("Saved", f"Test case saved to {folder}")
        elif mode == "extraction":
            sentence = self.sentence_entry.get().strip()
            if not sentence:
                messagebox.showerror("Error", "Please enter a sentence.")
                return
            if not self.audio:
                messagebox.showerror("Error", "No audio recorded.")
                return
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "extraction"))
            os.makedirs(base_dir, exist_ok=True)
            folder = filedialog.askdirectory(title="Select extraction test case folder to save")
            if not folder:
                return
            with open(os.path.join(folder, "sentence.txt"), "w", encoding="utf-8") as f:
                f.write(sentence)
            import numpy as np
            audio_np = np.concatenate(self.audio, axis=0)
            sf.write(os.path.join(folder, "audio.wav"), audio_np, SAMPLE_RATE)
            self.status.config(text=f"Saved to {folder}", fg="blue")
            messagebox.showinfo("Saved", f"Test case saved to {folder}")
        elif mode == "analysis":
            json_str = self.json_entry.get("1.0", tk.END).strip()
            if not json_str:
                messagebox.showerror("Error", "Please enter input JSON.")
                return
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "analysis"))
            os.makedirs(base_dir, exist_ok=True)
            file_path = filedialog.asksaveasfilename(title="Save analysis test case as", defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=base_dir)
            if not file_path:
                return
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            self.status.config(text=f"Saved to {file_path}", fg="blue")
            messagebox.showinfo("Saved", f"Test case saved to {file_path}")
        elif mode == "gpt":
            json_str = self.json_entry.get("1.0", tk.END).strip()
            if not json_str:
                messagebox.showerror("Error", "Please enter input JSON.")
                return
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "gpt"))
            os.makedirs(base_dir, exist_ok=True)
            file_path = filedialog.asksaveasfilename(title="Save gpt test case as", defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=base_dir)
            if not file_path:
                return
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            self.status.config(text=f"Saved to {file_path}", fg="blue")
            messagebox.showinfo("Saved", f"Test case saved to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RecorderUI(root)
    root.mainloop()
