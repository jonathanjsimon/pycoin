"""Runs a menu in the macOS menu bar with the top x (selected in preferences) coins from coinmarketcap.com"""

import os
import time
import json
import copy
import logging
import logging.handlers
import threading
import sys
import webbrowser

import rumps
import requests
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileSystemEventHandler

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
        target_logo = logos_folder + "/" + self.id + ".png"
        if os.path.isfile(target_logo):
            return target_logo

        return None

    def DownloadCoinIcon(self):
        coin_logo_url = self.GetIconUrl()
        target_file = logos_folder + "/" + os.path.basename(coin_logo_url)

        with self.logoDownloadSemaphore:
            if not os.path.isfile(target_file):
                logger.info("Downloading icon for %s from %s", self.id, coin_logo_url)
                try:
                    r = s.get(coin_logo_url, timeout=(2, 3))

                    if r.status_code == requests.codes.ok:
                        with open(target_file, "wb") as local_file:
                            for chunk in r.iter_content(chunk_size=128):
                                local_file.write(chunk)

                except requests.ConnectionError, e:
                    logger.error("Error connecting to url", exc_info=True)
                except requests.ConnectTimeout, e:
                    logger.error("Connection to url timed out", exc_info=True)
                except requests.ReadTimeout, e:
                    logger.error("Reading from url timed out", exc_info=True)
                except:
                    logger.error("Error processing response", exc_info=True)

    def GetCoinDetailsAsMenuItems(self):
        details = []

        if not self.name is None:
            details.append(rumps.MenuItem("Name: " + self.name))
        if not self.rank is None:
            details.append(rumps.MenuItem("Rank: " + self.rank))
        if not self.priceBtc is None:
            details.append(rumps.MenuItem(u"BTC: \u20BF" + self.priceBtc))
        if not self._24hVolumeUsd is None:
            details.append(rumps.MenuItem("24hr Volume: " + self._24hVolumeUsd))
        if not self.marketCapUsd is None:
            details.append(rumps.MenuItem("Market Cap USD: $" + self.marketCapUsd))
        if not self.availableSupply is None:
            details.append(rumps.MenuItem("Available: " + self.availableSupply))
        if not self.totalSupply is None:
            details.append(rumps.MenuItem("Total: " + self.totalSupply))
        if not self.percentChange1h is None:
            details.append(rumps.MenuItem(u"1h \u0394: " + self.percentChange1h + "%"))
        if not self.percentChange24h is None:
            details.append(rumps.MenuItem(u"24h \u0394: " + self.percentChange24h + "%"))
        if not self.percentChange7d is None:
            details.append(rumps.MenuItem(u"7d \u0394: " + self.percentChange7d + "%"))

        return details

    def OpenCoinPage(self, sender):
        webbrowser.open("https://coinmarketcap.com/currencies/" + self.id + "/")
        return

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

def UpdateCoinsNow(sender):
    global coin_update_event
    coin_update_event.set()

def Quit(sender):
    global should_run_coin_loop
    global coin_update_event
    global coin_update_thread

    should_run_coin_loop = False
    coin_update_event.set()
    coin_update_thread.join()
    rumps.quit_application()

debug_window = None
def OpenDebugWindow(sender):
    global debug_window
    logger.info("should open debugging window")
    debug_window = rumps.Window(message="Foo", title="Debugging", default_text='Bar', dimensions=(320, 160))
    debug_window.run()
    return

possible_fiat_reference = ["AUD", "BRL", "CAD", "CHF", "CNY", "EUR", "GBP", "HKD", "IDR", "INR", "JPY", "KRW", "MXN", "RUB", "USD"]
possible_coin_counts = [10, 25, 50, 100]

default_coin = "bitcoin"
fiat_reference = "USD"
coin_count = 50

def SetCoinCount(sender):
    global coin_count
    global coin_update_event

    logger.info("Setting coin count to %s", str(sender.title))
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
        r = s.get(url, timeout=(2, 3))

        if r.status_code == requests.codes.ok:
            rVal = r.json()
    except requests.ConnectionError, e:
        logger.error("Error connecting to url", exc_info=True)
    except requests.ConnectTimeout, e:
        logger.error("Connection to url timed out", exc_info=True)
    except requests.ReadTimeout, e:
        logger.error("Reading from url timed out", exc_info=True)
    except:
        logger.error("Error processing response", exc_info=True)

    return rVal

