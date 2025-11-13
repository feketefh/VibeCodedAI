# jarvis_boot.py
import tkinter as tk
from tkinter import ttk
import time
import threading

class BootSequence:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS Boot Sequence")
        self.root.geometry("600x400")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(False, False)
        
        # Címke
        self.title_label = tk.Label(
            self.root,
            text="J.A.R.V.I.S.",
            font=("Courier New", 36, "bold"),
            fg="#00ff00",
            bg="#0a0a0a"
        )
        self.title_label.pack(pady=30)
        
        # Alcím
        self.subtitle_label = tk.Label(
            self.root,
            text="Just A Rather Very Intelligent System",
            font=("Courier New", 12),
            fg="#00aa00",
            bg="#0a0a0a"
        )
        self.subtitle_label.pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=400,
            mode="determinate"
        )
        self.progress.pack(pady=40)
        
        # Status szöveg
        self.status_text = tk.Text(
            self.root,
            height=10,
            width=70,
            bg="#0a0a0a",
            fg="#00ff00",
            font=("Courier New", 9),
            insertbackground="#00ff00"
        )
        self.status_text.pack(pady=10)
        self.status_text.config(state=tk.DISABLED)
        
        # Boot üzenetek
        self.boot_messages = [
            "[INIT] Rendszerindítás...",
            "[LOAD] Kernelmodulok betöltése...",
            "[CHECK] Biztonsági protokollok ellenőrzése...",
            "[LOAD] Neurális hálózat inicializálása...",
            "[CHECK] Tűzfal szabályok betöltése...",
            "[LOAD] Beszédszintézis modul betöltése...",
            "[LOAD] Látásrendszer inicializálása...",
            "[CHECK] 3D motor ellenőrzése...",
            "[LOAD] Memória rendszer betöltése...",
            "[READY] Minden rendszer működőképes!",
            "[BOOT] J.A.R.V.I.S. online."
        ]
        
    def add_message(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
        
    def boot_sequence(self):
        total_steps = len(self.boot_messages)
        for i, message in enumerate(self.boot_messages):
            self.add_message(message)
            self.progress["value"] = ((i + 1) / total_steps) * 100
            time.sleep(0.3)
        
        time.sleep(1)
        self.root.destroy()
        
    def run(self):
        # Boot sequence külön szálon
        boot_thread = threading.Thread(target=self.boot_sequence, daemon=True)
        boot_thread.start()
        self.root.mainloop()

def main():
    boot = BootSequence()
    boot.run()

if __name__ == "__main__":
    main()