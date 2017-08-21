"""Runs a menu in the macOS menu bar with the top 50 coins from coinmarketcap.com"""

import os
from urllib2 import urlopen, URLError, HTTPError
import time
import json
import copy
import logging
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

    def SetToMenuItem(self, sender):
        global default_coin
        default_coin = copy.copy(self.id)
        SaveSettings()

        if pycoin is not None:
            pycoin.icon = self.GetIconFile()
            pycoin.title = self.GetSymbolAndUsd()

    def GetIconUrl(self):
        return "https://files.coinmarketcap.com/static/img/coins/64x64/" + self.id + ".png"

    def GetIconFile(self):
        # Open the url
        url = self.GetIconUrl()
        target_file = logos_folder + "/" + os.path.basename(url)

        if not os.path.isfile(target_file):
            logging.info("Downloading icon for %s from %s", self.name, url)
            try:
                f = urlopen(url)
                # print "downloading " + url

                # Open our local file for writing
                with open(target_file, "wb") as local_file:
                    local_file.write(f.read())

            #handle errors
            except HTTPError, e:
                logging.error("HTTP Error: %s %s", e.code, url)
            except URLError, e:
                logging.error("URL Error: %s %s", e.reason, url)

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


# @rumps.clicked("Debugging")
def OpenDebugWindow():
    logging.info("should open debugging window")
    rumps.Window(title="Debugging")
    return

# current table goes here
coins = []
new_menu = []
def GetTopCoins():
    try:
        logging.info("Downloading coins from %s", GetCoinsUrl())
        output = urlopen(GetCoinsUrl()).read()
        jason = json.loads(output)

        del coins[:]
        del new_menu [:]

        quit_menu = rumps.MenuItem("Quit", callback=rumps.quit_application)
        new_menu.insert(len(new_menu), quit_menu)

        # debug_menu_window = rumps.MenuItem("Debugging", callback=OpenDebugWindow)
        # new_menu.insert(len(new_menu), debug_menu_window)


        for c in jason:
            curr = Currency.CurrencyFromTable(c)
            coins.insert(len(coins), curr)
            curr.GetIconFile()
            coinMenu = rumps.MenuItem(
                curr.GetSymbolAndUsd(), icon=curr.GetIconFile(), callback=curr.SetToMenuItem)
            new_menu.insert(len(new_menu), coinMenu)
            if curr.id == default_coin:
                curr.SetToMenuItem(None) # this is just setting the sender to None

        if pycoin is not None:
            pycoin.menu.clear()
            pycoin.menu.update(new_menu)

    except HTTPError, e:
        logging.error("HTTP error loading coins: %s %s", e.code, coins_url)
    except URLError, e:
        logging.error("Error loading url: %s %s", e.reason, coins_url)


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

    logging.info("Writing settings")
    with open(settings_file, 'w') as outfile:
        json.dump(data, outfile)

def Log(msg):
    return

def timez():
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())

@rumps.timer(300)
def GetCoinsTimerCallback(sender):
    # print('%r %r' % (sender, timez()))
    logging.info("Get Top Coins timer")
    GetTopCoins()

pycoin = None
application_support = None
logos_folder = "logos"

log_file = "pycoin.log"

if __name__ == "__main__":
    application_support = rumps.application_support("pycoin")
    logos_folder = application_support + "/" + logos_folder

    CreateDataFoldersIfNecessary()

    logging.basicConfig(filename=application_support + "/" + log_file,
                        level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    logging.info("---APP START---")

    settings_file = application_support + "/settings.json"
    LoadSettingsOrDefaults()

    pycoin = rumps.App("PyCoin", title="PyCoin")
    pycoin.run()
