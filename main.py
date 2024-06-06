import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import speech_recognition as sr
import os
from PIL import Image, ImageTk
from time import strftime
import threading
from datetime import datetime
import webbrowser

def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i

    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1,
                           dp[i][j - 1] + 1,
                           dp[i - 1][j - 1] + cost
                          )
    return dp[m][n]

class SpeechToTextApp(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.root.title("Speech to Text App")
        self.root.geometry("1300x700")
        self.root.resizable(width=True, height=True)

        self.create_widgets()
        self.microphone = sr.Microphone()

    def create_widgets(self):
        
        self.outer_frame = tk.Frame(self.root, bg="dark gray", padx=10, pady=10)
        self.outer_frame.pack(expand=True, fill=tk.BOTH)

        
        self.content_frame = tk.Frame(self.outer_frame, bg="dark grey")
        self.content_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        
        self.textbox = scrolledtext.ScrolledText(self.content_frame, width=130, height=25, 
                                                 font=("Courier", 12), bg="#e0e0e0")
        self.textbox.pack(pady=20, fill=tk.BOTH, expand=True)

        
        button_frame = tk.Frame(self.content_frame, bg="dark grey")
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="Start Recording", 
                                      command=self.start_recording,
                                      font=("Fixedsys", 15, "bold"), 
                                      bg="#00FF00", fg="white", bd=5, relief="raised")
        
        self.start_button.pack(side=tk.LEFT, padx=10, pady=30)


        self.stop_button = tk.Button(button_frame, text="Stop Recording", 
                                     command=self.stop_recording, state=tk.DISABLED,
                                     font=("Fixedsys", 15, "bold"), 
                                     bg="#FF0000", fg="white", bd=5, relief="raised")
        
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.save_button = tk.Button(button_frame, text="Save Recording", 
                                     command=self.save_recording, state=tk.DISABLED,
                                     font=("Fixedsys", 15, "bold"), 
                                     bg="Skyblue3", fg="white", bd=5, relief="raised")
        
        self.save_button.pack(side=tk.LEFT, padx=10)

        self.save_entries_button = tk.Button(button_frame, text="Save Entries", 
                                             command=self.save_entries_to_folder,
                                             font=("Fixedsys", 15, "bold"), 
                                             bg="lemon chiffon", fg="black", bd=5, relief="raised")
        
        self.save_entries_button.pack(side=tk.LEFT, padx=10)

        self.search_button = tk.Button(button_frame, text="Search Recordings", 
                                       command=self.search_recordings,
                                       font=("Fixedsys", 15, "bold"),
                                       bg="#F5FFFA", fg="black", bd=5, relief="raised")
        
        self.search_button.pack(side=tk.LEFT, padx=10)

        self.recorded_entries = []

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        self.is_recording = False
        self.recorded_text = ""

        self.save_folder = self.create_save_folder()

    def create_save_folder(self):
        save_folder = os.path.join(os.path.expanduser('~'), "SpeechToTextRecordings")
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        return save_folder

    def start_recording(self):
        self.is_recording = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        self.textbox.delete(1.0, tk.END)
        self.recorded_text = ""

        threading.Thread(target=self.recognize_speech).start()

    def stop_recording(self):
        self.is_recording = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)

    def recognize_speech(self):
        while self.is_recording:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                try:
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio)
                    self.recorded_text += text + "\n"
                    self.root.after(0, self.update_textbox, text)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    self.is_recording = False
                    self.root.after(0, messagebox.showerror, 
                                    "Error", f"Speech recognition request failed: {str(e)}")
                    self.root.after(0, self.stop_recording)
                    break

    def update_textbox(self, text):
        self.textbox.insert(tk.END, text + "\n")
        self.textbox.see(tk.END)

    def save_recording(self):
        if self.recorded_text:
            entry_name = simpledialog.askstring("Save Recording", 
                                                "Enter a name for the recording:")
            if entry_name:
                file_path = os.path.join(self.save_folder, f"{entry_name}.txt")
                try:
                    with open(file_path, 'w') as file:
                        file.write(self.recorded_text)
                    self.recorded_entries.append((entry_name, file_path))
                    messagebox.showinfo("Success", f"Recording '{entry_name}' saved.")
                    self.clear_textbox()
                except IOError as e:
                    messagebox.showerror("Error", f"Failed to save recording: {str(e)}")

    def sort_recorded_entries_by_name(self):
        n = len(self.recorded_entries)
        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                if self.recorded_entries[j][0].lower() > self.recorded_entries[j + 1][0].lower():
                    self.recorded_entries[j], self.recorded_entries[j + 1] = self.recorded_entries[j + 1], self.recorded_entries[j]
                    swapped = True
            if not swapped:
                break

    def save_entries_to_folder(self):
        if self.recorded_entries:
            self.sort_recorded_entries_by_name()  
            messagebox.showinfo("Info", "Recordings are saved in:\n" + self.save_folder)
        else:
            messagebox.showinfo("Info", "No recordings to save.")

    def search_recordings(self):
        query = simpledialog.askstring("Search Recordings", "Enter search keyword:")
        if query:
            matched_files = []
            self.textbox.delete(1.0, tk.END)

            for filename in os.listdir(self.save_folder):
                if filename.endswith('.txt'):
                    entry_name = filename[:-4]
                    distance = edit_distance(query.lower(), entry_name.lower())
                    if distance == 0:
                        matched_files.append((entry_name, os.path.join(self.save_folder, filename)))

            if matched_files:
                self.textbox.insert(tk.END, "Exact Match Results:\n")
                for entry_name, file_path in matched_files:
                    self.textbox.insert(tk.END, f"Recording Name: {entry_name}\n")
                    try:
                        with open(file_path, 'r') as file:
                            content = file.read()
                            self.textbox.insert(tk.END, f"{content}\n\n")
                    except IOError as e:
                        self.textbox.insert(tk.END, f"Error reading file: {str(e)}\n\n")
            else:
                suggested_file = None
                for filename in os.listdir(self.save_folder):
                    if filename.endswith('.txt'):
                        entry_name = filename[:-4]
                        distance = edit_distance(query.lower(), entry_name.lower())
                        if distance <= 5:
                            if suggested_file is None or distance < suggested_file[1]:
                                suggested_file = (entry_name, distance, os.path.join(self.save_folder, filename))

                if suggested_file:
                    entry_name, distance, file_path = suggested_file
                    self.textbox.insert(tk.END, "\n\nSuggested File:\n")
                    self.textbox.insert(tk.END, f"Did you mean: {entry_name}?\n")
                    self.textbox.insert(tk.END, f"File Path: {file_path}\n")
                    try:
                        with open(file_path, 'r') as file:
                            content = file.read()
                            self.textbox.insert(tk.END, f"{content}\n\n")
                    except IOError as e:
                        self.textbox.insert(tk.END, f"Error reading file: {str(e)}\n\n")

            if matched_files or suggested_file:
                messagebox.showinfo("Search Result", "Search completed.")
            else:
                messagebox.showinfo("Search Result", "No matching recordings found.")

    def clear_textbox(self):
        self.textbox.delete(1.0, tk.END)
        self.recorded_text = ""
    

class AboutUsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About Us")
        self.geometry("700x300")
        self.configure(bg="#333333")

        about_label1 = tk.Label(self, text="StudioRecord is developed by Raecell Ann & Zeldrick Jesus.\n \n From BSCS-2A",
                                font=("Fixedsys", 12), fg="white", bg="#333333")
        about_label1.pack(pady=10)

        reftitle = tk.Label(self, text="The following links are the references used in this code." 
                            "\n Special Thanks to those developers.\n", 
                            font=("Fixedsys", 12), fg="white", bg="#333333")
        reftitle.pack(pady=10)

        ref1 = tk.Label(self, text="GeeksforGeeks - Python Convert Speech to Text and Text to Speech", 
                        font=("Fixedsys", 12), fg="skyblue", bg="#333333", cursor="hand2")
        ref1.pack(pady=5)
        ref1.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.geeksforgeeks.org/python-convert-speech-to-text-and-text-to-speech/"))

        ref2 = tk.Label(self, text="Fabio Mussani - How to Display and Play a GIF File in Python Tkinter GUIs |\n"
                        "Run and Animate GIFs in Python", 
                        font=("Fixedsys", 12), fg="skyblue", bg="#333333", cursor="hand2")
        ref2.pack(pady=5)
        ref2.bind("<Button-1>", lambda e: webbrowser.open_new("https://youtu.be/KQ0Dddn6sag?si=1_C0BBrXaAk15DTE"))

