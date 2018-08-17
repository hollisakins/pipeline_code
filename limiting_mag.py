import os
import csv
import pandas as pd 
import math
import numpy as np
import matplotlib.pyplot as plt 
import glob

print("\033c")

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

path = raw_input("\tPath to files including filename w/ * syntax: ")
filenames = glob.glob(path)
for i in range(len(filenames)):
    filenames[i] = os.path.basename(filenames[i])
filenames = [f for f in filenames if not f.endswith('.SRC')]
print(filenames)
mags = []
stds = []
data = []


filt = raw_input('\tFor which filter would you like to plot the data? [R/V/B]: ')
for filename in filenames:
    indices = np.nonzero(sources['IMGNAME']==filename)[0]

    identifiers = [sources['id'][x] for x in indices]
    identifiers = np.unique(identifiers)
    for starid in identifiers:
        current_mags = [sources['MAG_'+filt][j] for j in indices if sources['id'][j]==starid]
        stds.append(np.std(current_mags))
        mags.append(np.mean(current_mags))
        data.append(len(current_mags))


saveflag = raw_input("\tWould you like to save this plot? [y/n]: ")
plt.xlabel('Mean magnitude')
plt.ylabel('Standard deviation')
plt.scatter(mags,stds,s=data,c='k')
if saveflag=='y':
    targname = raw_input('\tTarget name: ')
    plt.savefig('plots/%s_limiting_mag.png' % targname)
plt.show()
