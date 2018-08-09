import observatory
observatory.checkversion()
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

# def find_comparison_stars(data,RA,DEC,magnitude,imagename):
#     choices = [data['id'][v] for v in range(len(data['id'])) if ]

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
        printright('Choice Registered: '+choice,clear=True)
        indices = np.nonzero(sources['id']==choice)[0]
        printright('%s data points found' % len(indices),delay=True)

    if choice=='2':
        printright('Choice Registered: Coordinate Lookup',clear=True)
        coord_type = raw_input("\tEnter in sexagesimal or decimal units? Enter 's' or 'd': ")
        if coord_type=='s':
            coords_ra = raw_input("\tEnter RA as 'Hours:Minutes:Seconds': ")
            coords_dec = raw_input("\tEnter DEC as 'Degrees:Minutes:Seconds': ")
            coords_ra = coords_ra.split(':')
            RA = float(coords_ra[0])*15+float(coords_ra[1])/4+float(coords_ra[2])/240
            coords_dec = coords_dec.split(':')
            DEC = float(coords_dec[0])+float(coords_dec[1])/60+float(coords_dec[2])/60/60

        else:
            coords = raw_input("\tRA and DEC coordinates in decimal degrees (format 'RA,DEC'): ")
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
            if difference[j]<1/60.:
                indices.append(j)

        print('\tFound %s data points within 1 arcminutes' % len(indices))
        radius_flag = raw_input("\tEnter smaller search radius in arcseconds or press Enter keep 1 arcmin: ")
        if radius_flag=='':
            pass
        else:
            radius = float(radius_flag)
            indices = []
            for j in range(len(difference)):
                if difference[j]<=radius/60.0/60.0:
                    indices.append(j)

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
                '[b] Return back to object selection',
                '[q] Quit the program'])

    printright('Choice Registered: '+filt,clear=True,delay=True)
    if filt=='q':
        print("\033c")
        sys.exit()
    elif filt=='b':
        print("\033c")
        sleep(0.2)
        header()
        sleep(0.2)
        continue


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
            datetimes = [datetime.strptime(sources['DATETIME'][x], '%Y-%m-%d %H:%M:%S.%f') for x in indices]
            start = np.amin(datetimes)
            end = np.amax(datetimes)
            printright('Choice Registered: All time data',clear=True,delay=True)

        mags,error,time = [],[],[]



        for x in indices:
            mags.append(sources['MAG_'+filt][x])
            error.append(sources['MAG_err'][x])
            time.append(datetime.strptime(sources['DATETIME'][x], '%Y-%m-%d %H:%M:%S.%f'))

        try:
            mags = [float(mags[x]) for x in range(len(mags)) if not math.isnan(float(mags[x]))]
        except ValueError:
            print('\tNo %s magnitude data found' % filt)
            sleep(0.5)
            print('\tReturning to Star Lookup')
            sleep(2.5)
            print("\033c")
            sleep(0.5)
            header()
            sleep(0.5)
            continue
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
        mag = np.mean(mags)
        RA_comparison = np.mean([sources['RA_M'][x] for x in indices])
        DEC_comparison = np.mean([sources['DEC_M'][x] for x in indices])
        possible_comparison_ids = []
        imgname_comparison = [sources['IMGNAME'][x] for x in indices][0]
        for j in range(len(sources['id'])):
            if abs(sources['MAG_'+filt][j]-mag)<1 and abs(sources['RA_M'][j]-RA_comparison)<0.2 and abs(sources['DEC_M'][j]-DEC_comparison)<0.2 and not str(sources['id'][j]).strip()=='nan' and sources['IMGNAME'][j]==imgname_comparison:
                possible_comparison_ids.append(sources['id'][j])
        possible_comparison_ids = np.unique(possible_comparison_ids)
        for j in range(len(possible_comparison_ids)):
            print('\t%s: %s, mag %s, N=%s' % (j+1,possible_comparison_ids[j],np.mean(sources['MAG_'+filt][j]),len(np.nonzero(sources['id']==possible_comparison_ids[j])[0])))
        print('')
        comparisonid = raw_input('\tComparison star selction (or enter for no comparison star): ')

        saveflag = raw_input("\tSave plot as file? (will also save summary statistics to .txt file [y/n]: ")
        if saveflag=='y':
            savename = raw_input("\tEnter custom filename (omit extension) or press enter to auto-generate filename: ")

        print("\t(if you're connecting remotely it may take a bit to display the plot...)")

        plt.figure(figsize=(10,8))
        label = str(filt+' mag')
        # data
        plt.errorbar(time, mags, c='k', label=label,yerr=error,fmt='.')
        # comparison
        if not comparisonid=='':
            comparisonid = possible_comparison_ids[int(comparisonid)-1]
            comparison_indices = np.nonzero(sources['id']==comparisonid)[0]
            mags_comparison,error_comparison,time_comparison = [],[],[]
            for x in comparison_indices:
                mags_comparison.append(sources['MAG_'+filt][x])
                error_comparison.append(sources['MAG_err'][x])
                time_comparison.append(datetime.strptime(sources['DATETIME'][x], '%Y-%m-%d %H:%M:%S.%f'))

            mags_comparison = [float(mags_comparison[x]) for x in range(len(mags_comparison)) if not math.isnan(float(mags_comparison[x]))]

            error_comparison = [float(error_comparison[x]) for x in range(len(error_comparison)) if not math.isnan(float(error_comparison[x]))]
            try:
                time_comparison = [time_comparison[x] for x in range(len(time_comparison)) if not math.isnan(float(mags_comparison[x]))]
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
        plt.errorbar(time_comparison,mags_comparison,c='m',label='Comparison star %s %s mag' % (comparisonid,filt),yerr = error_comparison,fmt='.')
        duration = end - start
        date_list = [start + timedelta(seconds=x) for x in range(0, int(duration.total_seconds()))]
        cmag = np.mean([float(sources['CMAG_'+filt][c]) for c in indices])
        cmags = [cmag for r in range(len(date_list))]
        plt.plot(date_list,cmags,linestyle='dashdot',color='black',label='Catalog '+filt+' mag')

        plt.legend()

        plt.ticklabel_format(useOffset=False,axis='y')
        
        plt.xlim(start,end)
        mean, std = np.mean(mags), np.std(mags)
        plt.ylim(mean-25*std,mean+25*std)
        plt.gca().invert_yaxis()
        plt.xlabel('Time')
        plt.ylabel('Magnitude')
        plt.xticks(rotation=50)
        plt.margins(0.2)
        plt.subplots_adjust(bottom=0.15)

       

        if choice=='2':
            plt.title('Star at %s, %s' % (RA,DEC))
            if saveflag=='y':
                if savename=='':
                    filename = 'star_%s_%s_%s.png' % (RA,DEC,filt)
                else:
                    filename = savename+'.png'
        else: 
            plt.title('UCAC4 %s' % choice)
            if saveflag=='y':
                if savename=='':
                    filename = 'star_%s_%s.png' % (choice,filt)
                else:
                    filename = savename+'.png'
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
            datetimes = [datetime.strptime(sources['DATETIME'][x], '%Y-%m-%d %H:%M:%S.%f') for x in indices]
            start = np.amin(datetimes)
            end = np.amax(datetimes)
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
        if saveflag=='y':
            savename = raw_input("\tEnter custom filename (omit extension) or press enter to auto-generate filename: ")
        plt.figure(figsize=(10,8))
        plt.scatter(time[0], mags[0], c='r', marker='.', label='R mag')
        plt.scatter(time[1], mags[1], c='g', marker='.', label='V mag')
        plt.scatter(time[2], mags[2], c='b', marker='.', label='B mag')


        plt.legend()

        plt.ticklabel_format(useOffset=False,axis='y')
        
        plt.xlim(start,end)

        mean, std = np.mean(mags[1]), np.std(mags[1])
        plt.ylim(mean-25*std,mean+25*std)
        plt.gca().invert_yaxis()
        plt.xlabel('Time')
        plt.ylabel('Magnitude')
        plt.xticks(rotation=50)
        plt.margins(0.2)
        plt.subplots_adjust(bottom=0.15)


        if choice=='2':
            plt.title('Star at %s, %s' % (RA,DEC))
            if saveflag=='y':
                if savename=='':
                    filename = 'star_%s_%s_all.png' % (RA,DEC)
                else:
                    filename = savename+'.png'
        else: 
            plt.title('UCAC4 %s' % choice)
            if saveflag=='y':
                if savename=='':
                    filename = 'star_%s_all.png' % choice
                else:
                    filename = savename+'.png'
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