class MyApp(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.root.title('My App')
        self.root.geometry('1100x600')
        self.root.configure(bg="#333333")
        self.root.resizable(width=True, height=True)

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.content_frame = tk.Frame(self.main_frame, bg="#333333")
        self.content_frame.pack(fill=tk.BOTH, expand=True)


        self.gif_frames = self.load_gif_frames('bg.gif')
        self.current_frame_idx = 0


        self.gif_label = tk.Label(self.content_frame, 
                                  border=0, highlightthickness=0, compound="top")
        self.gif_label.pack(fill=tk.BOTH, expand=True)


        self.clock_label = tk.Label(self.content_frame, 
                                    font=("Fixedsys", 30), fg="white", bg="#333333")
        self.clock_label.place(relx=0.5, rely=0.3, anchor="center")


        self.date_label = tk.Label(self.content_frame, font=("Fixedsys", 12), fg="white", bg="#333333")
        self.date_label.place(relx=0.5, rely=0.4, anchor="center")


        self.menu_button = tk.Button(self.content_frame, text="Open Menu", 
                                     font=("Arial", 12), 
                                     command=self.open_menu, 
                                     bg="#444444", fg="white", 
                                     bd=5, relief="raised")
        self.menu_button.place(relx=0.5, rely=0.5, anchor="center")


        self.main_message = tk.Label(self.content_frame, 
                                     font=("Cambria", 13), fg="white", bg="#333333")
        self.main_message.place(relx=0.5, rely=0.1, anchor="center")


        self.show_next_frame()
        self.update_clock_and_date()
        self.update_main_message()

    def load_gif_frames(self, filename):
        frames = []
        try:
            with Image.open(filename) as gif:
                while True:
                    try:
                        gif_frame = ImageTk.PhotoImage(gif)
                        frames.append(gif_frame)
                        gif.seek(gif.tell() + 1)
                    except EOFError:
                        break
        except Exception as e:
            print(f"Error loading GIF frames: {e}")
        return frames


    def show_next_frame(self):
        if self.current_frame_idx < len(self.gif_frames):
            self.gif_label.config(image=self.gif_frames[self.current_frame_idx])
            self.current_frame_idx += 1
            self.after(100, self.show_next_frame)
        else:
            self.current_frame_idx = 0
            self.after(100, self.show_next_frame)


    def update_clock_and_date(self):
        try:
            current_time = strftime("%H:%M:%S")
            self.clock_label.config(text=current_time)

            current_date = strftime("%A, %B %d, %Y")
            self.date_label.config(text=current_date)

            self.after(1000, self.update_clock_and_date)
        except Exception as e:
            print(f"Error updating clock and date: {e}")


    def update_main_message(self):
        current_hour = int(strftime("%H"))
        if 6 <= current_hour < 12:
            message_text = "Good Morning! Welcome to StudioRecord"
        elif 12 <= current_hour < 18:
            message_text = "Good Afternoon! Welcome to StudioRecord"
        elif 18 <= current_hour < 24:
            message_text = "Good Evening! Welcome to StudioRecord"
        else:
            message_text = "Hello!"
        self.main_message.config(text=message_text)
        self.after(60000, self.update_main_message)


    def open_menu(self):
        menu = tk.Menu(self.root, tearoff=0, bg = "#333333", fg= "white")
        menu.add_command(label="Speech to Text", command=self.option2_action)
        menu.add_separator()
        menu.add_command(label="About Us", command=self.show_about_us)
        menu.add_separator()
        menu.add_command(label="Quit", command=self.root.quit)
        menu.post(self.menu_button.winfo_rootx(), self.menu_button.winfo_rooty() + self.menu_button.winfo_height())


    def option2_action(self):
        self.root.withdraw()
        speech_to_text_app = SpeechToTextApp(tk.Toplevel(self.root))
        speech_to_text_app.pack(fill=tk.BOTH, expand=True)

    def show_about_us(self):
        about_dialog = AboutUsDialog(self.root)



if __name__ == "__main__":
    root = tk.Tk()
    my_app_instance = MyApp(root)
    my_app_instance.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
