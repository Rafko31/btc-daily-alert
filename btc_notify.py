import os
import requests
from datetime import date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

ATH_PRICE = 126000
ATH_DATE = date(2025, 10, 6)

def fetch_btc():
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"},
        timeout=15
    )
    data = r.json()["bitcoin"]
    price = data["usd"]
    change = data.get("usd_24h_change", 0)
    hist = requests.get(
        "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
        params={"vs_currency": "usd", "days": "210", "interval": "daily"},
        timeout=15
    ).json()
    prices = [p[1] for p in hist["prices"]]
    ma200 = sum(prices[-200:]) / 200 if len(prices) >= 200 else None
    return price, change, ma200

def fetch_fg():
    r = requests.get("https://api.alternative.me/fng/?limit=1&format=json", timeout=10)
    return int(r.json()["data"][0]["value"])

def fg_label(v):
    if v <= 24:
        return "Extreme Fear"
    elif v <= 44:
        return "Fear"
    elif v <= 55:
        return "Neutral"
    elif v <= 74:
        return "Greed"
    return "Extreme Greed"

def dot(active):
    if active is True:
        return "OK"
    if active is False:
        return "--"
    return "??"

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Secrets manquants")

    price, change, ma200 = fetch_btc()
    fg = fetch_fg()

    today = date.today()
    days = (today - ATH_DATE).days
    drawdown = (ATH_PRICE - price) / ATH_PRICE * 100
    days_left = max(0, 365 - days)

    s1 = fg < 30
    s2 = ma200 is not None and price < ma200
    s3 = drawdown >= 55
    s4 = 270 <= days <= 420
    score = sum([s1, s2, s3, s4])

    arrow = "+" if change >= 0 else ""
    ma_txt = str(round(ma200)) if ma200 else "N/A"

    msg = (
        "BTC Cycle Tracker - " + today.strftime("%d/%m/%Y") + "\n"
        "\n"
        "Prix : $" + str(round(price)) + " (" + arrow + str(round(change, 2)) + "%)\n"
        "Drawdown ATH : -" + str(round(drawdown, 1)) + "%\n"
        "MA 200 jours : $" + ma_txt + "\n"
        "J+" + str(days) + " depuis ATH\n"
        "\n"
        "SIGNAUX\n"
        + dot(s1) + " Fear&Greed < 30 : " + str(fg) + "/100 (" + fg_label(fg) + ")\n"
        + dot(s2) + " Sous MA200j\n"
        + dot(s3) + " Drawdown >= 55%\n"
        + dot(s4) + " Fenetre Oct 2026 (~" + str(days_left) + "j)\n"
        "\n"
        "Score : " + str(score) + "/4\n"
        "Bottom historique : ~Oct 2026"
    )

    requests.post(
        "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
        timeout=15
    )

if __name__ == "__main__":
    main()
