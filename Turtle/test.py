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
class Action(Enum):
    UNKNOWN = 0
    Buy = 1
    Sell = 2
import pyalgotrade.dataseries

class TurtleTrading(strategy.BacktestingStrategy):
    def __init__(self, feed, instruments, capital):
        strategy.BacktestingStrategy.__init__(self, feed, capital)
        self.__instruments = instruments
        self.action = Action.UNKNOWN
        self.last_price = None
        self.positions = []
        self.positions_all = []
        self.record = {}

    def getDollarPerPoint(self, instrument):
        return self.__instruments[instrument]["dollar_per_point"]

    def onBars(self, bars):
        for instrument, bar in bars.items():
            action = ""
            keys = []
            position = None
            barDs = self.getFeed().getDataSeries(instrument)
            highDS = barDs.getHighDataSeries()
            lowDS = barDs.getLowDataSeries()
            high55 = MAX(highDS, 100, 55)
            low55 = MIN(lowDS, 100, 55)
            high20 = MAX(highDS, 100, 20)
            low20 = MIN(lowDS, 100, 20)
            atr20 = ATR(barDs, 100, 20)
            if len(high55) < 2 or len(low55) < 2 or len(high20) < 2 or len(low20) < 2 or len(atr20) < 2:
                continue
            high55 = high55[-1]
            low55 = low55[-1]
            high20 = high20[-1]
            low20 = low20[-1]
            atr20 = atr20[-1]

            # Wait for enough bars to be available to calculate a SMA.
            if str(high55) == "nan" or str(low55) == "nan":
                continue

            #self.info("%s %.2f %.2f %.2f %.2f %.2f %.2f" % (instrument, bar.getAdjClose(), atr20, low20, high20, low55, high55))

            market_dollar_volatility = atr20 * self.getDollarPerPoint(instrument)
            equity = self.getBroker().getEquity()
            unit_size = int(equity * 0.01 / market_dollar_volatility)
            #self.info("%s %.2f %.2f" % (instrument, market_dollar_volatility, unit_size))

            # If a position was not opened, check if we should enter a long position.
            if len(self.positions) == 0:
                # print bar.getPrice(), high55, low55
                if bar.getHigh() >= high55:
                    # Enter a buy market order for 10 shares. The order is good till canceled.
                    action = "Enter long"
                    position = self.enterLong(instrument, int(unit_size), True)
                    self.action = Action.Buy
                    keys.append("enter_" + str(position))
                elif bar.getLow() <= low55:
                    # Enter a buy market order for 10 shares. The order is good till canceled.
                    action = "Enter short"
                    position = self.enterShort(instrument, int(unit_size), True)
                    self.action = Action.Sell
                    keys.append("enter_" + str(position))
            # Check if we have to exit the position.
            else:
                if self.action == Action.Buy:
                    if bar.getLow() <= low20:
                        action = "Stop win"
                        for p in self.positions:
                            self.info("Try to exit position %s" % p)
                            keys.append("exit_" + str(p))
                            p.exitMarket(False)
                    elif bar.getLow() <= self.last_price - 2 * atr20:
                        action = "Stop loss"
                        for p in self.positions:
                            self.info("Try to exit position %s" % p)
                            keys.append("exit_" + str(p))
                            p.exitMarket(False)
                    elif bar.getHigh() >= self.last_price + 0.5 * atr20 and len(self.positions) < 4:
                        action = "Add long"
                        position = self.enterLong(instrument, int(unit_size), True)
                        keys.append("enter_" + str(position))
                if self.action == Action.Sell:
                    if bar.getHigh() >= high20:
                        action = "Stop win"
                        for p in self.positions:
                            self.info("Try to exit position %s" % p)
                            keys.append("exit_" + str(p))
                            p.exitMarket(False)
                    elif bar.getHigh() >= self.last_price + 2 * atr20:
                        action = "Stop loss"
                        for p in self.positions:
                            self.info("Try to exit position %s" % p)
                            keys.append("exit_" + str(p))
                            p.exitMarket(False)
                    elif bar.getLow() <= self.last_price - 0.5 * atr20 and len(self.positions) < 4:
                        action = "Add short"
                        position = self.enterShort(instrument, int(unit_size), True)
                        keys.append("enter_" + str(position))
            for key in keys:
                r = OrderedDict()
                r["date"] = bar.getDateTime()
                r["high55"] = high55
                r["low55"] = low55
                r["high20"] = high20
                r["low20"] = low20
                r["atr20"] = atr20
                r["open"] = bar.getOpen()
                r["high"] = bar.getHigh()
                r["low"] = bar.getLow()
                r["close"] = bar.getClose()
                r["action"] = action
                self.record[key] = r
                self.info(key)

    def onEnterOk(self, position):
        self.positions.append(position)
        self.positions_all.append(position)
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("Enter position, total = %s" % len(self.positions))
        self.info(execInfo)
        self.last_price = execInfo.getPrice()
        key = "enter_" + str(position)
        self.record[key]["exe_price"] = execInfo.getPrice()
        self.record[key]["quantity"] = execInfo.getQuantity()

    def onEnterCanceled(self, position):
        self.info("Enter failed")

    def onExitOk(self, position):
        self.positions.remove(position)
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("Exit position, total = %s" % len(self.positions))
        self.info(execInfo)
        key = "exit_" + str(position)
        self.record[key]["exe_price"] = execInfo.getPrice()
        self.record[key]["quantity"] = execInfo.getQuantity()

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.info("Exit failed")
        position.cancelExit()
        #position.exitMarket(False)


