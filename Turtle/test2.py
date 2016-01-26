from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma
from pyalgotrade import technical
from pyalgotrade.tools import yahoofinance
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.bar import Frequency
import csv
import os
from pyalgotrade.talibext.indicator import ATR, MIN, MAX
from enum import Enum
from collections import OrderedDict
from datetime import datetime
from pprint import pprint
from pyalgotrade.broker import Order
class Action(Enum):
    UNKNOWN = 0
    Buy = 1
    Sell = 2
import pyalgotrade.dataseries

class TurtleTrading(strategy.BacktestingStrategy):
    def __init__(self, feed, instruments, capital, indicators):
        strategy.BacktestingStrategy.__init__(self, feed, capital*100)
        self.init_capital = capital
        self.__instruments = instruments
        self.indicators = indicators
        self.open_positions = []

    def getDollarPerPoint(self, instrument):
        return self.__instruments[instrument]["dollar_per_point"]

    def onBars(self, bars):
        this_date = self.getCurrentDateTime().strftime("%Y-%m-%d")
        for instrument, bar in bars.items():
            try:
                indicator = self.indicators.get(instrument).get(this_date)
                high55 = indicator["High55"]
                low55 = indicator["Low55"]
                high20 = indicator["High20"]
                low20 = indicator["Low20"]
                atr20 = indicator["ATR20"]
                market_dollar_volatility = atr20 * self.getDollarPerPoint(instrument)
                market_dollar_volatility = atr20 * 1
                unit_size = int(self.init_capital * 0.01 / market_dollar_volatility)
                # If a position was not opened, check if we should enter a long position.
                if len(self.open_positions) == 0:
                    if bar.getClose() >= high55:
                        position = self.enterLong(instrument, int(unit_size), True)
                        self.info("Enter long for %.2f >= %.2f" % (bar.getClose(), high55))
                    elif bar.getClose() <= low55:
                        position = self.enterShort(instrument, int(unit_size), True)
                        self.info("Enter short for %.2f <= %.2f" % (bar.getClose(), low55))
                # Check if we have to exit the position.
                else:
                    last_order = self.open_positions[-1].getEntryOrder()
                    last_action = last_order.getAction()
                    last_price = last_order.getAvgFillPrice()
                    #self.info(last_action)
                    if last_action == Order.Action.BUY:
                        if bar.getClose() <= low20:
                            action = "Stop win"
                            self.info("Stop win for %.2f <= %.2f" % (bar.getClose(), low20))
                            for p in self.open_positions:
                                self.info("Try to exit position %s" % p)
                                p.exitMarket(False)
                        elif bar.getClose() <= last_price - 2 * atr20:
                            action = "Stop loss"
                            self.info("Stop loss for %.2f <= %.2f - 2 * %.2f" % (bar.getClose(), last_price, atr20))
                            for p in self.open_positions:
                                self.info("Try to exit position %s" % p)
                                p.exitMarket(False)
                        elif bar.getClose() >= last_price + 0.5 * atr20 and len(self.open_positions) < 4:
                            action = "Add long"
                            self.info("Add long for %.2f >= %.2f + 0.5 * %.2f" % (bar.getClose(), last_price, atr20))
                            position = self.enterLong(instrument, int(unit_size), True)
                    elif last_action == Order.Action.SELL_SHORT:
                        if bar.getClose() >= high20:
                            action = "Stop win"
                            self.info("Stop win for %.2f >= %.2f" % (bar.getClose(), high20))
                            for p in self.open_positions:
                                self.info("Try to exit position %s" % p)
                                p.exitMarket(False)
                        elif bar.getClose() >=last_price + 2 * atr20:
                            action = "Stop loss"
                            self.info("Stop loss for %.2f >= %.2f + 2 * %.2f" % (bar.getClose(), last_price, atr20))
                            for p in self.open_positions:
                                self.info("Try to exit position %s" % p)
                                p.exitMarket(False)
                        elif bar.getClose() <= last_price - 0.5 * atr20 and len(self.open_positions) < 4:
                            action = "Add short"
                            position = self.enterShort(instrument, int(unit_size), True)
                            self.info("Add short for %.2f <= %.2f - 0.5 * %.2f" % (bar.getClose(), last_price, atr20))
            except KeyError:
                continue
            except Exception as e:
                print e
                raw_input()
                continue

    def onEnterOk(self, position):
        self.open_positions.append(position)
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info(execInfo)

    def onEnterCanceled(self, position):
        self.info("Enter failed")

    def onExitOk(self, position):
        self.open_positions.remove(position)
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info(execInfo)

    def onExitCanceled(self, position):
        self.info("Exit failed")
        position.cancelExit()

