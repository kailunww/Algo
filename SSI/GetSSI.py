# coding=UTF-8

__author__ = 'User'

import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
from datetime import datetime
import sys
from pprint import pprint
import csv
def clean(txt):
    return "".join(txt.split())

web = requests.session()
r = web.get("http://www.dailyfx.com.hk/login.php")
r = web.get("https://plus.dailyfx.com/login/loginFormIB.jsp?ib=hongkong")

data = {
    "j_username":	"ukfxcm",
    "j_password":	"test",
    "submit.x":	50,
    "submit.y":	9
}
r = web.post("https://plus.dailyfx.com/login/j_security_check", data=data)
r = web.get("http://www.dailyfx.com.hk/tnews.php?lang=en")
r = web.get("https://plus.dailyfx.com/dailyfxsignals/fxsignals.do?ib=hongkong&lang=zh_HK")
headers = {
    "Referer": "http://www.dailyfx.com.hk/tnews.php?lang=en",
    "Accept-Language": "zh-HK,en-US;q=0.7,en;q=0.3"
}
cookies = {
    "udlang":   "big-5"
}
r = web.get("http://www.dailyfx.com.hk/dailyfx.plus/plus.ssi/index.php", headers=headers, cookies=cookies)
urls = OrderedDict()
r = web.get("http://www.dailyfx.com.hk/dailyfx.plus/plus.ssi/index.php?list=1", headers=headers, cookies=cookies)
r.encoding = "utf-8"
soup = BeautifulSoup(r.text, "html.parser")
table = soup.find("table")
for tr in table.find_all("tr"):
    td = tr.find("td")
    if td:
        a = td.find("a")
        url = a["href"]
        date_str = a.text
        date_str =  date_str.replace(u"年", "-")
        date_str =  date_str.replace(u"月", "-")
        date_str =  date_str.replace(u"日", "")
        date_ = datetime.strptime(date_str, "%Y-%m-%d")
        uid = url.split("=")[1]
        urls[uid] = {
            "url" : "http://www.dailyfx.com.hk/dailyfx.plus/plus.ssi/" + url
            , "date" : date_
        }
for i in range(2,71):
    r = web.get("http://www.dailyfx.com.hk/dailyfx.plus/plus.ssi/index.php?list=1&pagenum=%s" % i, headers=headers, cookies=cookies)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    for tr in table.find_all("tr"):
        td = tr.find("td")
        if td:
            a = td.find("a")
            url = a["href"]
            date_str = a.text
            date_str =  date_str.replace(u"年", "-")
            date_str =  date_str.replace(u"月", "-")
            date_str =  date_str.replace(u"日", "")
            date_ = datetime.strptime(date_str, "%Y-%m-%d")
            uid = url.split("=")[1]
            urls[uid] = {
                "url" : "http://www.dailyfx.com.hk/dailyfx.plus/plus.ssi/" + url
                , "date" : date_
            }
currencies_trans = {
    u"货币对" : -1,
    u"欧元/美元" : "EUR/USD",
    u"英镑/美元" : "GBP/USD",
    u"英镑/日元" : "GBP/JPY",
    u"英镑/日" : "GBP/JPY",
    u"美元/日元" : "USD/JPY",
    u"美元/瑞郎" : "USD/CHF",
    u"美元/加元" : "USD/CAD",
    u"澳元/美元" : "AUD/USD",
    u"纽元/美元" : "NZD/USD",
    u"黄金/美元" : "XAU/USD",
    u"SPX500" : "SPX500",
    u"SP500" : "SPX500",
    u"欧元/瑞郎" : "EUR/CHF",
    u"欧元/日元" : "EUR/JPY",
    u"美元/人民币" : "USD/CNH",
    u"美元/离岸人民币" : "USD/CNH"
}
for key, u in urls.items():
    #if int(key) > 49278:
    #    continue
    #u = urls["49292"]
    print u["url"]
    r = web.get(u["url"], headers=headers, cookies=cookies)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    try:
        if u"北京时间" in soup.text:
            txt = soup.text.split(u"北京时间")[1]
            time_str = txt.split(")")[0].split(u"）")[0]
            if u"日" in time_str:
                time_str = time_str.split(u"日")[1]
            time_str = time_str.replace(u"：", ":")
            time_str = time_str.replace("::", ":")
            time_str = time_str.replace(u"　", "")
            time_str = time_str.replace(" ", "")
            time_str = time_str.strip()
            if not time_str[0].isnumeric():
                time_str = time_str[1:]
        else:
            time_str = "0:00"
    except Exception as e:
        time_str = "0:00"
    datetime_ = u["date"].strftime("%Y-%m-%d") + " " + time_str
    table = soup.find("tbody")
    trs = table.find_all("tr")
    u["data"] = []
    try:
        for tr in trs:
            if tr.text.isspace():
                continue
            divs = tr.find_all("td")
            if len(divs) == 0:
                divs = tr.find_all("p")
                if len(divs) == 0:
                    continue
            k = 0
            if divs[0].text.strip() == "":
                k = 1
            currencies = currencies_trans.get(divs[k].text.strip(), None)
            if currencies is None:
                print tr.text
                sys.exit(0)
            if currencies != -1:
                if divs[k+1].text.strip() == "":
                    k += 1
                price = float(clean(divs[k+1].text.replace(",",".")))
                if divs[k+2].text.strip() == "":
                    k += 1
                ssi = float(clean(divs[k+2].text.replace(",",".")))
                row = {
                    "Date": datetime_,
                    "Currencies": currencies,
                    "Price": price,
                    "SSI": ssi,
                }
                u["data"].append(row)
    except Exception as e:
        print e
        sys.exit(0)
output = []
for u in urls.values():
    output += u["data"]
#pprint(output)
f = open("output.csv", "wb")
r = csv.DictWriter(f, output[0].keys())
r.writeheader()
r.writerows(output)