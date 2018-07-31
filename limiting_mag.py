#hello!
import csv
import pandas as pd 
import math
import numpy as np
import matplotlib.pyplot as plt 

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

for j in set(sources['id']):
    try:
        if math.isnan(float(j)):
            continue
    except:
        pass
    indices = np.nonzero(sources['id']==j)[0]
    current_mags = []
    for m in indices:
        current_mags.append(sources['MAG_B'][m])
    # print(str(j)+':','mean: ',round(np.mean(current_mags),3),'std: ',round(np.std(current_mags),3),'range: ',round(np.max(current_mags)-np.min(current_mags),3),'# of data points: ',len(current_mags))
    stds.append(np.std(current_mags))
    mags.append(np.mean(current_mags))
    data.append(len(current_mags))

stds_numbers = []
for j in range(len(mags)):
    stds_numbers.append([stds[j],data[j]])

stds_numbers = np.sort(stds_numbers,axis=1)
print('for the 8 stars with the most data points...')
mean = np.mean([stds_numbers[i,0] for i in range(8)])
print('mean std deviation is '+str(mean))



plt.ylabel('Mean magnitude for star over time series')
plt.xlabel('Standard deviation for star over time series')
plt.title('Color represents amount of data (yellow = more)')
plt.scatter(stds,mags,s=80,c=data)
plt.show()