def test():
    # Load the yahoo feed from the CSV file
    instruments = {
        'XAUUSD': {"name":"XAUUSD", "dollar_per_point":100},
    }
    CAPITAL = 2000000
    feed = GenericBarFeed(5 * Frequency.MINUTE)
    indicators = {}
    for i in instruments:
        print i
        csv_name = '%s.csv' % (i)
        #convertTicketStoryCsv(csv_name)
        csv_name_new = "new_" + csv_name
        csv_name = os.path.join("data", csv_name)
        csv_name_new = os.path.join("new", csv_name_new)
        print csv_name_new
        feed.addBarsFromCSV(i, csv_name_new)
        indicators[i] = createIndicatorFromCsv(csv_name_new)
    #pprint(indicators)
    myStrategy = TurtleTrading(feed, instruments, CAPITAL, indicators)
    myStrategy.run()
    final = myStrategy.getBroker().getEquity() - CAPITAL * 99
    profit = final - CAPITAL
    print "Final portfolio value: $%.2f" % final
    print "Profit = %.2f, %.2f " % (profit, 100 * profit / CAPITAL)

def createIndicatorFromCsv(csv_name):
    f = open(csv_name, "rb")
    r = csv.DictReader(f)
    indicatorDict = {}
    indicatorList = []
    for d in r:
        key = d["Date Time"].split()[0]
        if key not in indicatorDict:
            data = {
                "Date":key,
                "Open": float(d["Open"]),
                "High": float(d["High"]),
                "Low": float(d["Low"]),
                "Close": float(d["Close"]),
                "TR":""
            }
            indicatorDict[key] = data
            indicatorList.append(data)
        else:
            data = indicatorDict[key]
            data["High"] = max(data["High"], float(d["High"]))
            data["Low"] = min(data["Low"], float(d["Low"]))
            data["Close"] = float(d["Close"])
    for i in range(0, len(indicatorList)):
        if i > 20:
            indicatorList[i]["High20"] = max([d["High"] for d in indicatorList[i-20:i]])
            indicatorList[i]["Low20"] = min([d["Low"] for d in indicatorList[i-20:i]])
        if i > 55:
            indicatorList[i]["High55"] = max([d["High"] for d in indicatorList[i-55:i]])
            indicatorList[i]["Low55"] = min([d["Low"] for d in indicatorList[i-55:i]])
        if i > 0:
            lastday = indicatorList[i-1]
            tr = max([indicatorList[i]["High"] - indicatorList[i]["Low"], indicatorList[i]["High"] - lastday["Close"], lastday["Close"] - indicatorList[i]["Low"]])
            indicatorList[i]["TR"] = tr
            if i > 20:
                if not lastday.has_key("ATR20"):
                    indicatorList[i]["ATR20"] = sum(d["TR"] for d in indicatorList[i-20:i]) / 20
                else:
                    indicatorList[i]["ATR20"] = (19*lastday["ATR20"] + tr)/20
    return indicatorDict

def convertTicketStoryCsv(csv_name):
    csv_name_new = "new_" + csv_name
    csv_name = os.path.join("data", csv_name)
    csv_name_new = os.path.join("new", csv_name_new)
    with open(csv_name, "rb") as fr:
        reader = csv.DictReader(fr)
        with open(csv_name_new, "wb")as fw:
            w = csv.DictWriter(fw, ["Date Time", "Open", "High", "Low", "Close", "Volume", "Adj Close"])
            w.writeheader()
            for row in reader:
                new = {}
                d = row["Date"]
                new["Date Time"] = d[:4] + "-" + d[4:6] + "-" + d[6:] + " " + row["Timestamp"]
                new["Open"] = row["Open"]
                new["High"] = row["High"]
                new["Low"] = row["Low"]
                new["Close"] = row["Close"]
                new["Volume"] = 100000
                w.writerow(new)

test()