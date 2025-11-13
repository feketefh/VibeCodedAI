# jarvis_ui.py
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue

# Text-to-Speech
TTS_AVAILABLE = False
try:
    import pyttsx3
    TTS_AVAILABLE = True
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
except Exception as e:
    print(f"TTS nem elérhető: {e}")

# ------------------ Beszéd funkció ------------------
def speak(text):
    """
    Kimondja a szöveget (ha TTS elérhető).
    """
    print(f"[JARVIS]: {text}")
    if TTS_AVAILABLE:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS hiba: {e}")

# ------------------ Jarvis GUI ------------------
class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS AI Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg="#1a1a1a")
        
        # Címke
        self.title_label = tk.Label(
            self.root,
            text="J.A.R.V.I.S. Interface",
            font=("Arial", 24, "bold"),
            fg="#00ff00",
            bg="#1a1a1a"
        )
        self.title_label.pack(pady=20)
        
        # Chat ablak
        self.chat_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.chat_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            height=20,
            width=90,
            bg="#0a0a0a",
            fg="#00ff00",
            font=("Courier New", 10),
            insertbackground="#00ff00",
            wrap=tk.WORD
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input mező
        self.input_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.input_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.input_entry = tk.Entry(
            self.input_frame,
            font=("Arial", 12),
            bg="#2a2a2a",
            fg="#00ff00",
            insertbackground="#00ff00",
            width=60
        )
        self.input_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_button = tk.Button(
            self.input_frame,
            text="Küldés",
            font=("Arial", 12, "bold"),
            bg="#00aa00",
            fg="white",
            command=self.send_message,
            width=10
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Üzenet queue
        self.message_queue = queue.Queue()
        
        # Kezdő üzenet
        self.add_message("JARVIS", "Üdvözlöm! Miben segíthetek?")
        
    def add_message(self, sender, message):
        """
        Üzenet hozzáadása a chat ablakhoz.
        """
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[{sender}]: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def send_message(self):
        """
        Felhasználói üzenet elküldése.
        """
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        self.add_message("TE", user_input)
        self.input_entry.delete(0, tk.END)
        
        # Válasz generálása háttérben
        threading.Thread(
            target=self.process_input,
            args=(user_input,),
            daemon=True
        ).start()
        
    def process_input(self, user_input):
        """
        Felhasználói input feldolgozása.
        """
        from jarvis_logic import decide_action
        
        response = decide_action(user_input)
        self.add_message("JARVIS", response)
        
        # TTS kimondás
        threading.Thread(target=speak, args=(response,), daemon=True).start()
        
    def run(self):
        """
        GUI fő loop indítása.
        """
        self.root.mainloop()

# ------------------ Tesztfuttatás ------------------
if __name__ == "__main__":
    speak("JARVIS inicializálása...")
    gui = JarvisGUI()
    gui.run()