def run_strategy():
    # Load the yahoo feed from the CSV file
    from pyalgotrade.tools import yahoofinance
    import csv
    instruments = {
        #'orcl'
        #,'aapl'
        '^HSI': {"name":"MHSI", "dollar_per_point":10},
        #'fxcm',
    }
    YEARS = [2010,2015]
    CAPITAL = 20000000
    feed = yahoofeed.Feed()
    for i in instruments:
        for y in range(YEARS[0], YEARS[1]+1):
            # print i, y
            csv_name = '%s-%s.csv' % (i,y)
            csv_name_new = "new_" + csv_name
            yahoofinance.download_daily_bars(i, y, csv_name)
            with open(csv_name, "rb") as fr:
                reader = csv.DictReader(fr)
                with open(csv_name_new, "wb")as fw:
                    w = csv.DictWriter(fw, reader.fieldnames)
                    w.writeheader()
                    for row in reader:
                        factor = float(row["Adj Close"]) / float(row["Close"])
                        row["Open"] = float(row["Open"]) * factor
                        row["High"] = float(row["High"]) * factor
                        row["Low"] = float(row["Low"]) * factor
                        row["Close"] = float(row["Close"]) * factor
                        row["Volume"] = float(row["Volume"]) * factor
                        w.writerow(row)
            feed.addBarsFromCSV(i, csv_name_new)

    # Evaluate the strategy with the feed.
    myStrategy = TurtleTrading(feed, instruments, CAPITAL)
    myStrategy.run()
    final = myStrategy.getBroker().getEquity()
    profit = final - CAPITAL
    print "Final portfolio value: $%.2f" % final
    print "Profit = %.2f, %.2f " % (profit, 100 * profit / CAPITAL)
    f = open("record.csv", "wb")
    rows = myStrategy.record.values()
    sorted(rows, key = lambda x: x["date"])
    for r in rows:
        print r["date"]
    w = csv.DictWriter(f, rows[0].keys())
    w.writeheader()
    w.writerows(rows)

def run():
    # Load the yahoo feed from the CSV file
    instruments = {
        #'orcl'
        #,'aapl'
        'XAGUSD': {"name":"XAGUSD", "dollar_per_point":1},
        #'fxcm',
    }
    CAPITAL = 20000000
    feed = GenericBarFeed(5 * Frequency.MINUTE)
    datas = {}
    for i in instruments:
        datas[i] = []
        csv_name = '%s.csv' % (i)
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
                    new["Volume"] = row["Volume"]
                    #w.writerow(new)
                    new["datetime"] = datetime.strptime(new["Date Time"], "%Y-%m-%d %H:%M:%S")
                    datas[i].append(new)
        feed.addBarsFromCSV(i, csv_name_new)
    # print datas
    indicator = OrderedDict()
    datelist = []
    for i in datas:
        for d in datas[i]:
            key = d["datetime"].strftime("%Y-%m-%d")
            if key not in indicator:
                indicator[key] = {
                    "Date":key,
                    "Open": float(d["Open"]),
                    "High": float(d["High"]),
                    "Low": float(d["Low"]),
                    "Close": float(d["Close"]),
                    "High55":"",
                    "Low55":"",
                    "High20":"",
                    "Low20":"",
                    "ATR20":"",
                    "TR":""
                }
                datelist.append(indicator[key])
            else:
                indicator[key]["High"] = max(indicator[key]["High"], float(d["High"]))
                indicator[key]["Low"] = min(indicator[key]["Low"], float(d["Low"]))
                indicator[key]["Close"] = float(d["Close"])
    for i in range(0, len(datelist)):
        if i > 20:
            datelist[i]["High20"] = max([d["High"] for d in datelist[i-20:i]])
            datelist[i]["Low20"] = min([d["Low"] for d in datelist[i-20:i]])
        if i > 55:
            datelist[i]["High55"] = max([d["High"] for d in datelist[i-55:i]])
            datelist[i]["Low55"] = min([d["Low"] for d in datelist[i-55:i]])
        if i > 1:
            lastday = datelist[i-1]
        #lastlastday = datelist[i-2]
            tr = max([datelist[i]["High"] - datelist[i]["Low"], datelist[i]["High"] - lastday["Close"], lastday["Close"] - datelist[i]["Low"]])
        datelist[i]["TR"] = tr
        if i > 20:
            if lastday["ATR20"] == "":
                datelist[i]["ATR20"] = sum(d["TR"] for d in datelist[i-20:i]) / 20
            else:
                datelist[i]["ATR20"] = (19*lastday["ATR20"] + tr)/20

    from pprint import pprint
    for d in indicator.values():
        pprint( d)

    # Evaluate the strategy with the feed.
    #myStrategy = TurtleTrading(feed, instruments, CAPITAL)
    #myStrategy.run()
    # final = myStrategy.getBroker().getEquity()
    # profit = final - CAPITAL
    # print "Final portfolio value: $%.2f" % final
    # print "Profit = %.2f, %.2f " % (profit, 100 * profit / CAPITAL)
    # f = open("record.csv", "wb")
    # rows = myStrategy.record.values()
    # sorted(rows, key = lambda x: x["date"])
    # for r in rows:
    #     print r["date"]
    # w = csv.DictWriter(f, rows[0].keys())
    # w.writeheader()
    # w.writerows(rows)

run()