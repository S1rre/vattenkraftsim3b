# Funktion för att läsa csv-filer

import csv
import math
import numpy as np
from pathlib import Path

mapp = Path(r"2026-09/2026-09 frekvenser")
import os

print("Current working dir:", os.getcwd())
print("Folder exists:", mapp.exists())
print("Files found:", list(mapp.glob("*")))
period = 1000 # Tidssteg i ms

def läsData(period):
    Tider = []
    frekvenser = []
    aFRR = []
    Dagspris = []
    FCR = []
    steg = period // 100
    print('Sparar data med', period, 'ms')
    for fil in sorted(mapp.glob("*.csv")): # Iterera alla csv-filer i mappen
    #for fil in range(0):
        print(fil)
        with open(fil, "r", encoding="utf-8") as f:
            data = csv.reader(f)
            next(data) # Skippa första raden
            rader = list(data)

            offset = 0 # Behövs för ibland fattas det data i en tidpunkt
            mål_ms = 86400000 * int(rader[0][0][8:10])
            
            for t in range(0, len(rader), steg): # Iterera raderna med steg baserade på perioden

                DD = int(rader[t+offset][0][8:10]) # Plockar ut tider
                hh = int(rader[t+offset][0][11:13])
                mm = int(rader[t+offset][0][14:16])
                ss = int(rader[t+offset][0][17:19])
                ms = int(rader[t+offset][0][20:23])

                nuvarande_ms = (DD*86400 + hh*3600 + mm*60 + ss) * 1000 + ms

                if nuvarande_ms == mål_ms: #Testa så att inget fel uppstått påvägen
                    frekvenser.append(float(rader[t+offset][1]))  
                else: # Hanterar fel som uppstått på vägen
                    while nuvarande_ms > mål_ms:
                        offset -= 1
                        DD = int(rader[t+offset][0][8:10])
                        hh = int(rader[t+offset][0][11:13])
                        mm = int(rader[t+offset][0][14:16])
                        ss = int(rader[t+offset][0][17:19])
                        ms = int(rader[t+offset][0][20:23])
                        nuvarande_ms = (DD*86400 + hh*3600 + mm*60 + ss) * 1000 + ms
                    frekvenser.append(float(rader[t+offset][1]))
                Tider.append(mål_ms - 86400*1000)
                mål_ms += period

    with open(r"aFRR 261110.csv", "r", encoding="utf-8") as f:
        data = csv.reader(f)
        next(data) # Slänger header i datan
        rader = list(data)
        steg = period / (1000*60*60) # Stegtid i timmar
        position = 0

        #frekvenser = []*1000

        rad = 0
        
        for t in range(len(frekvenser)):
            förväntad_tid = math.floor(position)
            tid = int(rader[rad][1][8:10])*24-24 + int(rader[rad][1][11:13])

            while tid < förväntad_tid and rad < len(rader)-1: # Hanterar konstig data i filen
                rad += 1 # Kompenserar konstiga radnummer
                tid = int(rader[rad][1][8:10])*24 - 24 + int(rader[rad][1][11:13])

            aFRR.append(float(rader[rad][6]))
        
            position += steg
            position = round(position, 7)

    with open(r"Dagspris 261110.csv", "r", encoding="utf-8") as f:
        data = csv.reader(f)
        next(data)
        rader = list(data)
        steg = period / (1000*60) # Stegtid i minuter
        position = 0
        rad = 0

        #frekvenser = [1] * 1000

        for t in range(len(frekvenser)):
            förväntad_tid = math.floor(position)
            tid = int(rader[rad][1][8:10])*24*60 - 24*60 + int(rader[rad][1][11:13])*60 + int(rader[rad][1][14:16])

            while tid < förväntad_tid and rad < len(rader) - 1:
                rad += 1
                tid = int(rader[rad][1][8:10])*24*60 - 24*60 + int(rader[rad][1][11:13])*60 + int(rader[rad][1][14:16])

            Dagspris.append(float(rader[rad][4]))

            position += steg
            position = round(position, 7)

    with open(r"FCR 261110.csv", "r", encoding="utf-8") as f:
        data = csv.reader(f)
        next(data)
        rader = list(data)
        steg = period / (1000*60*60) # Stegtid i timmar
        position = 0
        rad = 0

        for t in range(len(frekvenser)):
            förväntad_tid = math.floor(position)
            tid = int(rader[rad][1][8:10])*24-24 + int(rader[rad][1][11:13])

            while tid < förväntad_tid and rad < len(rader) - 1:
                rad += 1
                tid = int(rader[rad][1][8:10])*24 - 24 + int(rader[rad][1][11:13])

            if rader[rad][6] == "fcrAuction1":
                FCR.append(rader[rad][7])
            else:
                FCR.append(float(rader[rad-1][7]))
                

            position += steg
            position = round(position, 7)

    return frekvenser, aFRR, Dagspris, FCR, Tider
        
Frekvenser, aFRR, Dagspris, FCR, Tider = läsData(period)

print('Klar')

np.savez(
    f"grid_data.npz_{period/1000}s",\
    frequencies = Frekvenser,
    time = Tider,
    dailyPrice = Dagspris,
    aFRR = aFRR,
    FCR = FCR
)

print('Sparat data')
