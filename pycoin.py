"""Runs a menu in the macOS menu bar with the top 50 coins from coinmarketcap.com"""

import os
from urllib2 import urlopen, URLError, HTTPError
import time
import json
import copy
import logging
import threading
import requests
import sys
import rumps
# from concurrent.futures import ThreadPoolExecutor, as_completed

default_coin = "bitcoin"
fiat_reference = "USD"
coin_count = "50"
coins_url = 'https://api.coinmarketcap.com/v1/ticker/?convert=USD&limit=50'

def GetCoinsUrl():
    return "https://api.coinmarketcap.com/v1/ticker/?convert=" + fiat_reference + "&limit=" + coin_count

class Currency:
    id = None
    name = None
    symbol = None
    rank = None
    priceUsd = None
    priceBtc = None
    _24hVolumeUsd = None
    marketCapUsd = None
    availableSupply = None
    totalSupply = None
    percentChange1h = None
    percentChange24h = None
    percentChange7d = None
    lastUpdated = None

    logoDownloadThread = None
    logoDownloadSemaphore = threading.Semaphore(1)

    def GetNameWithSymbol(self):
        rVal = self.name
        if self.symbol is not None:
            rVal += " (" + self.symbol + ")"
        return rVal

    def GetSymbolAndUsd(self):
        rVal = ""
        if self.priceUsd is not None:
            rVal = "$" + self.priceUsd

        if self.symbol is not None:
            rVal = "(" + self.symbol + ") " + rVal

        return rVal

    def ToggleMyCoinsMembership(self, sender):
        global my_coins
        if not self.id in my_coins:
            my_coins.append(self.id)
        else:
            del my_coins[my_coins.index(self.id)]

        SaveSettings()
        ProcessCoinsToMenu()


    def SetToMenuItem(self, sender):
        global default_coin
        default_coin = copy.copy(self.id)
        SaveSettings()

        if pycoin is not None:
            pycoin.icon = self.GetIconFile()
            pycoin.title = self.GetSymbolAndUsd()

            if sender is not None:
                ProcessCoinsToMenu();

    def GetIconUrl(self):
        return "https://files.coinmarketcap.com/static/img/coins/64x64/" + self.id + ".png"

    def GetIconFile(self):
        target_file = logos_folder + "/" + os.path.basename(self.GetIconUrl())

        # if self.logoDownloadThread is None or self.logoDownloadThread.isAlive() is False:
        #     self.logoDownloadThread = threading.Thread(target=LogoDownloadWorker, args=(self,))
        #     # self.logoDownloadThread.setDaemon(True)
        #     self.logoDownloadThread.start()
        #     # self.logoDownloadThread.join(timeout=1)

        return target_file

    @staticmethod
    def CurrencyFromTable(tbl):
        rVal = Currency()

        if "id" in tbl:
            rVal.id = tbl["id"]
        if "name" in tbl:
            rVal.name = tbl["name"]
        if "symbol" in tbl:
            rVal.symbol = tbl["symbol"]
        if "rank" in tbl:
            rVal.rank = tbl["rank"]
        if "price_usd" in tbl:
            rVal.priceUsd = tbl["price_usd"]
        if "price_btc" in tbl:
            rVal.priceBtc = tbl["price_btc"]
        if "24h_volume_usd" in tbl:
            rVal._24hVolumeUsd = tbl["24h_volume_usd"]
        if "market_cap_usd" in tbl:
            rVal.marketCapUsd = tbl["market_cap_usd"]
        if "available_supply" in tbl:
            rVal.availableSupply = tbl["available_supply"]
        if "total_supply" in tbl:
            rVal.totalSupply = tbl["total_supply"]
        if "percent_change_1h" in tbl:
            rVal.percentChange1h = tbl["percent_change_1h"]
        if "percent_change_24h" in tbl:
            rVal.percentChange24h = tbl["percent_change_24h"]
        if "percent_change_7d" in tbl:
            rVal.percentChange7d = tbl["percent_change_7d"]
        if "last_updated" in tbl:
            rVal.lastUpdated = tbl["last_updated"]

        return rVal

threads = []
coins_for_logo_download = []
logoDownloadThread = None
def LogoDownloadWorker(coin):
    # time.sleep(1)
    if coin is None:
        return

    coin_logo_url = coin.GetIconUrl()
    target_file = logos_folder + "/" + os.path.basename(coin_logo_url)

    with coin.logoDownloadSemaphore:
        if not os.path.isfile(target_file):
            logging.info("Downloading icon for %s from %s",
                        coin.id, coin_logo_url)
            try:
                r = s.get(coin_logo_url)

                if r.status_code == 200:
                    with open(target_file, "wb") as local_file:
                        for chunk in r.iter_content(chunk_size=128):
                            local_file.write(chunk)

            #handle errors
            except HTTPError, e:
                logging.error("HTTP Error: %s %s", e.code, coin_logo_url)
            except URLError, e:
                logging.error("URL Error: %s %s", e.reason, coin_logo_url)
    return

# @rumps.clicked("Debugging")
def OpenDebugWindow():
    logging.info("should open debugging window")
    rumps.Window(title="Debugging")
    return

coin_update_thread = None
def StartCoinUpdateThread():
    global coin_update_thread
    if (coin_update_thread is None or coin_update_thread.IsAlive() is False):
        coin_update_thread = threading.Thread(target=GetTopCoinsLooper)
        coin_update_thread.setDaemon(True)
        coin_update_thread.start()

