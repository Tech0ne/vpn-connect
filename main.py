#!./.venv/bin/python3

from rich import print
from rich.panel import Panel
from rich.live import Live
from rich.console import Console

from threading import Thread
from queue import Queue, Empty
from base64 import b64decode
from requests import get

import subprocess
import tempfile
import getch
import shlex

import time
import json
import sys
import os

MAX_CACHE_TIME = 2 * 24 * 60 * 60

PROCESS = None

console = Console()

def clear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def error(message: str) -> int:
    print(Panel("Error: " + message, border_style="red", title=":warning: Error ! :warning:", title_align="left"))
    return 1

def info(message: str):
    print(Panel(message, border_style="green", title="Info", title_align="left"))

def curl(url: str) -> bytes:
    info("Retreiving API infos...")
    p = Panel("", border_style="blue", title="[white]Requesting "+url.split('/')[-1], title_align="left", expand=False)
    response = get(url, stream=True)

    info("Returning VPN infos...")
    return response.content

def retreive_vpns():
    static_vpns = b'\n'
    if os.path.isfile("./.static_vpns"):
        with open("./.static_vpns", 'rb') as f:
            static_vpns += f.read()
    if not os.path.isfile("./.vpn_infos") or time.time() - os.path.getmtime("./.vpn_infos") >= MAX_CACHE_TIME:
        vpns = curl("http://www.vpngate.net/api/iphone")
        try:
            json.dump(vpns.decode(), open("./.vpn_infos", 'w+'))
        except TypeError:
            sys.exit(error("Could not decode VPNs infos !"))
        return vpns + static_vpns
    try:
        vpns = json.load(open("./.vpn_infos", 'r'))
    except:
        error("Could not load .vpn_infos.\nRegenerating...")
        os.remove("./.vpn_infos")
        return retreive_vpns()
    return vpns.encode() + static_vpns

def store_vpns(vpns: str) -> list[dict]:
    output = []
    vpns = vpns.replace('\r', '').replace('#', '').split('\n')
    if vpns[0][0] == "*":
        vpns = vpns[1:]
    keys = vpns[0].split(',')
    for e in vpns[1:]:
        current = {}
        valid = True
        for i in range(len(keys)):
            if i < len(e.split(',')):
                if keys[i].endswith("_Base64"):
                    current[keys[i][:-7]] = b64decode(e.split(',')[i].encode()).decode().replace('\r', '')
                else:
                    current[keys[i]] = e.split(',')[i]
            else:
                valid = False
        if valid:
            output.append(current)
    return output

def ask_keys(prompt: str, choices: list[str]) -> str:
    ok = False
    index = 0
    while not ok:
        clear()
        info(prompt)
        term_size = os.get_terminal_size()
        total_size = term_size[0]
        total_length = term_size[1]
        total_length -= 5 # length of the "info(prompt)"
        print("  ..." if max([0, index - (total_length // 2)]) > 0 else "")
        beggining = max([0, min([len(choices) - total_length + 1, index - (total_length // 2)])])
        end = min([len(choices), max([index, (total_length // 2)]) + (total_length // 2)])
        for i in range(beggining, end):
            choice = choices[i]
            if len(choice) + 6 > total_size:
                choice = choice[:total_size - 6] + '...'
            if i == index:
                print("> " + choice)
            else:
                print("  " + choice)
        print("  ..." if min([len(choices), index + (total_length // 2)]) < len(choices) else "")
        key = ord(getch.getch())
        if key == 27:
            getch.getch()
            key = ord(getch.getch())
        if key == 10:
            ok = True
        elif key == 65:
            index -= 1
            if index < 0:
                index = 0
        elif key == 66:
            index += 1
            if index >= len(choices):
                index = len(choices) - 1
        elif key == 113:
            sys.exit(error("User abort !"))
    return choices[index]

def make_nice_format(obj: list[dict], keys: list[str]) -> list[str]:
    lengths = {e: 0 for e in keys}
    for e in obj:
        for k in keys:
            if len(str(e[k])) > lengths[k]:
                lengths[k] = len(str(e[k]))
    output = []
    for e in obj:
        current = ""
        current += str(e[keys[0]])
        current += ' ' * (max([0, lengths[keys[0]] - len(str(e[keys[0]]))]))
        for k in keys[1:]:
            current += " - "
            current += str(e[k])
            current += ' ' * (max([0, lengths[k] - len(str(e[k]))]))
        output.append(current)
    return output

def run_command(command):
    global PROCESS
    info("Starting openvpn command...")
    scommand = shlex.split(command)
    PROCESS = subprocess.Popen(scommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info("Your connection should be up withing seconds.\nStop the VPN using Ctrl+C")
    while PROCESS.poll() is None:
        time.sleep(3)

def main(args: list[str]) -> int:
    if os.geteuid() != 0:
        return error("Please run as root !")
    vpns = retreive_vpns()
    info("Processing VPN infos...")
    try:
        vpns = vpns.decode()
    except:
        return error("Could not decode VPNs !")
    stored = store_vpns(vpns)
    country_shorts = list(set(make_nice_format(stored, ["CountryShort", "CountryLong"])))
    country = ask_keys("Please chose your country :", sorted(country_shorts)).split(' ')[0]
    choices = list(filter(lambda e: e.get("CountryShort") == country, stored))
    choices = sorted(choices, key=lambda e: int(e.get("Score")), reverse=True)
    target = ask_keys("Please chose your VPN :", make_nice_format(choices, ["IP", "HostName", "Operator"]))
    target = list(filter(lambda e: e.get("IP") == target.split(' ')[0], choices))[0]
    print(target)
    info("Connecting to " + target.get("IP") + "...")
    tmp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    tmp_file.write(target.get("OpenVPN_ConfigData"))
    file_name = tmp_file.name
    tmp_file.close()
    try:
        run_command("openvpn --config " + file_name)
    except KeyboardInterrupt:
        if PROCESS is not None:
            PROCESS.kill()
        print()
        info("Connection closed successfully !")
        return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
