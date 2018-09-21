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




coord_type = raw_input("Enter in sexagesimal or decimal units? Enter 's' or 'd': ")
if coord_type=='s':
    coords_ra = raw_input("Enter RA as 'Hours:Minutes:Seconds': ")
    coords_dec = raw_input("Enter DEC as 'Degrees:Minutes:Seconds': ")
    coords_ra = coords_ra.split(':')
    RA = float(coords_ra[0])*15+float(coords_ra[1])/4+float(coords_ra[2])/240
    coords_dec = coords_dec.split(':')
    DEC = float(coords_dec[0])+np.sign(float(coords_dec[0]))*float(coords_dec[1])/60+np.sign(float(coords_dec[0]))*float(coords_dec[2])/60/60

else:
    coords = raw_input("RA and DEC coordinates in decimal degrees (format 'RA,DEC'): ")
    coords = coords.split(',')
    RA = float(coords[0])
    DEC = float(coords[1])

difference = np.zeros(np.shape(sources['RA_M']))
for j in range(len(sources['RA_M'])):
    RA_M = float(sources['RA_M'][j])
    DEC_M = float(sources['DEC_M'][j])
    difference[j] = math.sqrt((RA_M-RA)**2+(DEC_M-DEC)**2)
indices = []
for j in range(len(difference)):
    if difference[j]<7/60.:
        indices.append(j)

unqiue_stars = np.unique([sources['id'][i] for i in indices])

colors = []
Vmags = []
Vmags_err = []
colors_err = []

for starid in unqiue_stars:
    Vmag = [sources['MAG_V'][i] for i in indices if sources['id']==starid and not sources['MAG_V'][i]=='---' and not sources['MAG_V'][i]=='nan']
    Bmag = [sources['MAG_B'][i] for i in indices if sources['id']==starid and not sources['MAG_B'][i]=='---' and not sources['MAG_B'][i]=='nan']
    # Bmag = [sources['MAG_B'][i] if not sources['MAG_B'][i]=='---' and not sources['MAG_B'][i]=='nan']

    # print(Vmag,Bmag)
    if len(Vmag)==0 or len(Bmag)==0:
        continue
    mean_Vmag = np.mean(Vmag)
    mean_Bmag = np.mean(Bmag)
    mean_Vmag_std = np.std(Vmag)
    mean_Bmag_std = np.std(Bmag)
    color_err = np.sqrt(mean_Bmag_std*mean_Bmag_std+mean_Vmag_std*mean_Vmag_std) # add errors in quadrature 

    Vmags.append(mean_Vmag)
    Vmags_err.append(mean_Vmag_std)
    colors.append(mean_Bmag-mean_Vmag)
    colors_err.append(color_err)

plt.figure(figsize=(7,5))
plt.scatter(colors,Vmags)
plt.xlabel('color (B-V)')
plt.ylabel('V magnitude')
filename = raw_input('Filename for saving the plot (omit ext): ')
plt.savefig('plots/'+filename+'.png')
plt.show()
