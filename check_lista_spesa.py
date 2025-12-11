import json
import os
import requests
import firebase_admin
from firebase_admin import credentials, db

# ============================
# 1) INIZIALIZZA FIREBASE
# ============================
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": os.getenv("FIREBASE_DB_URL")
})

# ============================
# 2) LEGGE LA LISTA DAL DB
# ============================
ref = db.reference("shoppingList")
current_data = ref.get() or {}

# Converti in lista leggibile
current_items = [{
    "id": key,
    "name": value.get("name"),
    "addedAt": value.get("addedAt")
} for key, value in current_data.items()]

# ============================
# 3) CARICA LA CACHE
# ============================
CACHE_FILE = "lista_spesa_cache.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        previous_items = json.load(f)
else:
    previous_items = []

# ============================
# 4) TROVA GLI ELEMENTI NUOVI
# ============================
prev_ids = {item["id"] for item in previous_items}
new_items = [item for item in current_items if item["id"] not in prev_ids]

# ============================
# 5) INVIA MESSAGGI TELEGRAM
# ============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# Invia notifica per ogni nuovo prodotto
for item in new_items:
    message = f"🛒 *Nuovo prodotto aggiunto alla lista!*\n\n👉 {item['name']}"
    send_telegram(message)

# ============================
# 6) AGGIORNA LA CACHE
# ============================
with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(current_items, f, indent=2)

print("Controllo completato.")