def AddMissingCoinToCoins(coinId):
    global coins

    logger.info("%s missing from main list, must retrieve", coinId)
    coin_json = GetJsonResponseForUrl(GetSpecificCoinUrl(coinId))
    if not coin_json is None and not "error" in coin_json:
        logger.debug("Retrieved %s", coinId)
        true_coin = coin_json[0]
        if not true_coin is None:
            curr = Currency.CurrencyFromTable(true_coin)
            curr.DownloadCoinIcon()
            coins.append(curr)

coin_update_thread = None
def StartCoinUpdateThread():
    global coin_update_thread
    if (coin_update_thread is None or coin_update_thread.IsAlive() is False):
        coin_update_thread = threading.Thread(target=GetTopCoinsLooper, name="CoinUpdater")
        coin_update_thread.start()

coin_update_timeout = 300
coin_update_event = threading.Event()
should_run_coin_loop = True
def GetTopCoinsLooper():
    global coin_update_timeout
    global coin_update_event
    global should_run_coin_loop

    while coin_update_event.wait(timeout=coin_update_timeout) or True:
        if (should_run_coin_loop):
            coin_update_event.clear()
            did_get_coins = False

            try:
                did_get_coins = GetTopCoins()
            except:
                logger.error("Error in coins loop", exc_info=True)

            if not did_get_coins:
                coin_update_timeout = 60
                logger.warn("Will retry getting coins in 60 seconds...")
            else:
                coin_update_timeout = 300
        else:
            break

# current table goes here
my_coins = []
coins = []
last_updated_time = ""
def GetTopCoins():
    global coins
    global last_updated_time

    logger.info("Downloading coins from %s", GetCoinsUrl())
    coins_json = GetJsonResponseForUrl(GetCoinsUrl())

    if not coins_json is None:
        del coins[:]

        for c in coins_json:
            coin = Currency.CurrencyFromTable(c)
            coins.append(coin)
            try:
                coin.DownloadCoinIcon()
            except:
                logger.warn("Failed to download icon for %s", coin.id)

        last_updated_time = TimeStringForNow()
        ProcessCoinsToMenu()
        return True

    return False


def ProcessCoinsToMenu():
    global my_coins
    global coins
    global coin_count
    global possible_fiat_reference

    new_menu = []
    app_menu = []
    my_coins_menu = []
    all_coins_menu = []

    last_updated = rumps.MenuItem("Updated: " + last_updated_time)
    app_menu.append(last_updated)

    coin_count_options = []
    for count in possible_coin_counts:
        count_selected = 0
        if count == coin_count:
            count_selected = 1

        new_coin_count_option = rumps.MenuItem(count, callback=SetCoinCount)
        new_coin_count_option.state = count_selected

        coin_count_options.append(new_coin_count_option)

    coin_count_menu = [rumps.MenuItem("Coin Count"), coin_count_options]
    app_menu.append(coin_count_menu)

    force_refresh = rumps.MenuItem("Refresh", callback=UpdateCoinsNow)
    app_menu.append(force_refresh)

    # debug_menu_window = rumps.MenuItem("Debugging", callback=OpenDebugWindow)
    # app_menu.append(debug_menu_window)

    quit_menu = rumps.MenuItem("Quit", callback=Quit)
    app_menu.append(quit_menu)

    app_menu.append(None)

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
            main_coin_details = coin.GetCoinDetailsAsMenuItems()
            app_menu[1:1] = main_coin_details
        else:
            main_coin_select = rumps.MenuItem("Set as main coin", callback=coin.SetToMenuItem)

        this_coin_submenu = [my_coin_toggle]
        this_coin_submenu.append(rumps.MenuItem("View on coinmarketcap.com", callback=coin.OpenCoinPage))
        if main_coin_select is not None:
            this_coin_submenu.insert(0, main_coin_select)

        this_coin_submenu = this_coin_submenu + coin.GetCoinDetailsAsMenuItems()

        coin_menu_item = [rumps.MenuItem(coin.GetSymbolAndUsd(), icon=coin.GetIconFilePath(), callback=coin.SetToMenuItem), this_coin_submenu]

        if not coin.id in my_coins:
            all_coins_menu.append(coin_menu_item)
        else:
            my_coins_menu.append(coin_menu_item)

    if len(my_coins_menu) > 0:
        my_coins_menu.insert(0, rumps.MenuItem("My Coins"))
        my_coins_menu.append(None)

    if pycoin is not None:
        pycoin.menu.clear()
        pycoin.menu.update(app_menu + my_coins_menu + all_coins_menu)

