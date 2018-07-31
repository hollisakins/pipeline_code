from observatory import checkversion
checkversion()
import csv
import pandas as pd 
import math
import numpy as np
import matplotlib.pyplot as plt 

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

mags = []
stds = []
data = []
data_gathered = False
while data_gathered==False:
    filt = raw_input('\tFor which filter would you like to plot the data? [R/V/B]: ')
    for j in set(sources['id']):
        try:
            if math.isnan(float(j)):
                continue
        except:
            pass
        indices = np.nonzero(sources['id']==j)[0]
        current_mags = []
        for m in indices:
            current_mags.append(sources['MAG_'+filt][m])
        # print(str(j)+':','mean: ',round(np.mean(current_mags),3),'std: ',round(np.std(current_mags),3),'range: ',round(np.max(current_mags)-np.min(current_mags),3),'# of data points: ',len(current_mags))
        try:
            stds.append(np.std(current_mags))
            mags.append(np.mean(current_mags))
            data.append(len(current_mags))
            data_gathered = True
        except TypeError:
            print('\tNo data for %s filter, please select another' % filt)
            break

stds_numbers = []
for j in range(len(mags)):
    stds_numbers.append([stds[j],data[j]])

stds_numbers = np.sort(stds_numbers,axis=1)
print('\tFor the 8 stars with the most data points...')
mean = np.mean([stds_numbers[i,0] for i in range(8)])
print('\tThe mean standard deviation is '+str(mean))


saveflag = raw_input("\tWould you like to save this plot? [y/n]: ")
plt.xlabel('Mean magnitude')
plt.ylabel('Standard deviation')
plt.scatter(mags,stds,s=data,c='k')
if saveflag=='y':
    plt.savefig('limiting_mag.png')
plt.show()