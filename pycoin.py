"""Runs a menu in the macOS menu bar with the top 50 coins from coinmarketcap.com"""

import os
from urllib2 import urlopen, URLError, HTTPError
import time
import json
import rumps
import pathlib2 as pathlib
import objc
# from concurrent.futures import ThreadPoolExecutor, as_completed

coins_url = 'https://api.coinmarketcap.com/v1/ticker/?convert=USD&limit=50'

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
            rVal = self.priceUsd

        if self.symbol is not None:
            rVal = "(" + self.symbol + ") " + rVal

        return rVal

    def SetToMenuItem(self, sender):
        if theApp is not None:
            theApp.icon = self.GetIconFile()
            theApp.title = self.GetSymbolAndUsd()

    def GetIconUrl(self):
        return "https://files.coinmarketcap.com/static/img/coins/64x64/" + self.id + ".png"

    def GetIconFile(self):
        # Open the url
        url = self.GetIconUrl()
        target_file = theApplicationSupport + "/" + os.path.basename(url)

        if pathlib.Path(target_file).is_file() is False:
            try:
                f = urlopen(url)
                # print "downloading " + url

                # Open our local file for writing
                with open(target_file, "wb") as local_file:
                    local_file.write(f.read())

            #handle errors
            except HTTPError, e:
                print "HTTP Error:", e.code, url
            except URLError, e:
                print "URL Error:", e.reason, url

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

# current table goes here

menuItemCoin = "ethereum"
coins = []
newMenu = []
def GetTopCoins():
    try:
        output = urlopen(coins_url).read()

        jason = json.loads(output)

        del coins[:]
        del newMenu [:]

        quitMenu = rumps.MenuItem("Quit", callback=rumps.quit_application)
        newMenu.insert(len(newMenu), quitMenu)

        deafult_coin_name = ""
        default_coin_price = ""
        for c in jason:
            curr = Currency.CurrencyFromTable(c)
            coins.insert(len(coins), curr)
            curr.GetIconFile()
            coinMenu = rumps.MenuItem(
                curr.GetSymbolAndUsd(), icon=curr.GetIconFile(), callback=curr.SetToMenuItem)
            newMenu.insert(len(newMenu), coinMenu)
            if curr.id == menuItemCoin:
                curr.SetToMenuItem(None) # this is just setting the sender to None
                defaultCoinName = curr.name
                defaultCoinPrice = curr.priceUsd

        if theApp is not None:
            NSDictionary = objc.lookUpClass("NSDictionary")
            theApp.menu.clear()
            theApp.menu.update(newMenu)
            rumps.notification("PyCoin Update", deafult_coin_name,
                            default_coin_price, sound=False, data=NSDictionary())
    except HTTPError, e:
        print "HTTP error loading coins:", e.code, coins_url
    except URLError, e:
        print "Error loading url:", e.reason, coins_url

def timez():
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())

@rumps.timer(300)
def GetCoinsTimerCallback(sender):
    # print('%r %r' % (sender, timez()))
    GetTopCoins()

theApp = None
theApplicationSupport = None
if __name__ == "__main__":
    theApplicationSupport = rumps.application_support("pycoin")
    # GetTopCoins()

    theApp = rumps.App("PyCoin", title="PyCoin")

    theApp.run()
