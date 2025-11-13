# jarvis_firewall.py
from pathlib import Path
import json
import socket
import time

# ------------------ Tűzfal konfiguráció ------------------
DATA_DIR = Path("jarvis_full_data")
DATA_DIR.mkdir(exist_ok=True)
FIREWALL_FILE = DATA_DIR / "firewall_rules.json"
LOG_FILE = DATA_DIR / "firewall_log.json"

# Alapértelmezett szabályok
DEFAULT_RULES = {
    "allowed_ips": ["127.0.0.1", "localhost"],
    "blocked_ips": [],
    "allowed_ports": [8080, 5000, 3000],
    "max_connections": 100,
    "enabled": True
}

# ------------------ Tűzfal inicializálás ------------------
def initialize_firewall():
    if not FIREWALL_FILE.exists():
        try:
            with open(FIREWALL_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_RULES, f, indent=2, ensure_ascii=False)
            print("✓ Tűzfal szabályok inicializálva.")
        except Exception as e:
            print(f"Tűzfal inicializálási hiba: {e}")

# ------------------ Szabályok betöltése ------------------
def load_rules():
    initialize_firewall()
    try:
        with open(FIREWALL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Szabályok betöltési hiba: {e}")
        return DEFAULT_RULES

# ------------------ Tűzfal ellenőrzés ------------------
def firewall_check(ip=None, port=None):
    """
    Ellenőrzi, hogy az IP és port engedélyezett-e.
    """
    rules = load_rules()
    
    if not rules.get("enabled", True):
        print("⚠ Tűzfal ki van kapcsolva!")
        return True
    
    # Ha nincs IP megadva, akkor helyi ellenőrzés
    if ip is None:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except:
            ip = "127.0.0.1"
    
    # Blokkolt IP ellenőrzés
    if ip in rules.get("blocked_ips", []):
        log_event("BLOCKED", ip, port, "IP blokkolt")
        print(f"✗ Tűzfal: IP blokkolt: {ip}")
        return False
    
    # Engedélyezett IP ellenőrzés
    if ip not in rules.get("allowed_ips", []) and ip != "127.0.0.1":
        log_event("DENIED", ip, port, "IP nem engedélyezett")
        print(f"✗ Tűzfal: IP nem engedélyezett: {ip}")
        return False
    
    # Port ellenőrzés
    if port and port not in rules.get("allowed_ports", []):
        log_event("DENIED", ip, port, "Port nem engedélyezett")
        print(f"✗ Tűzfal: Port nem engedélyezett: {port}")
        return False
    
    log_event("ALLOWED", ip, port, "Hozzáférés engedélyezve")
    print(f"✓ Tűzfal: Hozzáférés engedélyezve: {ip}:{port if port else 'N/A'}")
    return True

# ------------------ Esemény naplózás ------------------
def log_event(action, ip, port, message):
    try:
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "ip": ip,
            "port": port,
            "message": message
        }
        
        logs = []
        if LOG_FILE.exists():
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        
        # Csak az utolsó 1000 eseményt tároljuk
        logs = logs[-1000:]
        
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Log esemény hiba: {e}")

# ------------------ IP hozzáadása az engedélyezettekhez ------------------
def add_allowed_ip(ip):
    rules = load_rules()
    if ip not in rules.get("allowed_ips", []):
        rules["allowed_ips"].append(ip)
        try:
            with open(FIREWALL_FILE, "w", encoding="utf-8") as f:
                json.dump(rules, f, indent=2, ensure_ascii=False)
            print(f"✓ IP engedélyezve: {ip}")
        except Exception as e:
            print(f"IP hozzáadási hiba: {e}")

# ------------------ IP blokkolás ------------------
def block_ip(ip):
    rules = load_rules()
    if ip not in rules.get("blocked_ips", []):
        rules["blocked_ips"].append(ip)
        try:
            with open(FIREWALL_FILE, "w", encoding="utf-8") as f:
                json.dump(rules, f, indent=2, ensure_ascii=False)
            print(f"✓ IP blokkolva: {ip}")
        except Exception as e:
            print(f"IP blokkolási hiba: {e}")