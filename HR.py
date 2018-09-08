import os
import csv
import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
import glob

def openData(filename):
    with open(filename) as csvFile:
        reader = csv.reader(csvFile)
        keys = next(reader)
    dictionary = dict()
    for i in keys:
        df = pd.read_csv(filename)
        dictionary[i]=np.array(df[i])
    return dictionary

sources = openData('sources.csv')

unique_stars = np.unique([i for i in sources['id'] if not i=='nan'])
print(unique_stars)

colors = []
Vmags = []

for starid in unique_stars:
    Vmag = [sources['MAG_V'][i] for i in range(len(sources['MAG_V'])) if sources['id'][i]==starid and not sources['MAG_V'][i]=='---' and not sources['MAG_V'][i]=='nan']
    Bmag = [sources['MAG_B'][i] for i in range(len(sources['MAG_B'])) if sources['id'][i]==starid and not sources['MAG_B'][i]=='---' and not sources['MAG_B'][i]=='nan']
    print(Vmag,Bmag)
    if len(Vmag)==0 or len(Bmag)==0:
        continue
    mean_Vmag = np.mean(Vmag)
    mean_Bmag = np.mean(Bmag)
    Vmags.append(mean_Vmag)
    colors.append(mean_Bmag-mean_Vmag)

plt.figure(figsize=(7,5))
plt.plot(colors,Vmags)
plt.xlabel(color B-V)
plt.ylabel(V magnitude)
plt.show()
