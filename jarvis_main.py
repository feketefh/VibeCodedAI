# jarvis_main.py
import threading
import time

# ------------------ Modulok importálása ------------------
from jarvis_boot import main as boot_main               # Boot GUI
from jarvis_ui import JarvisGUI, speak               # GUI + TTS + animált fej
from jarvis_3d_advanced import generate_material_preview  # 3D anyag generálás
from jarvis_vision import start_vision                 # Kamera + objektumfelismerés

# ------------------ Fő futtató függvény ------------------
def run_all():
    # 1️⃣ Boot GUI elindítása külön szálon
    boot_thread = threading.Thread(target=boot_main, daemon=True)
    boot_thread.start()

    # 2️⃣ Várunk, amíg a boot lefut (kb. 3 másodperc)
    time.sleep(3)

    # 4️⃣ Fő GUI indítása
    gui = JarvisGUI()

    # 5️⃣ Háttér 3D anyag generálás
    threading.Thread(
        target=lambda: generate_material_preview("Titanium", "cube", 2.0),
        daemon=True
    ).start()

    # 6️⃣ Háttér objektumfelismerés kamera használatával
    threading.Thread(target=start_vision, daemon=True).start()

    ## 7️⃣ GUI fő loop
    gui.run()

# ------------------ Belépési pont ------------------
if __name__ == "__main__":
    run_all()
