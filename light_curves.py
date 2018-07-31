import pandas as pd
import numpy as np
import csv
import math
from datetime import datetime,timedelta
from time import sleep
import matplotlib.pyplot as plt
import matplotlib
import sys
import os
import random

import sys

vers = '%s.%s' % (sys.version_info[0],sys.version_info[1])
if not vers=='2.7':
    raise Exception("Must be using Python 2.7")


print("\033c")
rows, columns = os.popen('stty size', 'r').read().split()
termsize = int(columns)


def bold(msg):
    return u'\033[1m%s\033[0m' % msg

def header():
    print('-'*termsize)
    print(bold('Plotting Light Curves:').center(termsize))
    print('a part of The Guilford College Cline Observatory Data Analysis Pipeline Project'.center(termsize))
    print('-'*termsize)
    print('')

def printright(printout,clear=False,delay=False):
    if clear==True:
        print("\033c")
        header()
    print(' '*(termsize-len(printout)-8)+printout)
    if delay==True:
        sleep(0.3)

def options(head,items):
    print('')
    print('\t'+bold(head))
    print(('-'*(termsize-16)).center(termsize))
    for j in items:
        print('\t'+j)
    choice = raw_input('\tChoice: ')
    return choice

def print_slow(t,indent=1,speed=100):
    i = ' '*8*indent
    sys.stdout.write(i)
    #print(i,end='')
    for l in t:
        sys.stdout.write(l)
        sys.stdout.flush()
        sleep(random.random()*10.0/speed)
    print('')
    sleep(0.2)

def init():
    header()
    sleep(1)
    printright('[press ^C at any time to skip this intro]')
    try:
        print_slow('This program facilitates the following tasks:',indent=1)
        print_slow('Analysis of data collected and run through the data pipeline',indent=2)
        print_slow('Plotting of light curves for various optical filters and time spans',indent=2)
        print_slow('..........',indent=int((termsize/2-5)/8),speed=10)
        sleep(1)
        print("\033c")
        header()
        sleep(3)
    except KeyboardInterrupt:
        print("\033c")
        header()
        sleep(0.5)
    
def openData(filename):
    with open(filename) as csvFile:
        reader = csv.reader(csvFile)
        keys = next(reader)
    dictionary = dict()
    for i in keys:
        df = pd.read_csv(filename)
        dictionary[i]=np.array(df[i])
    return dictionary

# init()
header()
sources = openData('sources.csv')


