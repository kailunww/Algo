__author__ = 'User'

import csv
import math
from pprint import pprint
from datetime import datetime
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
pprint (data)

