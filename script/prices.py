import requests
import time
import platform
from tabulate import tabulate


def fetch_asset_prices():
    # Zoznam aktív, ktoré chceme sledovať
    asset_ids = [
        "bitcoin", "ethereum", "binancecoin", "ripple", "cardano", "solana", "avalanche-2",
        "dogecoin", "tron", "chainlink", "polkadot", "shiba-inu", "litecoin", "bitcoin-cash", "uniswap"
    ]
    prices = {}
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(asset_ids)}&vs_currencies=usd"

    # Získavame dáta z API
    response = requests.get(url)

    # Skontrolujeme odpoveď
    print("API Response:", response.json())  # Diagnostika

    data = response.json()

    # Extrahujeme ceny pre každé aktívum, zabezpečíme, že ak nie sú dostupné, použije sa "N/A"
    for asset in asset_ids:
        prices[asset] = data.get(asset, {}).get('usd', "N/A")

    return prices


def display_prices(prices, history):
    headers = ["Asset", "Current Price (USD)", "History (Last Price)"]

    # Ukladáme len poslednú cenu (história je len posledná aktualizácia)
    for asset in prices.keys():
        history[asset] = prices[asset]  # Ukladáme poslednú cenu ako históriu

    # Pripravíme dáta pre tabuľku
    table = []
    for asset, price in prices.items():
        history_str = str(history[asset])  # Zobrazujeme iba poslednú cenu
        table.append([asset, price, history_str])

    # Vyčistenie obrazovky
    if platform.system().lower() == "windows":
        print("\033c", end="")  # Vyčistenie obrazovky na Windows
    else:
        print("\033[H\033[J", end="")  # Vyčistenie obrazovky na Linux/Mac

    # Zobrazenie tabuľky
    print(tabulate(table, headers=headers, tablefmt="grid", numalign="right", stralign="center"))


try:
    history = {}  # Ukladanie poslednej ceny pre každý asset
    while True:
        prices = fetch_asset_prices()  # Získanie aktuálnych cien

        # Zobrazenie cien a histórie v tabuľke
        display_prices(prices, history)

        time.sleep(30)  # Čakáme 30 sekúnd pred ďalším požiadavkom
except KeyboardInterrupt:
    print("\nProgram bol prerušený. Zastavujem...")