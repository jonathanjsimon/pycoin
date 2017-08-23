"""Runs a menu in the macOS menu bar with the top x (selected in preferences) coins from coinmarketcap.com"""

import os
import time
import json
import copy
import logging
import threading
import requests
import sys
import rumps

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
            pycoin.icon = self.GetIconFilePath()
            pycoin.title = self.GetSymbolAndUsd()

            if sender is not None:
                ProcessCoinsToMenu();

    def GetIconUrl(self):
        return "https://files.coinmarketcap.com/static/img/coins/64x64/" + self.id + ".png"

    def GetIconFilePath(self):
        return logos_folder + "/" + self.id + ".png"

    def DownloadCoinIcon(self):
        coin_logo_url = self.GetIconUrl()
        target_file = logos_folder + "/" + os.path.basename(coin_logo_url)

        with self.logoDownloadSemaphore:
            if not os.path.isfile(target_file):
                logging.info("Downloading icon for %s from %s", self.id, coin_logo_url)
                try:
                    r = s.get(coin_logo_url, timeout=(2, 5))

                    if r.status_code == requests.codes.ok:
                        with open(target_file, "wb") as local_file:
                            for chunk in r.iter_content(chunk_size=128):
                                local_file.write(chunk)

                except requests.ConnectionError, e:
                    logging.error("Error connecting to url: %s", coin_logo_url)
                except requests.ConnectTimeout, e:
                    logging.error(
                        "Connection to url timed out: %s ", coin_logo_url)
                except requests.ReadTimeout, e:
                    logging.error("Reading from url timed out: %s", coin_logo_url)

    def GetCoinDetailsAsMenuItems(self):
        details = []

        if not self.name is None:
            details.insert(len(details), rumps.MenuItem("Name: " + self.name))
        if not self.rank is None:
            details.insert(len(details), rumps.MenuItem("Rank: " + self.rank))
        if not self.priceBtc is None:
            details.insert(len(details), rumps.MenuItem(u"BTC: \u20BF" + self.priceBtc))
        if not self._24hVolumeUsd is None:
            details.insert(len(details), rumps.MenuItem("24hr Volume: " + self._24hVolumeUsd))
        if not self.marketCapUsd is None:
            details.insert(len(details), rumps.MenuItem("Market Cap USD: $" + self.marketCapUsd))
        if not self.availableSupply is None:
            details.insert(len(details), rumps.MenuItem("Available: " + self.availableSupply))
        if not self.totalSupply is None:
            details.insert(len(details), rumps.MenuItem("Total: " + self.totalSupply))
        if not self.percentChange1h is None:
            details.insert(len(details), rumps.MenuItem(u"1h \u0394: " + self.percentChange1h + "%"))
        if not self.percentChange24h is None:
            details.insert(len(details), rumps.MenuItem(u"24h \u0394: " + self.percentChange24h + "%"))
        if not self.percentChange7d is None:
            details.insert(len(details), rumps.MenuItem(u"7d \u0394: " + self.percentChange7d + "%"))

        return details

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


# @rumps.clicked("Debugging")
debug_window = None
def OpenDebugWindow(sender):
    global debug_window
    logging.info("should open debugging window")
    debug_window = rumps.Window(message="Foo", title="Debugging", default_text='Bar', dimensions=(320, 160))
    debug_window.run()
    return


default_coin = "bitcoin"
fiat_reference = "USD"
coin_count = 50

def SetCoinCount(sender):
    global coin_count
    global coin_update_event

    logging.debug("Setting coin count to %s", str(sender.title))
    new_coin_count = int(sender.title)
    if not new_coin_count is None:
        coin_count = new_coin_count
        coin_update_event.set()

def GetCoinsUrl():
    global fiat_reference
    global coin_coin
    return "https://api.coinmarketcap.com/v1/ticker/?convert=" + fiat_reference + "&limit=" + str(coin_count)

def GetSpecificCoinUrl(coinId):
    global fiat_reference
    return "https://api.coinmarketcap.com/v1/ticker/" + coinId + "/?convert=" + fiat_reference

def GetJsonResponseForUrl(url):
    rVal = None
    try:
        r = s.get(url, timeout=(2, 5))

        if r.status_code == requests.codes.ok:
            rVal = r.json()
    except requests.ConnectionError, e:
        logging.error("Error connecting to url: %s", url)
    except requests.ConnectTimeout, e:
        logging.error("Connection to url timed out: %s ", url)
    except requests.ReadTimeout, e:
        logging.error("Reading from url timed out: %s", url)

    return rVal

def AddMissingCoinToCoins(coinId):
    global coins

    logging.info("%s missing from main list, must retrieve", default_coin)
    coin_json = GetJsonResponseForUrl(GetSpecificCoinUrl(default_coin))
    if not coin_json is None and not "error" in coin_json:
        logging.debug("Retrieved %s", default_coin)
        true_coin = coin_json[0]
        if not true_coin is None:
            curr = Currency.CurrencyFromTable(true_coin)
            curr.DownloadCoinIcon()
            coins.append(curr)

