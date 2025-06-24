#%%
import tkinter as tk
from tkinter import ttk, font
import threading
import queue
from phoneme_assistant import PhonemeAssistant
import pandas as pd

class PhonemeAssistantApp:
    def __init__(self):
        # Initialize the assistant
        self.assistant = PhonemeAssistant()

        # Create update queue for thread-safe UI updates
        self.update_queue = queue.Queue()

        # Create the main application window
        self.window = tk.Tk()
        self.window.title("Phoneme Assistant")
        self.window.geometry("800x600")
        self.window.configure(bg="#f5f5f5")
        
        # Set custom font
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Segoe UI", size=10)
        self.window.option_add("*Font", self.default_font)
        
        # Create styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("Custom.TButton", font=("Segoe UI", 10, "bold"))
        self.style.map("Custom.TButton",
            background=[('active', '#3a76d8'), ('!disabled', '#4a86e8')],
            foreground=[('!disabled', 'white')])
        self.style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="Phoneme Assistant", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)

        # Input section (top frame)
        input_frame = ttk.Frame(main_frame, padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        input_frame.configure(relief="groove", borderwidth=1)
        
        self.sentence_label = ttk.Label(input_frame, text="Enter a sentence to practice:")
        self.sentence_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.sentence_entry = ttk.Entry(input_frame, width=50, font=("Segoe UI", 11))
        self.sentence_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # When creating the button, use the custom style:
        self.run_button = ttk.Button(
            input_frame, 
            text="Record & Analyze", 
            command=self.process_audio,
            style="Custom.TButton"
        )
        self.run_button.grid(row=1, column=1, padx=10, pady=5)
        
        input_frame.columnconfigure(0, weight=1)
        
        # Status and progress area
        self.status_frame = ttk.Frame(main_frame, padding="10")
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_frame.configure(relief="groove", borderwidth=1)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode="indeterminate")
        self.progress_bar.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        
        # Create notebook for results
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Feedback tab
        feedback_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(feedback_frame, text="Feedback")
        
        self.output_label = ttk.Label(feedback_frame, wraplength=700, justify="left")
        self.output_label.pack(fill=tk.BOTH, expand=True)
        
        # Word analysis tab
        word_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(word_frame, text="Word Analysis")
        
        # Create a frame to hold the text widget and scrollbar
        text_frame = ttk.Frame(word_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar to the text widget
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.word_display_text = tk.Text(text_frame, wrap="word", height=10, 
                                        font=("Consolas", 11))
        self.word_display_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Connect scrollbar to text widget
        self.word_display_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.word_display_text.yview)  # Correct method name
        
        self.word_display_text.config(state="disabled")  # Make it read-only

        # DataFrame tab
        df_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(df_frame, text="DataFrame")
        
        # Create a frame for DataFrame with scrollbar
        df_text_frame = ttk.Frame(df_frame)
        df_text_frame.pack(fill=tk.BOTH, expand=True)
        
        df_scrollbar = ttk.Scrollbar(df_text_frame)
        df_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.df_text = tk.Text(df_text_frame, wrap="none", height=10, font=("Consolas", 10))
        self.df_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add horizontal scrollbar for DataFrame
        df_hscrollbar = ttk.Scrollbar(df_frame, orient="horizontal")
        df_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Connect scrollbars to text widget
        self.df_text.config(yscrollcommand=df_scrollbar.set, xscrollcommand=df_hscrollbar.set)
        df_scrollbar.config(command=self.df_text.yview)
        df_hscrollbar.config(command=self.df_text.xview)
        
        self.df_text.config(state="disabled")
        
        # Summaries tab
        summaries_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(summaries_frame, text="Summaries")
        
        # Create a frame for summaries with scrollbar
        summaries_text_frame = ttk.Frame(summaries_frame)
        summaries_text_frame.pack(fill=tk.BOTH, expand=True)
        
        summaries_scrollbar = ttk.Scrollbar(summaries_text_frame)
        summaries_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.summaries_text = tk.Text(summaries_text_frame, wrap="word", height=10, font=("Consolas", 11))
        self.summaries_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Connect scrollbar to text widget
        self.summaries_text.config(yscrollcommand=summaries_scrollbar.set)
        summaries_scrollbar.config(command=self.summaries_text.yview)
        
        self.summaries_text.config(state="disabled")

        # Start the queue checker BEFORE mainloop
        self.check_update_queue()
        
        # Start the Tkinter event loop
        self.window.mainloop()

    def check_update_queue(self):
        """Process any pending UI updates from threads"""
        try:
            while True:
                update_func, args, kwargs = self.update_queue.get_nowait()
                update_func(*args, **kwargs)
                self.update_queue.task_done()
        except queue.Empty:
            # No more updates to process
            pass
        # Check again after 100ms
        self.window.after(100, self.check_update_queue)
    
    def safe_update_ui(self, update_func, *args, **kwargs):
        """Thread-safe way to update the UI"""
        self.update_queue.put((update_func, args, kwargs))
    
    def update_status(self, message):
        """Update the status display with a message"""
        self.safe_update_ui(self.status_label.config, text=message)
    
    def process_audio(self):
        """Process audio in a separate thread with status updates"""
        # Disable the button to prevent multiple recordings
        self.safe_update_ui(self.run_button.config, state="disabled")
        
        # Start progress bar
        self.safe_update_ui(self.progress_bar.start)
        self.safe_update_ui(self.status_label.config, text="Starting process...")

        def run_assistant():
            try:
                attempted_sentence = self.sentence_entry.get().strip()
                if not attempted_sentence:
                    self.safe_update_ui(self.status_label.config, text="Please enter a sentence.")
                    self.safe_update_ui(self.run_button.config, state="normal")
                    self.safe_update_ui(self.progress_bar.stop)
                    return
                
                # Get the response, DataFrame, and other details from the assistant
                response, df, highest_per_word, problem_summary, per_summary = self.assistant.record_audio_and_get_response(
                    attempted_sentence, 
                    verbose=True, 
                    status_callback=lambda msg: self.safe_update_ui(self.status_label.config, text=msg)
                )
                
                self.safe_update_ui(self.process_results, response, df, highest_per_word, problem_summary, per_summary)
            except Exception as e:
                self.safe_update_ui(self.status_label.config, text=f"Error: {str(e)}")
            finally:
                # Always re-enable the button and stop progress
                self.safe_update_ui(self.run_button.config, state="normal")
                self.safe_update_ui(self.progress_bar.stop)
                self.safe_update_ui(self.status_label.config, text="Ready")

        # Start the thread
        threading.Thread(target=run_assistant, daemon=True).start()
    
    def process_results(self, response, df, highest_per_word=None, problem_summary=None, per_summary=None):
        """Process the results from the assistant (runs on main thread)"""
        try:
            output_json = response
            feedback_text = output_json.get("feedback", "No feedback available")
            new_sentence = output_json.get("sentence", "No sentence available")
            
            # Format feedback with better styling
            formatted_text = f"FEEDBACK:\n{feedback_text}\n\nNEXT SENTENCE:\n{new_sentence}"
            self.output_label.config(text=formatted_text)
            
            # Switch to the feedback tab
            self.notebook.select(0)
            
            self.display_colored_words(df)
            self.display_dataframe(df)
            self.display_summaries(problem_summary, per_summary, highest_per_word)
            
            self.sentence_entry.delete(0, tk.END)
            self.sentence_entry.insert(0, output_json["sentence"].replace(".", "").lower())
        except Exception as e:
            self.output_label.config(text=f"Error: {str(e)}")

    def display_colored_words(self, df):
        """
        Display each word from the DataFrame in the text widget, color-coded based on PER.
        """
        self.word_display_text.config(state="normal")
        self.word_display_text.delete("1.0", tk.END)  # Clear previous content
        
        # Add header
        self.word_display_text.insert(tk.END, "WORD ANALYSIS\n\n", "header")
        self.word_display_text.tag_configure("header", font=("Segoe UI", 12, "bold"))

        for i, (_, row) in enumerate(df.iterrows()):
            word_type = row.get("type", "unknown")
            gt_word = row.get("ground_truth_word", "")
            predicted = row.get("predicted_word", "")
            
            # Skip empty entries
            if not gt_word and not predicted:
                continue
                
            # Add word number and create section for each word
            self.word_display_text.insert(tk.END, f"Word {i+1}: ", "word_num")
            self.word_display_text.tag_configure("word_num", font=("Segoe UI", 10, "bold"))
            
            # Handle different word types
            if word_type == "deletion":
                # Word was in ground truth but not spoken
                self.word_display_text.insert(tk.END, f"{gt_word}\n", "deletion")
                self.word_display_text.tag_configure("deletion", foreground="red", font=("Segoe UI", 11, "bold"))
                self.word_display_text.insert(tk.END, "This word wasn't spoken (deletion)\n\n", "error_msg")
                self.word_display_text.tag_configure("error_msg", font=("Segoe UI", 9, "italic"))
                continue
                
            elif word_type == "insertion":
                # Word was spoken but not in ground truth
                self.word_display_text.insert(tk.END, f"{predicted}\n", "insertion")
                self.word_display_text.tag_configure("insertion", foreground="blue", font=("Segoe UI", 11, "bold"))
                self.word_display_text.insert(tk.END, "Extra word spoken (insertion)\n\n", "error_msg")
                continue
                
            # For match or substitution types (or any other types)
            # Calculate PER color
            if not predicted:
                per = 1
            else:
                per = row.get("per", 0)

            red = min(int(per * 255), 255)
            green = max(255 - red, 0)
            color = f"#{red:02x}{green:02x}00"  # RGB to hex

            # Configure the tag for the gradient color
            tag_name = f"color_{color}"
            try:
                self.word_display_text.tag_cget(tag_name, "foreground")
            except tk.TclError:
                self.word_display_text.tag_config(tag_name, foreground=color, font=("Segoe UI", 11, "bold"))

            # Insert the word with the appropriate tag
            self.word_display_text.insert(tk.END, f"{gt_word}\n", tag_name)
            
            # Display actual vs expected
            self.word_display_text.insert(tk.END, f"Expected: {gt_word}   Heard: {predicted}\n", "details")
            self.word_display_text.tag_configure("details", font=("Segoe UI", 9))
            
            # Handle case where phonemes might not exist
            phonemes = row.get("phonemes", [])
            statuses = row.get("statuses", [])
            
            if phonemes and isinstance(phonemes, list) and len(phonemes) > 0:
                # Display phonemes header
                self.word_display_text.insert(tk.END, "Phonemes: ", "phoneme_header")
                self.word_display_text.tag_configure("phoneme_header", font=("Segoe UI", 9, "bold"))
                
                # Make sure statuses list is at least as long as phonemes list
                while len(statuses) < len(phonemes):
                    statuses.append("correct")
                
                # Display phonemes with their statuses
                for j, (phoneme, status) in enumerate(zip(phonemes, statuses)):
                    if status == "missed":
                        phoneme_color = "red"
                        status_text = "(missed)"
                    elif status == "substituted":
                        phoneme_color = "orange"
                        status_text = "(subst)"
                    elif status == "added":
                        phoneme_color = "blue"
                        status_text = "(added)"
                    else:
                        phoneme_color = "green"  # Default color for correct phonemes
                        status_text = ""

                    # Configure the tag for the phoneme status color
                    phoneme_tag = f"phoneme_{phoneme_color}"
                    try:
                        self.word_display_text.tag_cget(phoneme_tag, "foreground")
                    except tk.TclError:
                        self.word_display_text.tag_config(phoneme_tag, foreground=phoneme_color)

                    # Insert the phoneme with the appropriate tag
                    self.word_display_text.insert(tk.END, f"{phoneme}", phoneme_tag)
                    if status_text:
                        self.word_display_text.insert(tk.END, f"{status_text} ", "status")
                    else:
                        self.word_display_text.insert(tk.END, " ", "status")
                        
                self.word_display_text.tag_configure("status", font=("Segoe UI", 8))
            else:
                # No phonemes available
                self.word_display_text.insert(tk.END, "No phoneme data available", "no_phonemes")
                self.word_display_text.tag_configure("no_phonemes", font=("Segoe UI", 9, "italic"))
                
            self.word_display_text.insert(tk.END, "\n\n")  # Add space between words

        self.word_display_text.config(state="disabled")  # Make the text widget read-only

    def display_dataframe(self, df):
        """Display the entire DataFrame in a text widget"""
        self.df_text.config(state="normal")
        self.df_text.delete("1.0", tk.END)
        
        if df is not None and not df.empty:
            # Format the DataFrame as string with fixed-width columns
            df_string = df.to_string()
            self.df_text.insert(tk.END, df_string)
        else:
            self.df_text.insert(tk.END, "No DataFrame available")
            
        self.df_text.config(state="disabled")
        
    def display_summaries(self, problem_summary, per_summary, highest_per_word):
        """Display problem and PER summaries"""
        self.summaries_text.config(state="normal")
        self.summaries_text.delete("1.0", tk.END)
        
        # Add headers and content with formatting
        self.summaries_text.insert(tk.END, "PROBLEM SUMMARY\n\n", "header")
        self.summaries_text.tag_configure("header", font=("Segoe UI", 12, "bold"))
        
        if problem_summary:
            if isinstance(problem_summary, dict):
                for key, value in problem_summary.items():
                    self.summaries_text.insert(tk.END, f"{key}:\n", "subheader")
                    self.summaries_text.insert(tk.END, f"{value}\n\n", "content")
            else:
                self.summaries_text.insert(tk.END, f"{problem_summary}\n\n", "content")
        else:
            self.summaries_text.insert(tk.END, "No problem summary available\n\n", "content")
            
        self.summaries_text.insert(tk.END, "\nPER SUMMARY\n\n", "header")
        
        if per_summary:
            if isinstance(per_summary, dict):
                for key, value in per_summary.items():
                    self.summaries_text.insert(tk.END, f"{key}: {value}\n", "content")
            else:
                self.summaries_text.insert(tk.END, f"{per_summary}\n\n", "content")
        else:
            self.summaries_text.insert(tk.END, "No PER summary available\n\n", "content")
            
        self.summaries_text.insert(tk.END, "\nHIGHEST PER WORD\n\n", "header")
        
        if highest_per_word is not None:
            if isinstance(highest_per_word, pd.Series):
                self.summaries_text.insert(tk.END, highest_per_word.to_string(), "content")
            else:
                self.summaries_text.insert(tk.END, f"{highest_per_word}\n", "content")
        else:
            self.summaries_text.insert(tk.END, "No highest PER word data available\n", "content")
            
        self.summaries_text.tag_configure("subheader", font=("Segoe UI", 10, "bold"))
        self.summaries_text.tag_configure("content", font=("Consolas", 10))
        
        self.summaries_text.config(state="disabled")

if __name__ == "__main__":
    app = PhonemeAssistantApp()
