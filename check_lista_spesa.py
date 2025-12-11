# check_lista_spesa.py
import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, db

# --- Config da env (setta in GitHub Secrets)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "").rstrip('/')

if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID and FIREBASE_DB_URL):
    raise SystemExit("Missing TELEGRAM_TOKEN, TELEGRAM_CHAT_ID or FIREBASE_DB_URL env vars")

TELEGRAM_SEND_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
CACHE_FILE = "lista_spesa_cache.json"
DB_PATH = "shoppingList"   # path usato nella tua index.html

def send_telegram(text):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(TELEGRAM_SEND_URL, data=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print("Errore invio Telegram:", e)
        return False

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def main():
    # init firebase (firebase-key.json deve essere presente)
    cred = credentials.Certificate("firebase-key.json")
    # se già inizializzato, riutilizza l'app
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

    ref = db.reference(DB_PATH)
    snapshot = ref.get() or {}

    # snapshot: dict {id: {name:..., ...}}
    existing_ids = load_cache()    # lista di doc id già notificati
    new_ids = []
    new_items = []

    # snapshot may be dict or other; iterate safely
    if isinstance(snapshot, dict):
        for key, val in snapshot.items():
            # consider only entries with name field
            name = None
            if isinstance(val, dict):
                name = val.get("name") or val.get("nome") or val.get("title")
            else:
                # if value is string
                name = str(val)
            if not name:
                continue
            if key not in existing_ids:
                new_ids.append(key)
                new_items.append(name)
    else:
        print("No items or unexpected data shape in DB:", type(snapshot))

    if new_items:
        # format message
        lines = [f"🛒 *Nuovi elementi aggiunti alla lista:*"]
        for n in new_items:
            lines.append(f"• {n}")
        text = "\n".join(lines)
        ok = send_telegram(text)
        if ok:
            # aggiorna cache aggiungendo i nuovi id
            cache = existing_ids + new_ids
            save_cache(cache)
            print("Notificati e cache salvata:", new_items)
        else:
            print("Invio Telegram fallito, cache non aggiornata.")
    else:
        print("Nessun nuovo elemento da notificare.")

if __name__ == "__main__":
    main()