coin_update_thread = None
def StartCoinUpdateThread():
    global coin_update_thread
    if (coin_update_thread is None or coin_update_thread.IsAlive() is False):
        coin_update_thread = threading.Thread(target=GetTopCoinsLooper)
        coin_update_thread.setDaemon(True)
        coin_update_thread.start()

coin_update_event = threading.Event()
def GetTopCoinsLooper():
    global coin_update_event

    while coin_update_event.wait(timeout=300):
        coin_update_event.clear()
        GetTopCoins()
        # time.sleep(300)

# current table goes here
my_coins = []
coins = []
last_updated_time = ""
def GetTopCoins():
    global coins
    global last_updated_time

    logging.info("Downloading coins from %s", GetCoinsUrl())
    coins_json = GetJsonResponseForUrl(GetCoinsUrl())

    if not coins_json is None:
        del coins[:]

        for c in coins_json:
            coin = Currency.CurrencyFromTable(c)
            coins.insert(len(coins), coin)
            coin.DownloadCoinIcon()

        last_updated_time = TimeStringForNow()
        ProcessCoinsToMenu()


def ProcessCoinsToMenu():
    global my_coins
    global coins
    global coin_count

    new_menu = []
    app_menu = []
    my_coins_menu = []
    all_coins_menu = []

    last_updated = rumps.MenuItem("Updated: " + last_updated_time)
    app_menu.insert(len(app_menu), last_updated)

    coin_count_options = []
    for count in [10, 25, 50, 100]:
        count_selected = 0
        if count == coin_count:
            count_selected = 1

        new_coin_count_option = rumps.MenuItem(count, callback=SetCoinCount)
        new_coin_count_option.state = count_selected

        coin_count_options.append(new_coin_count_option)

    coin_count_menu = [rumps.MenuItem("Coin Count"), coin_count_options]
    app_menu.insert(len(app_menu), coin_count_menu)

    # debug_menu_window = rumps.MenuItem("Debugging", callback=OpenDebugWindow)
    # app_menu.insert(len(app_menu), debug_menu_window)

    quit_menu = rumps.MenuItem("Quit", callback=rumps.quit_application)
    app_menu.insert(len(app_menu), quit_menu)

    app_menu.insert(len(app_menu), None)

    result = None
    for coin in my_coins:
        result = next(iter(filter(lambda x: x.id == coin, coins)), None)
        if result is None:
            AddMissingCoinToCoins(coin)

    has_main_coin = next(iter(filter(lambda x: x.id == default_coin, coins)), None)
    if has_main_coin is None:
        AddMissingCoinToCoins(default_coin)

    for coin in coins:
        my_coin_toggle = None
        if not coin.id in my_coins:
            my_coin_toggle = rumps.MenuItem("Add to my coins")
        else:
            my_coin_toggle = rumps.MenuItem("Remove from my coins")

        my_coin_toggle.set_callback(coin.ToggleMyCoinsMembership)

        main_coin_select = None
        if coin.id == default_coin:
            coin.SetToMenuItem(None)  # this is just setting the sender to None
        else:
            main_coin_select = rumps.MenuItem("Set as main coin", callback=coin.SetToMenuItem)

        this_coin_submenu = [my_coin_toggle]
        if main_coin_select is not None:
            this_coin_submenu.insert(0, main_coin_select)

        this_coin_submenu = this_coin_submenu + coin.GetCoinDetailsAsMenuItems()

        # this_coin_submenu = []

        coin_menu_item = [rumps.MenuItem(coin.GetSymbolAndUsd(), icon=coin.GetIconFilePath(), callback=coin.SetToMenuItem), this_coin_submenu]

        if not coin.id in my_coins:
            all_coins_menu.insert(len(all_coins_menu), coin_menu_item)
        else:
            my_coins_menu.insert(len(my_coins_menu), coin_menu_item)

    if len(my_coins_menu) > 0:
        my_coins_menu.insert(0, rumps.MenuItem("My Coins"))
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
        data["coinCount"] = 25
        data["myCoins"] = []

        with open(settings_file, 'w') as outfile:
            json.dump(data, outfile)

    if os.path.isfile(settings_file):
        logging.info("Reading settings")
        with open(settings_file) as json_file:
            data = json.load(json_file)
            global default_coin
            global fiat_reference
            global coin_count
            global my_coins

            if "defaultCoin" in data:
                default_coin = data["defaultCoin"]

            if "fiatReference" in data:
                fiat_reference = data["fiatReference"]

            if "coinCount" in data:
                coin_count = int(data["coinCount"])

            if "myCoins" in data:
                my_coins = data["myCoins"]
    return

def SaveSettings():
    if (application_support is None):
        return

    logging.info("Saving settings")
    data = {}

    global default_coin
    global fiat_reference
    global coin_count
    global my_coins

    data["defaultCoin"] = default_coin
    data["fiatReference"] = fiat_reference
    data["coinCount"] = coin_count
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
    coin_update_event.set()

    pycoin = rumps.App("PyCoin", title="PyCoin")
    pycoin.run()
