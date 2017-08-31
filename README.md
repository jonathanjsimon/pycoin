# PyCoin
A macOS menu bar app that monitors cryptos on [coinmarketcap.com](https://coinmarketcap.com). Uses the [rumps](https://github.com/jaredks/rumps) Python library for macOS interaction.

## Current features
 - All coins in terms of BTC and USD
 - Updates every 5 minutes (as often as the [coinmarketcap.com API](https://coinmarketcap.com/api/) endpoints update). Upon a failure to update, another attempt will be made after 1 minute.
 - Set a single coin as the main coin to be shown in the menubar.
 - Set multiple coins to be monitored as My Coins. These coins will be monitored even if they are not in the set of coins retrieved from CoinMarketCap.
 - Set the number of coins monitored to 10, 25, 50, or 100.
 - Each coin shows details about that coin.
 - Each coin contains a deep link to that coin's page on CoinMarketCap

## Upcoming features
 - Be able to set which fiat currency to use as reference

## Shameless request for donations
If you'd like to send a donation, please send BTC to `34FLk4rA4MwhXpJhdUbY91HVn2CYY97BFq`. Not necessary but very much appreciated.

![](https://raw.githubusercontent.com/jonathanjsimon/pycoin/master/PyCoin.png)