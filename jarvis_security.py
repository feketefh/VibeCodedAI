# jarvis_security.py
from pathlib import Path
import json

# ------------------ Felhasználói adat mappa ------------------
DATA_DIR = Path("jarvis_full_data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "authorized_users.json"

# ------------------ Alapértelmezett felhasználó létrehozása ------------------
def initialize_users():
    if not USERS_FILE.exists():
        default_users = {"users": ["admin"]}
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Felhasználói adat mentési hiba:", e)

# ------------------ Engedélyezett felhasználó ellenőrzése ------------------
def security_check(username="admin"):
    """
    Ellenőrzi, hogy a felhasználó engedélyezett-e.
    """
    initialize_users()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if username in data.get("users", []):
            print(f"✓ Hozzáférés engedélyezve: {username}")
            return True
        else:
            print(f"✗ Hozzáférés megtagadva: {username} nem engedélyezett.")
            return False
    except Exception as e:
        print("Security check hiba:", e)
        return False

# ------------------ Felhasználó hozzáadása ------------------
def add_user(username):
    initialize_users()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if username not in data.get("users", []):
            data["users"].append(username)
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Felhasználó hozzáadva: {username}")
        else:
            print(f"Felhasználó már létezik: {username}")
    except Exception as e:
        print("Add user hiba:", e)

# ------------------ Felhasználó eltávolítása ------------------
def remove_user(username):
    initialize_users()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if username in data.get("users", []):
            data["users"].remove(username)
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Felhasználó eltávolítva: {username}")
        else:
            print(f"Felhasználó nem található: {username}")
    except Exception as e:
        print("Remove user hiba:", e)

# ------------------ Felhasználók listázása ------------------
def list_users():
    initialize_users()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("users", [])
    except Exception as e:
        print("List users hiba:", e)
        return []