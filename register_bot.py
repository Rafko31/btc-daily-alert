import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def get_updates(offset=None):
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    r = requests.get(
        "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/getUpdates",
        params=params,
        timeout=15
    )
    return r.json().get("result", [])

def send_message(chat_id, text):
    requests.post(
        "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
        data={"chat_id": chat_id, "text": text},
        timeout=15
    )

def main():
    updates = get_updates()
    for update in updates:
        msg = update.get("message", {})
        text = msg.get("text", "")
        chat_id = str(msg.get("chat", {}).get("id", ""))
        first_name = msg.get("from", {}).get("first_name", "Inconnu")

        if text.strip() == "/start" and chat_id:
            # Réponse à l'abonné
            send_message(chat_id,
                "Bonjour " + first_name + " !\n"
                "Tu es inscrit au BTC Cycle Tracker.\n"
                "Tu recevras les alertes quotidiennes chaque matin.\n\n"
                "Ton ID : " + chat_id
            )
            # Notification à l'admin
            send_message(ADMIN_CHAT_ID,
                "Nouvel abonne BTC Tracker !\n"
                "Nom : " + first_name + "\n"
                "Chat ID : " + chat_id + "\n\n"
                "Ajoute ce chat_id a la liste CHAT_IDS dans btc_notify.py"
            )

if __name__ == "__main__":
    main()
