# coding=UTF-8

__author__ = 'User'

import requests
import csv

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
with open(file_name, "rb") as f:
    reader = csv.DictReader(f)
    for r in reader:
        ratio = float(r["Adj Close"]) / float(r["Close"])
        adjusted = {
            "open":float(r["Open"]) * ratio,

        }
        print r
#get_stock("119")