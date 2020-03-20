"""covid19_display - displays current stats on MiniPiTFT

"""
############################################################################
# covid19_display.py - display current disease progression svalues
# on an Adafruit MiniPiTVT on a Raspberry Pi.
#
# Author:      Phil Moyer (phil@moyer.ai)
# Date:        March 2020
#
# This program is released under the MIT license.
############################################################################


######################
# Import Libraries
######################

# Standard libraries modules
import time
import re
import requests
import datetime

# Third-party modules
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

from board import SCL, SDA
import busio
import digitalio
import board
from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789

# Package/application modules


######################
# Globals
######################



######################
# Classes and Methods
######################



######################
# Functions
######################

def getStats():
    url = "https://www.worldometers.info/coronavirus/country/us/"
    url2 = "https://www.worldometers.info/coronavirus/"
 
    response = requests.get(url)
    response2 = requests.get(url2)

    # Use BeautifulSoup library to parse the URLs we just retrieved
    soup = BeautifulSoup(response.text, "html.parser")
    soup2 = BeautifulSoup(response2.text, "html.parser")

    stats = []
    tmpList = []
 
    # For each statement to catch all lines of code that contain h1 tag
    for el in soup.findAll('h1'):
        if "Coronavirus" in str(el):
            tStr = (re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))
            if tStr.startswith('\n'):
                stats.append(tStr[1:(len(tStr) - 1)])
            else:
                stats.append(re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))
        elif "Deaths" in str(el):
            tStr = (re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))
            if tStr.startswith('\n'):
                stats.append(tStr[1:(len(tStr) - 1)])
            else:
                stats.append(re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))
 
    for el in soup2.findAll('h1'):
        if "Coronavirus" in str(el):
            tStr = (re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))
            if tStr.startswith('\n'):
                stats.append(tStr[1:(len(tStr) - 1)])
            else:
                stats.append(re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))
        if "Deaths" in str(el):
            tStr = (re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))
            if tStr.startswith('\n'):
                stats.append(tStr[1:(len(tStr) - 1)])
            else:
                stats.append(re.sub('<[^<]+?>', '', str(el.find_next_sibling())).replace(" ", ""))

    return stats
 

def main():
    """Abstract main() into a function. Normally exits after execution.

    A function abstracting the main code in the module, which
    allows it to be used for libraries as well as testing (i.e., it can be
    called as a script for testing or imported as a library, without
    modification).
    """
    # Create the I2C interface.
    i2c = busio.I2C(SCL, SDA)
 
    cs_pin = digitalio.DigitalInOut(board.CE0)
    dc_pin = digitalio.DigitalInOut(board.D25)
    reset_pin = None
    BAUDRATE = 6400000

    disp = st7789.ST7789(
        board.SPI(),
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        baudrate=BAUDRATE,
        width=135,
        height=240,
        x_offset=53,
        y_offset=40,
    )

    height = disp.width
    width = disp.height
    image = Image.new("RGB", (width, height))
    rotation = 90
    
    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)
 
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=(0,0,0))
    disp.image(image, rotation)

    padding = -2
    top = padding
    bottom = height - padding

    x = 0
 
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
 
    # Create array named difference with size 4 elements all with value 0
    difference = [0] * 4
 
    while True:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
 
        try:
            oldstats = newstats
        except:
            print("[!] Starting i2c device")
 
        try:
            newstats = getStats()
        except Exception as e:
            print("[!] Error retrieving stats; website most likely denied request. Reattempting in 60 seconds")
            time.sleep(60)
            try:
                newstats = getStats()
            except Exception as e:
                print("[!] Error retrieving second time; waiting 2m50s then running again")
                time.sleep(150)
                continue

        try:
            difference[0] += (int(re.sub("\D", "", newstats[0])) - int(re.sub("\D", "", oldstats[0])))
            difference[1] += (int(re.sub("\D", "", newstats[1])) - int(re.sub("\D", "", oldstats[1])))
            difference[2] += (int(re.sub("\D", "", newstats[2])) - int(re.sub("\D", "", oldstats[2])))
            difference[3] += (int(re.sub("\D", "", newstats[3])) - int(re.sub("\D", "", oldstats[3])))
 
        except Exception as e:
            print("[!] Variable old stats does not exist yet; most likely first run")
        try:
            y = top
            draw.text((x, y), "US C:" + "{:>7}".format(newstats[0]) + " (+" + str(difference[0]) + ")", font=font, fill="#FFFFFF")
            y += font.getsize("US")[1]

            draw.text((x, y), "US D:" + "{:>7}".format(newstats[1]) + " (+" + str(difference[1]) + ")", font=font, fill="#FFFF00")
            y += font.getsize("US")[1]

            draw.text((x, y), "WW C:" + "{:>7}".format(newstats[2]) + " (+" + str(difference[2]) + ")", font=font, fill="#00FF00")
            y += font.getsize("WW")[1]

            draw.text((x, y), "WW D:" + "{:>7}".format(newstats[3]) + " (+" + str(difference[3]) + ")", font=font, fill="#FF00FF")
        except Exception as e:
            print("[!] Error:", e)
            continue
 
        # Display image.
        disp.image(image, rotation)
        print("[*] Updated stats at:", datetime.datetime.now())
        time.sleep(300)



######################
# Main
######################

# The main code call allows this module to be imported as a library or
# called as a standalone program because __name__ will not be properly
# set unless called as a program.

if __name__ == "__main__":
    main()