def GetTopCoinsLooper():
    while True:
        GetTopCoins()
        time.sleep(300)

# current table goes here
my_coins = []
coins = []
last_updated_time = ""
def GetTopCoins():
    global coins
    global last_updated_time

    try:
        logging.info("Downloading coins from %s", GetCoinsUrl())
        r = s.get(GetCoinsUrl(), timeout=(2, 5))

        if r.status_code == 200:
            jason = r.json()

            del coins[:]

            for c in jason:
                coin = Currency.CurrencyFromTable(c)
                coins.insert(len(coins), coin)
                LogoDownloadWorker(coin)

            last_updated_time = TimeStringForNow()
            ProcessCoinsToMenu()

    except HTTPError, e:
        logging.error("HTTP error loading coins: %s %s", e.code, coins_url)
    except URLError, e:
        logging.error("Error loading url: %s %s", e.reason, coins_url)
    except requests.ConnectionError, e:
        logging.error("Error connecting to url: %s %s", e.reason, coins_url)
    except requests.ConnectTimeout, e:
        logging.error("Connection to url timed out: %s %s", e.reason, coins_url)
    except requests.ReadTimeout, e:
        logging.error("Reading from url timed out: %s %s", e.reason, coins_url)

def ProcessCoinsToMenu():
    global my_coins
    global coins

    new_menu = []
    app_menu = []
    my_coins_menu = []
    all_coins_menu = []

    quit_menu = rumps.MenuItem("Quit", callback=rumps.quit_application)
    app_menu.insert(len(app_menu), quit_menu)

    last_updated = rumps.MenuItem("Updated: " + last_updated_time)
    app_menu.insert(len(app_menu), last_updated)

    app_menu.insert(len(app_menu), None)

    for coin in coins:
        my_coin_toggle = None
        if not coin.id in my_coins:
            my_coin_toggle = rumps.MenuItem("Add to my coins")
        else:
            my_coin_toggle = rumps.MenuItem("Remove from my coins")

        my_coin_toggle.set_callback(coin.ToggleMyCoinsMembership)

        main_coin_select = None
        if coin.id == default_coin:  # this is just setting the sender to None
            coin.SetToMenuItem(None)
        else:
            main_coin_select = rumps.MenuItem(
                "Set as main coin", callback=coin.SetToMenuItem)

        this_coin_submenu = [my_coin_toggle]
        if main_coin_select is not None:
            this_coin_submenu.append(main_coin_select)

        # this_coin_submenu = []

        coin_menu_item = [rumps.MenuItem(coin.GetSymbolAndUsd(), icon=coin.GetIconFile(), callback=coin.SetToMenuItem), this_coin_submenu]

        if not coin.id in my_coins:
            all_coins_menu.insert(len(all_coins_menu), coin_menu_item)
        else:
            my_coins_menu.insert(len(my_coins_menu), coin_menu_item)

    if len(my_coins_menu) > 0:
        my_coins_menu.insert(len(my_coins_menu), None)

    if pycoin is not None:
        pycoin.menu.clear()
        pycoin.menu.update(app_menu + my_coins_menu + all_coins_menu)

def CreateDataFoldersIfNecessary():
    if not os.path.isdir(application_support):
        os.makedirs(application_support)

    if not os.path.isdir(logos_folder):
        os.makedirs(logos_folder)

    return

settings_file = ""
def LoadSettingsOrDefaults():
    if (application_support is None):
        return

    logging.info("Loading settings")
    if not os.path.isfile(settings_file):
        logging.info("Initializing default settings")
        data = {}
        data['defaultCoin'] = "bitcoin"
        data["fiatReference"] = "USD"
        data["coinCount"] = "50"
        data["myCoins"] = []

        with open(settings_file, 'w') as outfile:
            json.dump(data, outfile)

    if os.path.isfile(settings_file):
        logging.info("Reading settings")
        with open(settings_file) as json_file:
            data = json.load(json_file)
            global default_coin
            default_coin = data["defaultCoin"]

            global fiat_reference
            fiat_reference = data["fiatReference"]

            global coin_count
            coin_count = data["coinCount"]

            global my_coins
            my_coins = data["myCoins"]
    return

def SaveSettings():
    if (application_support is None):
        return

    logging.info("Saving settings")
    data = {}

    global default_coin
    data["defaultCoin"] = default_coin

    global fiat_reference
    data["fiatReference"] = fiat_reference

    global coin_count
    data["coinCount"] = coin_count

    global my_coins
    data["myCoins"] = my_coins

    logging.info("Writing settings")
    with open(settings_file, 'w') as outfile:
        json.dump(data, outfile)

def Log(msg):
    return

def TimeStringForNow():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

pycoin = None
application_support = None
logos_folder = "logos"
log_file = "pycoin.log"

is_py2app = hasattr(sys, "frozen")
pem_path = "lib/python2.7/certifi/cacert.pem" if is_py2app else None

s = requests.Session()
s.verify = pem_path

if __name__ == "__main__":
    application_support = rumps.application_support("pycoin")
    logos_folder = application_support + "/" + logos_folder

    CreateDataFoldersIfNecessary()

    logging.basicConfig(filename=application_support + "/" + log_file,
                        level=logging.DEBUG, format='%(asctime)s [%(levelname)s] [%(threadName)-10s] %(message)s')

    logging.info("---APP START---")

    settings_file = application_support + "/settings.json"
    LoadSettingsOrDefaults()
    StartCoinUpdateThread()

    pycoin = rumps.App("PyCoin", title="PyCoin")
    pycoin.run()