while True:
    choice = options('Star Entry: ',
                ['[1] Star lookup by UCAC4 ID',
                '[2] Star lookup by coordinates',
                '[3] View list of matched UCAC4 stars',
                '[q] Quit the program'])

    if choice=='q':
        print("\033c")
        sys.exit()

    if choice=='3':
        choices = [v for v in sources['id'] if not v=='nan']
        choices,counts = np.unique(choices,return_counts=True)
        choices = [v for v in choices if not v=='nan']
        a = []
        for j in range(len(choices)):
            a.append((choices[j],counts[j])) 
        dtype = [('id', 'U10'), ('count', int)]
        a = np.array(a, dtype=dtype)
        choices = np.sort(a, order='count')
        choices = np.array(list(reversed(choices)))   
        linelength = 0
        print('')
        print('\t(sorted by amount of data)')
        sys.stdout.write('\t')
        for m in range(len(choices)-1):
            spaces = ' '*(5-len(str(m+1)))
            printstatement = '%s: %s%s' % (m+1, str(choices[m][0]),spaces)
            if linelength>(termsize-55):
                linelength = 0
                print(printstatement)
                sys.stdout.write('\t')
                linelength += len(printstatement)
            else:
                sys.stdout.write(printstatement)
                linelength += len(printstatement)


        choice=int(raw_input("\n\n\tSelection (number): "))
        choice = str(choices[choice-1][0])
        printright('Choice Registered: Test Star '+choice,clear=True)
        indices = np.nonzero(sources['id']==choice)[0]
        printright('%s data points found' % len(indices),delay=True)

    if choice=='2':
        printright('Choice Registered: Coordinate Lookup',clear=True)
        coords = raw_input("\tRA and DEC coordinates in decimal decrees (format 'RA,DEC'): ")
        coords = coords.split(',')
        RA = float(coords[0])
        DEC = float(coords[1])
        difference = np.zeros(np.shape(sources['RA_M']))
        for j in range(len(sources['RA_M'])):
            RA_M = float(sources['RA_M'][j])
            DEC_M = float(sources['DEC_M'][j])
            difference[j] = np.sqrt((RA_M-RA)**2+(DEC_M-DEC)**2)

        indices = np.nonzero(difference<(2/60/60))[0]
        printright('%s data points found' % len(indices),delay=True)

    if choice=='1':
        choice = raw_input('\tUCAC4 ID: ')
        printright('Choice Registered: UCAC4 ID Star '+choice,clear=True)

        indices = np.nonzero(sources['id']==choice)[0]
        printright('%s data points found' % len(indices),delay=True)

    filt = options('Optical Filter Choice (selecting all filter data does not yield as much information as viewing a single filter at a time): ',
                ['[R] R band (red) fitler',
                '[V] V band (visual) filter',
                '[B] B band (blue) filter',
                '[a] View all filter data',
                '[q] Quit the program'])

    printright('Choice Registered: '+filt,clear=True,delay=True)
    if filt=='q':
        print("\033c")
        sys.exit()


    if not filt=='a':
        timeflag = options('Date/Time Entry: ',
                ['[1] Enter start/end manually',
                '[a] View all time data',
                '[q] Quit the program'])
                
        if timeflag=='q':
            print("\033c")
            sys.exit()

        if timeflag=='1':
            printright('Choice Registered: Manual Entry',clear=True,delay=True)
            print('')
            print('\t'+bold('Date/Time Entry: '))
            print(('-'*(termsize-16)).center(termsize))
            print('\tEnter dates as YYYY/MM/DD/HH/mm in GMT/24hr')
            start = raw_input("\tStart time: ")
            end = raw_input("\tEnd time: ")
            printright('Choice Registered: from %s to %s' % (start,end),clear=True)
            start = datetime.strptime(start,'%Y/%m/%d/%H/%M')
            end = datetime.strptime(end,'%Y/%m/%d/%H/%M')
        
        if timeflag=='a':
            start = datetime.strptime(np.amin(sources['DATETIME']), '%Y-%m-%d %H:%M:%S.%f')
            end = datetime.strptime(np.amax(sources['DATETIME']), '%Y-%m-%d %H:%M:%S.%f')
            printright('Choice Registered: All time data',clear=True,delay=True)

        mags,error,time = [],[],[]



        for x in indices:
            mags.append(sources['MAG_'+filt][x])
            error.append(sources['MAG_err'][x])
            time.append(datetime.strptime(sources['DATETIME'][x], '%Y-%m-%d %H:%M:%S.%f'))

        mags = [float(mags[x]) for x in range(len(mags)) if not math.isnan(float(mags[x]))]

        error = [float(error[x]) for x in range(len(error)) if not math.isnan(float(error[x]))]
        try:
            time = [time[x] for x in range(len(time)) if not math.isnan(float(mags[x]))]
        except IndexError:
            print('\tNo %s magnitude data found' % filt)
            sleep(0.5)
            print('\tReturning to Star Lookup')
            sleep(2.5)
            print("\033c")
            sleep(0.5)
            header()
            sleep(0.5)
            continue

        saveflag = raw_input("\tSave plot as file? (will also save summary statistics to .txt file [y/n]: ")


        plt.figure(figsize=(10,8))
        label = str(filt+' mag')
        plt.errorbar(time, mags, c='k', label=label,yerr=error,fmt='.')
        
        duration = end - start
        date_list = [start + timedelta(seconds=x) for x in range(0, int(duration.total_seconds()))]
        cmag = np.mean([float(sources['CMAG_'+filt][c]) for c in indices])
        cmags = [cmag for r in range(len(date_list))]
        plt.plot(date_list,cmags,linestyle='dashdot',color='black',label='Catalog '+filt+' mag')

        plt.legend()
        plt.gca().invert_yaxis()

        plt.ticklabel_format(useOffset=False,axis='y')
        
        plt.xlim(start,end)
        mean, std = np.mean(mags), np.std(mags)
        plt.ylim(mean-25*std,mean+25*std)
        plt.xlabel('Time')
        plt.ylabel('Magnitude')
        plt.xticks(rotation=50)
        plt.margins(0.2)
        plt.subplots_adjust(bottom=0.15)

       

        if choice=='C':
            plt.title('Star at %s, %s' % (RA,DEC))
            if saveflag=='y':
                filename = 'star_%s_%s_%s.png' % (RA,DEC,filt)
        else: 
            plt.title('UCAC4 %s' % choice)
            if saveflag=='y':
                filename = 'star_%s_%s.png' % (choice,filt)
        if saveflag=='y':
            plt.savefig('plots/'+filename)
            with open('plots/'+filename.replace('.png','.txt'),'w') as t:
                t.write('mean: '+str(np.mean(mags))+'\n')
                t.write('std: '+str(np.std(mags))+'\n')
                t.write('N: '+str(len(mags))+'\n')
                q75, q25 = np.percentile(mags, [75 ,25])
                iqr = q75 - q25
                t.write('min: '+str(np.min(mags))+'\n')
                t.write('1st quartile: '+str(q25)+'\n')
                t.write('median: '+str(np.median(mags))+'\n')
                t.write('3rd quartile: '+str(q75)+'\n')
                t.write('max: '+str(np.max(mags))+'\n')
                t.write('IQR: '+ str(iqr)+'\n')
                t.write('Start Date/Time: '+str(start)+' UTC\n')
                t.write('End Date/Time: '+str(end)+' UTC')

        plt.show()


    if filt=='a':
        timeflag = options('Date/Time Entry: ',
                ['[1] Enter start/end manually',
                '[a] View all time data',
                '[q] Quit the program'])

        if timeflag=='q':
            print("\033c")
            sys.exit()

        if timeflag=='1':
            printright('Choice Registered: Manual Entry',clear=True,delay=True)
            print('')
            print('\t'+bold('Date/Time Entry: '))
            print(('-'*(termsize-16)).center(termsize))
            print('\tEnter dates as YYYY/MM/DD/HH/mm in GMT/24hr')
            start = raw_input("\tStart time: ")
            end = raw_input("\tEnd time: ")
            printright('Choice Registered: from %s to %s' % (start,end),clear=True)
            start = datetime.strptime(start,'%Y/%m/%d/%H/%M')
            end = datetime.strptime(end,'%Y/%m/%d/%H/%M')
        if timeflag=='a':
            start = datetime.strptime(np.amin(sources['DATETIME']), '%Y-%m-%d %H:%M:%S.%f')
            end = datetime.strptime(np.amax(sources['DATETIME']), '%Y-%m-%d %H:%M:%S.%f')
            printright('Choice Registered: All time data',clear=True,delay=True)

        filt = ['R','V','B']
        mags,time = [[],[],[]],[[],[],[]]
        for x in indices:
            for j in range(len(filt)):
                if sources['MAG_'+filt[j]][x]=='---':
                    mags[j].append(sources['MAG_'+filt[j]][x])
                else:
                    mags[j].append(float(sources['MAG_'+filt[j]][x]))
                time[j].append(datetime.strptime(sources['DATETIME'][x], '%Y-%m-%d %H:%M:%S.%f'))

        nodata = 0
        for j in range(len(filt)):
            time[j] = [time[j][x] for x in range(len(time[j])) if isinstance(mags[j][x], float)]
            mags[j] = [mags[j][x] for x in range(len(mags[j])) if isinstance(mags[j][x], float)]
        

        saveflag = raw_input("\tSave plot as file? [y/n]: ")
        plt.figure(figsize=(10,8))
        plt.scatter(time[0], mags[0], c='r', marker='.', label='R mag')
        plt.scatter(time[1], mags[1], c='g', marker='.', label='V mag')
        plt.scatter(time[2], mags[2], c='b', marker='.', label='B mag')


        plt.legend()
        plt.gca().invert_yaxis()

        plt.ticklabel_format(useOffset=False,axis='y')
        
        plt.xlim(start,end)

        mean, std = np.mean(mags[1]), np.std(mags[1])
        plt.ylim(mean-25*std,mean+25*std)
        plt.xlabel('Time')
        plt.ylabel('Magnitude')
        plt.xticks(rotation=50)
        plt.margins(0.2)
        plt.subplots_adjust(bottom=0.15)


        if choice=='C':
            plt.title('Star at %s, %s' % (RA,DEC))
            if saveflag=='y':
                filename = 'star_%s_%s.png' % (RA,DEC)
        else: 
            plt.title('UCAC4 %s' % choice)
            if saveflag=='y':
                filename = 'star_%s' % choice
        if saveflag=='y':
            plt.savefig('plots/'+filename)
        plt.show()

    if saveflag=='y':
        printright('Plot saved as %s' % filename,clear=True,delay=True)
    else:
        printright('Plot not saved',clear=True,delay=True)

    loopflag = options('What would you like to do next?',
                ['[1] Return to the beginning to plot another curve',
                '[q] Quit the program'])
    print("\033c")
    if loopflag=='q':
        sys.exit()

    if loopflag=='1':
        sleep(0.2)
        header()
        sleep(0.2)
        continue
