import os
import requests
from datetime import date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

ATH_PRICE = 126000
ATH_DATE = date(2025, 10, 6)

DASHBOARD_URL = "https://rafko31.github.io/btc-daily-alert/"

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

def color_fg(v):
    if v <= 24:
        return "🟢"
    elif v <= 44:
        return "🟡"
    elif v <= 60:
        return "🟠"
    return "🔴"

def color_ma200(price, ma200):
    if ma200 is None:
        return "⚪"
    diff = (price - ma200) / ma200 * 100
    if diff < 0:
        return "🟢"
    elif diff < 15:
        return "🟡"
    return "🔴"

def color_drawdown(dd):
    if dd >= 60:
        return "🟢"
    elif dd >= 45:
        return "🟡"
    return "🔴"

def color_timing(days):
    if 270 <= days <= 420:
        return "🟢"
    elif 240 <= days < 270:
        return "🟡"
    return "🔴"

def color_score(score):
    if score >= 4:
        return "🟢 FORT SIGNAL"
    elif score == 3:
        return "🟡 Confluence moderee"
    elif score == 2:
        return "🟠 Signaux precoces"
    return "🔴 Bear actif"

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Secrets manquants")

    price, change, ma200 = fetch_btc()
    fg = fetch_fg()

    today = date.today()
    days = (today - ATH_DATE).days
    drawdown = (ATH_PRICE - price) / ATH_PRICE * 100
    days_left = max(0, 365 - days)

    s1 = fg <= 24
    s2 = ma200 is not None and price < ma200
    s3 = drawdown >= 55
    s4 = 270 <= days <= 420
    score = sum([s1, s2, s3, s4])

    arrow = "+" if change >= 0 else ""
    ma_txt = "$" + str(round(ma200)) if ma200 else "N/A"
    ma_diff = round((price - ma200) / ma200 * 100, 1) if ma200 else None
    ma_diff_txt = ("+" + str(ma_diff) + "% au-dessus") if ma_diff and ma_diff >= 0 else (str(ma_diff) + "% en-dessous") if ma_diff else ""

    msg = (
        "==============================\n"
        "BTC CYCLE TRACKER\n"
        + today.strftime("%d/%m/%Y") + " - 8h55 Montreal\n"
        "==============================\n"
        "\n"
        "PRIX & POSITION\n"
        "💰 BTC : $" + str(round(price)) + " (" + arrow + str(round(change, 2)) + "%)\n"
        "📉 Drawdown : -" + str(round(drawdown, 1)) + "% depuis ATH 126k$\n"
        "📊 MA 200j : " + ma_txt + " (" + ma_diff_txt + ")\n"
        "📅 J+" + str(days) + " depuis ATH (bot. hist. ~J+365)\n"
        "\n"
        "SIGNAUX DE RETOURNEMENT\n"
        + color_fg(fg) + " Fear&Greed : " + str(fg) + "/100 - " + fg_label(fg) + "\n"
        + color_ma200(price, ma200) + " MA200j : " + ("Prix SOUS la MA - zone critique" if s2 else "Prix au-dessus MA") + "\n"
        + color_drawdown(drawdown) + " Drawdown : -" + str(round(drawdown, 1)) + "% (seuil signal : -55%)\n"
        + color_timing(days) + " Timing : J+" + str(days) + " (fenetre Oct 2026 = J+270 a J+420)\n"
        "\n"
        "CONFLUENCE\n"
        + color_score(score) + " - " + str(score) + "/4 signaux actifs\n"
        "\n"
        "Dashboard live :\n"
        + DASHBOARD_URL
    )

    requests.post(
        "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
        timeout=15
    )

if __name__ == "__main__":
    main()
