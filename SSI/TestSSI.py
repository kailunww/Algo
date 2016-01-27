__author__ = 'User'

import csv
import math
from pprint import pprint
import numpy
from datetime import datetime
from scipy.stats.stats import pearsonr

def moving_average(interval, window_size):
    window= numpy.ones(int(window_size))/float(window_size)
    return numpy.convolve(interval, window, 'valid')

import matplotlib.pyplot as plt
csv_name = "output.csv"
data = {}
with open(csv_name, "rb") as fr:
    reader = csv.DictReader(fr)
    for row in reader:
        cu = row["Currencies"]
        if cu not in data:
            data[cu] = []
        row["Date"] = datetime.strptime(row["Date"], "%Y-%m-%d %H:%M")
        row["Price"] = float(row["Price"])
        ssi = float(row["SSI"])
        if ssi < 0:
            ssi = -1.0/ssi
        row["SSI_LN"] = math.log(ssi)
        data[cu].append(row)
for key in data:
    data[key] = sorted(data[key], key = lambda x: x["Date"])
    ssi = [d["SSI_LN"] for d in data[key]]
    price = [d["Price"] for d in data[key]]
    date = [d["Date"] for d in data[key]]
    print key
    print pearsonr(price,ssi)
    #mean = numpy.mean(price)
    #sd = numpy.std(price)
    #print mean
    for i in range(100, len(data[key])):
        moving_price = price[i-100:i]
        moving_mean = numpy.mean(moving_price)
        moving_sd = numpy.std(moving_price)
        if abs(data[key][i]["Price"] - moving_mean) > 10*moving_sd:
            print data[key][i], moving_mean, moving_sd
    f = plt.figure(1)
    f.suptitle(key)
    plt.subplot(211)
    plt.xlabel('date')
    plt.ylabel('ssi')
    plt.plot(date, ssi, 'r--')
    plt.subplot(212)
    plt.ylabel('price')
    plt.plot(date, price, 'bs')
    plt.show()

