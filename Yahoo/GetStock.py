# coding=UTF-8

__author__ = 'User'

import requests
import csv
from datetime import datetime
import matplotlib.pyplot as plt

def get_stock(code):
    code = code.zfill(4)
    web = requests.Session()
    params = {
        "s":code+".HK",
        "a":1,
        "b":1,
        "c":2000,
        "d":1,
        "e":1,
        "f":2016,
        "ignore":".csv"
    }
    url = "http://real-chart.finance.yahoo.com/table.csv"
    r = web.get(url, params=params)
    #print r.text
    file_name = code + ".csv"
    with open(file_name, "wb") as f:
        f.write(r.text)
with open("Futures.csv", "rb") as f:
    reader = csv.reader(f)
    codes = [r[0] for r in reader]
#for code in codes:
#    get_stock(code)
#for code in codes:
code = "119"
code = code.zfill(4)
file_name = code + ".csv"
data_feed = []
with open(file_name, "rb") as f:
    reader = csv.DictReader(f)
    for r in reader:
        ratio = float(r["Adj Close"]) / float(r["Close"])
        adjusted = {
            "open":float(r["Open"]) * ratio,
            "close":float(r["Close"]) * ratio,
            "high":float(r["High"]) * ratio,
            "low":float(r["Low"]) * ratio,
            "date":datetime.strptime(r["Date"], "%Y-%m-%d"),
            "volume":99999999
        }
        data_feed.append(adjusted)
print data_feed
#get_stock("119")
f = plt.figure(1)
plt.subplot(211)
plt.xlabel('date')
plt.ylabel('ssi')
high = [d["high"] for d in data_feed]
low = [d["low"] for d in data_feed]
close = [d["close"] for d in data_feed]
open = [d["open"] for d in data_feed]
date = [d["date"] for d in data_feed]
for i in range(0, len(data_feed)):
    start = max(i-20, 0)
    window = data_feed[start:i]
    data_feed["high20"] = max([d[""]])
plt.plot(date, high, 'r--',date, low, 'g--',date, open, 'b--',date, close, 'y--')
# plt.subplot(212)
# plt.ylabel('price')
# plt.plot(date, price, 'bs')
plt.show()