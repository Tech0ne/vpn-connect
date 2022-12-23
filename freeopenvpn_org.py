#!/usr/bin/python3

from requests import Session
from bs4 import BeautifulSoup
from sys import exit
from os import system, remove

from PIL import Image

URL = "https://www.freeopenvpn.org/"


print("Welcome !")
print("Here is a simple script to connect to freeopenvpn.org, with (almost) everything auto !")
print()


o = Session()

r = o.get(URL)

soup = BeautifulSoup(r.text, 'html.parser')

buttons = soup.find_all('a')

out = []

for b in buttons:
    if "premium.php?cntid=" in b.get('href'):
        out.append(URL + b.get('href'))

print()
print("Please chose your country :")
print()

i = 1

for h in out:
    string = h.split("https://www.freeopenvpn.org/premium.php?cntid=")[1].split('&')[0]
    print(f"{i} : {string}")
    i += 1

print()

is_good = False
while not is_good:
    chx = input("> ")
    try:
        ichx = int(chx)
    except:
        continue
    ichx -= 1
    if ichx >= 0 and ichx < len(out):
        is_good = True

print()
print(f"Choice : {out[ichx]}")
print()

print("Please chose between TCP (1) and UDP (2) :")
print("If you don't know the differences, chose TCP with 1")
print()
chx = input("> ")
while not chx in ('1', '2'):
    chx = input("> ")

mode = "tcp" if chx == '1' else "udp"

print()
print("Downloading config file...")
print()

r = o.get(out[ichx])
s = BeautifulSoup(r.text, 'html.parser')
x = s.find_all('a')

config_url = ""

for e in x:
    if "https://www.freeopenvpn.org/ovpn/" in e.get('href') and mode in e.get('href'):
        config_url = e.get('href')

r = o.get(config_url)
with open("config.ovpn", 'wb+') as f:
    f.write(r.content)

print()
print("Config file downloaded, now, we get the creds...")
print()

ps = s.find_all('p')
uname = ""
for e in ps:
    if not "Username:" in e.get_text():
        continue
    for b in e.find_all('b'):
        uname = b.get_text()
if uname == "":
    print()
    print("Could not retreive username !")
    print()
    exit(1)

print()
print(f"Got username : {uname}")
print(f"Retreiving password...")
print()

pass_url = ""

for e in s.find_all("script"):
    if "result.innerHTML = 'Password/PIN: <img src=" in e.get_text():
        pass_url = e.get_text().split("result.innerHTML = 'Password/PIN: <img src=\"")[1].split('"')[0]
        pass_url = URL + pass_url

pass_url, key_data = pass_url.split('?')

r = o.get(pass_url, data={key_data: ''}, headers={"Accept": "image/avif,image/webp,*/*", "Referer": out[ichx]})

with open("pass.png", 'wb+') as f:
    f.write(r.content)

print()
print("My OCR doesn't works well, as all aviables OCR are dog sh*t. Can you write the numbers you see plz ?")
print()
system("catimg pass.png")
print()
text = input("> ")

with open("creds.txt", 'w+') as f:
    f.write(f"{uname}\n{text}\n")

print()
print("Everything is ready to start ! Please type your password if it's required, and stop with ctrl+c !")
print()

system("sudo openvpn --config config.ovpn --data-ciphers 'AES-128-CBC' --auth-user-pass creds.txt")

remove("config.ovpn")
remove("pass.png")
remove("creds.txt")

print()
print("Everything is cleared, please thanks me if it was helpfull ;)")
print()