def CreateDataFoldersIfNecessary():
    try:
        if not os.path.isdir(application_support):
            os.makedirs(application_support)

        if not os.path.isdir(logos_folder):
            os.makedirs(logos_folder)
    except:
        # This is bad since we can't even log it
        pass

settings_file = ""
def LoadSettingsOrDefaults():
    if (application_support is None):
        # this is bad since we can't log to a file in a folder that doesn't exist
        return

    try:
        if not os.path.isfile(settings_file):
            logger.info("Initializing default settings")
            data = {}
            data['defaultCoin'] = "bitcoin"
            data["fiatReference"] = "USD"
            data["coinCount"] = 25
            data["myCoins"] = []

            with open(settings_file, 'w') as outfile:
                json.dump(data, outfile)

        if os.path.isfile(settings_file):
            logger.info("Reading settings")
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
    except:
        logger.error("Error loading settings", exc_info=True)

def SaveSettings():
    if (application_support is None):
        return

    logger.info("Saving settings")
    data = {}

    global default_coin
    global fiat_reference
    global coin_count
    global my_coins

    data["defaultCoin"] = default_coin
    data["fiatReference"] = fiat_reference
    data["coinCount"] = coin_count
    data["myCoins"] = my_coins

    try:
        with open(settings_file, 'w') as outfile:
            json.dump(data, outfile, indent=4)
    except:
        logger.error("Error saving settings", exc_info=True)

observer = None
def StartSettingsMonitor():
    global observer
    global application_support
    global settings_file

    logger.info(application_support)
    logger.info(settings_file)

    # event_handler = PatternMatchingEventHandler(patterns=settings_file, ignore_directories=True, case_sensitive=True)
    # event_handler.on_any_event = SettingsMonitorEventHandler

    event_handler = FileSystemEventHandler()
    event_handler.on_any_event = SettingsMonitorEventHandler

    observer = Observer()
    observer.schedule(event_handler, application_support, recursive=False)
    observer.start()

def SettingsMonitorEventHandler(event):
    logger.info("Settings Change detected")
    return

def TimeStringForNow():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

pycoin = None
application_support = None
logos_folder = "logos"
log_file = "pycoin.log"
logger = None

is_py2app = hasattr(sys, "frozen")
pem_path = "lib/python2.7/certifi/cacert.pem" if is_py2app else None

s = requests.Session()
s.verify = pem_path

if __name__ == "__main__":
    application_support = rumps.application_support("pycoin")
    logos_folder = application_support + "/" + logos_folder

    CreateDataFoldersIfNecessary()

    logger = logging.getLogger("PyCoin")
    logger.setLevel(logging.DEBUG)

    handler = logging.handlers.RotatingFileHandler(application_support + "/" + log_file, maxBytes=102400, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(threadName)-10s] %(message)s'))

    logger.addHandler(handler)

    httpLogger = logging.getLogger("urllib3")
    httpLogger.setLevel(logging.WARNING)
    httpLogger.addHandler(handler)

    logger.info("---APP START---")

    settings_file = application_support + "/settings.json"
    LoadSettingsOrDefaults()

    StartCoinUpdateThread()
    coin_update_event.set()

    # try:
    #     StartSettingsMonitor()
    # except:
    #     logger.error("Error configuring settings monitor", exc_info=True)

    pycoin = rumps.App("PyCoin", title="PyCoin")
    pycoin.run()
