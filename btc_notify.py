import os
import requests
from datetime import date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "VOTRE_TOKEN_BOT_ICI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "VOTRE_CHAT_ID_ICI")

ATH_PRICE = 126000
ATH_DATE = date(2025, 10, 6)
BOTTOM_WINDOW_START = 270
BOTTOM_WINDOW_END = 420

def fetch_btc():
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        },
        timeout=15
    )
    r.raise_for_status()
    data = r.json()["bitcoin"]
    price = data["usd"]
    change = data.get("usd_24h_change", 0)

    hist = requests.get(
        "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
        params={"vs_currency": "usd", "days": "210", "interval": "daily"},
        timeout=15
    )
    hist.raise_for_status()
    prices_list = [p[1] for p in hist.json()["prices"]]
    ma200 = sum(prices_list[-200:]) / 200 if len(prices_list) >= 200 else None
    return price, change, ma200

def fetch_fear_greed():
    r = requests.get("https://api.alternative.me/fng/?limit=1&format=json", timeout=10)
    r.raise_for_status()
    return int(r.json()["data"][0]["value"])

def fetch_gold():
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=XAU&to=USD", timeout=10)
        r.raise_for_status()
        return r.json()["rates"]["USD"]
    except Exception:
        return None

def fg_label(v):
    if v <= 24:
        return "Extreme Fear"
    if v <= 44:
        return "Fear"
    if v <= 55:
        return "Neutral"
    if v <= 74:
        return "Greed"
    return "Extreme Greed"

def signal_dot(active):
    if active is True:
        return "🟢"
    if active is False:
        return "🔴"
    return "🟡"

def build_message(price, change24, ma200, fg, gold):
    today = date.today()
    days_since = (today - ATH_DATE).days
    drawdown = (ATH_PRICE - price) / ATH_PRICE * 100
    days_left = max(0, 365 - days_since)

    sig_fg = fg is not None and fg < 30
    sig_ma200 = ma200 is not None and price < ma200
    sig_drawdown = drawdown >= 55
    sig_timing = BOTTOM_WINDOW_START <= days_since <= BOTTOM_WINDOW_END
    sig_gold = gold is not None and gold > 2800

    signals = [
        (sig_fg, f"Fear & Greed < 30 : {fg}/100 ({fg_label(fg)})"),
        (sig_ma200, f"Sous MA200j : {'Oui' if sig_ma200 else 'Non'} (MA200=${ma200:,.0f})" if ma200 else "MA200 indisponible"),
        (sig_drawdown, f"Drawdown >= 55% : -{drawdown:.1f}% depuis ATH"),
        (sig_timing, f"Fenetre temporelle : J+{days_since}/365 (~{days_left}j restants)"),
        (sig_gold, f"Or > 2800$ : {'Oui' if sig_gold else 'Non'} ({gold:,.0f}$/oz)" if gold else "Or indisponible"),
    ]

    score = sum(1 for s, _ in signals if s is True)

    if score <= 1:
        confluence = "Bear Market actif - observer"
    elif score <= 3:
        confluence = "Signaux precoces - surveiller"
    elif score <= 4:
        confluence = "Confluence moderee - attention"
    else:
        confluence = "FORT SIGNAL DE RETOURNEMENT"

    change_arrow = "▲" if change24 >= 0 else "▼"
    change_sign = "+" if change24 >= 0 else ""

    lines = [
        f"BTC Cycle Tracker - {today.strftime('%d/%m/%Y')}",
        "",
        f"Prix BTC : ${price:,.0f} {change_arrow} {change_sign}{change24:.2f}%",
        f"Drawdown ATH : -{drawdown:.1f}% (ATH 126k$ oct. 2025)",
        f"MA 200 jours : ${ma200:,.0f}" if ma200 else "MA 200 jours : -",
        "",
        "SIGNAUX DE RETOURNEMENT",
        "",
    ]

    for s, label in signals:
        lines.append(f"{signal_dot(s)} {label}")

    lines += [
        "",
        f"Score confluence : {score}/5",
        f"Statut : {confluence}",
        f"Fenetre bottom historique : ~Oct 2026 (J+{days_since}/365)",
    ]

    return "\\n".join(lines)

def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    r = requests.post(url, data=data, timeout=15)
    r.raise_for_status()
    return r.json()

def main():
    price, change24, ma200 = fetch_btc()
    fg = fetch_fear_greed()
    gold = fetch_gold()
    msg = build_message(price, change24, ma200, fg, gold)

    if TELEGRAM_TOKEN == "VOTRE_TOKEN_BOT_ICI":
        raise ValueError("TELEGRAM_TOKEN non configure")
    if TELEGRAM_CHAT_ID == "VOTRE_CHAT_ID_ICI":
        raise ValueError("TELEGRAM_CHAT_ID non configure")

    send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg)

if __name__ == "__main__":
    main()
