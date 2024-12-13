from flask import Flask, render_template, request
import requests
from cachetools import TTLCache

app = Flask(__name__)

# Cache s TTL (time-to-live) nastaveným na 10 sekúnd
price_cache = TTLCache(maxsize=100, ttl=10)

# Funkcia na získanie aktuálnych cien aktív z Coinbase
def fetch_asset_prices():
    asset_symbols = [
        "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "AVAX",
        "DOGE", "TRX", "LINK", "DOT", "SHIB", "LTC", "BCH", "UNI"
    ]

    prices = {}

    for symbol in asset_symbols:
        if symbol in price_cache:
            prices[symbol] = price_cache[symbol]  # Získať cenu z cache
        else:
            url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
            response = requests.get(url)
            data = response.json()

            if 'data' in data:
                price = float(data['data']['amount'])
                prices[symbol] = round(price, 2)  # Zaokrúhliť cenu na dve desatinné miesta
                price_cache[symbol] = prices[symbol]  # Uložiť cenu do cache
            else:
                prices[symbol] = None  # Ak cena nie je dostupná

    return prices

# Funkcia na výpočet veľkosti pozície na základe pákového efektu a risk manažmentu
def calculate_position_size(account_balance, capital_per_position, leverage, min_notionals):
    minimum_collateral_required = min_notionals / leverage
    collateral_without_leverage = max(capital_per_position, minimum_collateral_required)
    collateral_with_leverage = collateral_without_leverage * leverage
    return collateral_with_leverage, collateral_without_leverage, minimum_collateral_required

# Funkcia na pridanie nového aktíva do kolekcie
def add_new_asset(asset_info, asset_name, max_leverage, min_notional):
    asset_info[asset_name] = {
        'min_notionals': min_notional,
        'max_leverage': max_leverage
    }

# Hlavná stránka s formulármi
@app.route("/", methods=["GET", "POST"])
def home():
    asset_info = {
        'BTCUSDT': {'min_notionals': 100, 'max_leverage': 125},
        'ETHUSDT': {'min_notionals': 20, 'max_leverage': 125},
        'BNBUSDT': {'min_notionals': 5, 'max_leverage': 75},
        'XRPUSDT': {'min_notionals': 5, 'max_leverage': 75},
        'ADAUSDT': {'min_notionals': 5, 'max_leverage': 75},
        'SOLUSDT': {'min_notionals': 5, 'max_leverage': 100},
        'AVAXUSDT': {'min_notionals': 5, 'max_leverage': 75},
        'DOGEUSDT': {'min_notionals': 5, 'max_leverage': 75},
        'TRXUSDT': {'min_notionals': 5, 'max_leverage': 75},
        'LINKUSDT': {'min_notionals': 20, 'max_leverage': 75},
        'DOTUSDT': {'min_notionals': 5, 'max_leverage': 75},
        'LTCUSDT': {'min_notionals': 20, 'max_leverage': 75},
        'BCHUSDT': {'min_notionals': 20, 'max_leverage': 75},
        'UNIUSDT': {'min_notionals': 5, 'max_leverage': 75},
    }

    asset_prices = fetch_asset_prices()  # Získame aktuálne ceny aktív z Coinbase

    if request.method == "POST":
        if "add_asset" in request.form:
            # Pridanie nového aktíva
            asset_name = request.form["asset_name"]
            max_leverage = float(request.form["max_leverage"])
            min_notional = float(request.form["min_notional"])

            add_new_asset(asset_info, asset_name, max_leverage, min_notional)

        elif "calculate" in request.form:
            account_balance = float(request.form["account_balance"])
            max_risk_percent = float(request.form["max_risk_percent"])
            capital_per_position = float(request.form["capital_per_position"])

            # Výpočet maximálneho rizika v percentách z účtu
            max_risk = max_risk_percent  # Už to je zadané v % formáte

            results = []
            total_collateral_needed = 0

            # Pre každý asset vypočítať požiadavky na maržu
            for asset, info in asset_info.items():
                max_leverage = info['max_leverage']
                min_notionals = info['min_notionals']

                collateral_with_leverage, collateral_without_leverage, minimum_collateral_required = calculate_position_size(
                    account_balance, capital_per_position, max_leverage, min_notionals)

                total_collateral_needed += collateral_without_leverage
                results.append({
                    "asset": asset,
                    "max_leverage": max_leverage,
                    "min_notionals": min_notionals,
                    "collateral_without_leverage": collateral_without_leverage,
                    "collateral_with_leverage": collateral_with_leverage,
                    "minimum_collateral_required": minimum_collateral_required,
                    "risk_contribution": (collateral_without_leverage / total_collateral_needed) * 100  # Risk contribution ako percento
                })

            # Výpočet skutočného rizika
            total_collateral_with_leverage = sum([result['collateral_with_leverage'] for result in results])
            actual_risk = (total_collateral_with_leverage / account_balance) * 100  # Skutočné riziko ako percento

            # Zistiť, či je celkové riziko v norme
            risk_status = "Risk is within limits" if total_collateral_needed <= (account_balance * max_risk / 100) else "Risk exceeds limit"

            return render_template("index.html", results=results, max_risk=max_risk,
                                   total_collateral_needed=total_collateral_needed, actual_risk=actual_risk,
                                   risk_status=risk_status, asset_info=asset_info, asset_prices=asset_prices)

    return render_template("index.html", results=[], asset_info=asset_info, asset_prices=asset_prices)


if __name__ == "__main__":
    app.run(debug=True)
