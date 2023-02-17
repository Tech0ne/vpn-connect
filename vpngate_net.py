#!/usr/bin/python3

from requests import Session
from bs4 import BeautifulSoup
from sys import exit
from os import system, remove

import base64
import csv

URL = "https://www.vpngate.net/"

print("Fetching data, this can take a while...")

s = Session()

lst = s.get(URL + "api/iphone/")

with open("list.csv", 'w+') as f:
    f.write(lst.text)

f = open("list.csv", 'r')
data = csv.reader(f)

i = 1

total = []

for e in list(data)[2:]:
    if (len(e) == 15):
        print(f"{i}: {e[5]} - {e[12]} ({e[1]})")
        i += 1
        total.append(e[14])

f.close()

good = False
while not good:
    try:
        choice = int(input("> "))
    except:
        pass
    else:
        if choice > 0 and choice < len(total):
            good = True

config = base64.b64decode(total[choice].encode())

with open("config.ovpn", 'wb+') as n:
    n.write(config)

print("\nAlmost done ! If required, enter your password, and enjoy your connection !!!\n")
try:
    system("sudo openvpn config.ovpn")
except:
    pass

print("\nClearing...")

remove("list.csv")
remove("config.ovpn")

print("\nDone ! U welcome !!!\n")
