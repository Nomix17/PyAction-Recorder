from pynput.mouse import Controller, Button, Listener
from pynput.keyboard import Listener as keylistener
from pynput.keyboard import Key
from pynput.keyboard import Controller as keyController
from threading import Thread, Event
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import time
import os

def replicate(script, replicate_times, delay, stop_event):
    mouse = Controller()
    keyboard = keyController()
    for i in range(0, replicate_times):
        if stop_event.is_set():
            break
        with open(script, 'r') as file:
            content = file.readlines()[:-2]
        with open(script, "w") as file:
            file.write("".join(content))
        with open(script, 'r') as file:
            for line in file.readlines():
                if stop_event.is_set():
                    break
                time.sleep(delay)
                if(line != 0 and line != '\n'):
                    line = line.strip("\n")
                    specs = line.split(";")
                    if("keyboard" in line):
                        key = specs[1].replace("'","").replace("'","").strip()
                        state = "True" == specs[2].strip()
                        if(state):
                            if(len(key) > 1):
                                keyboard.press(getattr(Key, key.replace("Key.","")))
                            else:
                                keyboard.press(key)
                        else:
                            if(len(key) > 1):
                                keyboard.release(getattr(Key, key.replace("Key.","")))
                            else:
                                keyboard.release(key)
                    elif("mouse" in line):
                        button = specs[1].strip(" ")
                        positionx = int(specs[2].split(",")[0])
                        positiony = int(specs[2].split(",")[1])
                        state = "True" == specs[3]
                        mouse.position = (positionx, positiony)
                        if(state):
                            mouse.press(getattr(Button, button))
                        else:
                            mouse.release(getattr(Button, button))

class RecorderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mouse/Keyboard Recorder")
        self.root.geometry("400x350")
        self.root.configure(bg="#101010")

        self.recording = False
        self.current_script = None
        self.record_thread = None
        self.replicate_thread = None
        self.stop_event = None

        self.main_frame = tk.Frame(self.root, padx=20, pady=20, bg="#101010")
        self.main_frame.pack(expand=True, fill='both')

        self.status_label = tk.Label(self.main_frame, text="Status: Ready", font=('Arial', 10), fg="white", bg="#101010")
        self.status_label.pack(pady=10)

        self.script_label = tk.Label(self.main_frame, text="No script loaded", font=('Arial', 10), fg="white", bg="#101010")
        self.script_label.pack(pady=10)

        self.record_button = tk.Button(self.main_frame, text="Start Recording", command=self.toggle_recording, width=20, bg="#202020", fg="white")
        self.record_button.pack(pady=5)

        self.load_button = tk.Button(self.main_frame, text="Load Script", command=self.load_script, width=20, bg="#202020", fg="white")
        self.load_button.pack(pady=5)

        self.rep_frame = tk.LabelFrame(self.main_frame, text="Replication Settings", padx=10, pady=10, bg="#101010", fg="white")
        self.rep_frame.pack(pady=10, fill='x')

        tk.Label(self.rep_frame, text="Times:", bg="#101010", fg="white").grid(row=0, column=0, padx=5)
        self.rep_times = tk.Entry(self.rep_frame, width=10, bg="#202020", fg="white", insertbackground="white")
        self.rep_times.insert(0, "1")
        self.rep_times.grid(row=0, column=1, padx=5)

        tk.Label(self.rep_frame, text="Delay:", bg="#101010", fg="white").grid(row=0, column=2, padx=5)
        self.delay = tk.Entry(self.rep_frame, width=10, bg="#202020", fg="white", insertbackground="white")
        self.delay.insert(0, "0.3")
        self.delay.grid(row=0, column=3, padx=5)

        self.rep_buttons_frame = tk.Frame(self.main_frame, bg="#101010")
        self.rep_buttons_frame.pack(pady=5)

        self.replicate_button = tk.Button(self.rep_buttons_frame, text="Replicate Script", command=self.start_replication, width=20, bg="#202020", fg="white")
        self.replicate_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.rep_buttons_frame, text="Stop Replication", command=self.stop_replication, width=20, bg="#202020", fg="white")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.config(state=tk.DISABLED)

    def toggle_recording(self):
        if not self.recording:
            script_name = simpledialog.askstring("New Recording",
                                               "Enter script name\n(or click Cancel to choose file location):",
                                               parent=self.root)

            if script_name is None:
                filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                      filetypes=[("Text files", "*.txt")])
            else:
                script_name = script_name.strip()
                if not script_name.endswith('.txt'):
                    script_name += '.txt'
                filename = script_name

            if filename:
                self.current_script = filename
                self.script_label.config(text=f"Recording to: {filename}")
                self.recording = True
                self.record_button.config(text="Stop Recording")
                self.status_label.config(text="Status: Recording...")
                self.record_thread = Thread(target=self.record_function, daemon=True)
                self.record_thread.start()
        else:
            self.recording = False
            self.record_button.config(text="Start Recording")
            self.status_label.config(text="Status: Ready")

    def record_function(self):
        def keypress(key):
            if self.recording:
                with open(self.current_script, 'a') as file:
                    file.write(f"keyboard; {key}; True\n")

        def keyreleased(key):
            if self.recording:
                with open(self.current_script, 'a') as file:
                    file.write(f"keyboard; {key}; False\n")

        def mouseclick(x, y, button, pressed):
            if self.recording:
                with open(self.current_script, 'a') as file:
                    file.write(f"mouse; {button.name}; {x},{y};{pressed}\n")

        keyboard_listener = keylistener(on_press=keypress, on_release=keyreleased)
        mouse_listener = Listener(on_click=mouseclick)

        keyboard_listener.start()
        mouse_listener.start()

        while self.recording:
            time.sleep(0.1)

        keyboard_listener.stop()
        mouse_listener.stop()

    def load_script(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filename:
            self.current_script = filename
            self.script_label.config(text=f"Loaded: {filename}")

    def start_replication(self):
        if not self.current_script:
            messagebox.showerror("Error", "Please load a script first!")
            return

        try:
            times = int(self.rep_times.get())
            delay = float(self.delay.get())

            self.status_label.config(text="Status: Replicating...")
            self.stop_event = Event()

            self.replicate_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.root.update()

            self.replicate_thread = Thread(target=self.replicate_function,
                                        args=(times, delay),
                                        daemon=True)
            self.replicate_thread.start()

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for times and delay!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def replicate_function(self, times, delay):
        try:
            replicate(self.current_script, times, delay, self.stop_event)
        finally:
            self.root.after(0, self.replication_finished)

    def replication_finished(self):
        self.status_label.config(text="Status: Ready")
        self.replicate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.stop_event = None

    def stop_replication(self):
        if self.stop_event:
            self.stop_event.set()
            self.status_label.config(text="Status: Stopping...")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = RecorderGUI()
    app.run()
