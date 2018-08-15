#
#
#


import sys
vers = '%s.%s' % (sys.version_info[0],sys.version_info[1])
if not vers=='2.7':
    raise Exception("Must be using Python 2.7")



#####################################################################################################################################################
### import dependent packages
#####################################################################################################################################################

# standard packages
import numpy as np 
import math 
import os # for interacting with the terminal 
import warnings # for suppressing warnings
import csv # for reading/writing from csv files
import shutil # solely for copying .SRC files between directories 
from datetime import datetime,timedelta
from time import strftime, gmtime, strptime, sleep, localtime
import datetime as dt
from collections import OrderedDict # make Python 2.7 dictionary act like 3.6 dictionary 
import pandas as pd

# astro packages
from astropy.io import fits # fits module for opening and writing to fits files
from astropy import wcs # world coordinate system module for converting .SRC file data to RA/Dec
from astroquery.vizier import Vizier # for looking up stars in catalogs listed in Vizier
import astropy.coordinates as coord # for inputting coordinates into Vizier
import astropy.units as u # for units for the coord module
import sep # source extraction package based on the SExtractor application

# email packages
from email.MIMEMultipart import MIMEMultipart
import smtplib
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders



#####################################################################################################################################################
### define variables and other housekeeping things
#####################################################################################################################################################

# defines variable for the the width of the console to print output more clearly 
rows, columns = os.popen('stty size', 'r').read().split()
termsize = int(columns)


# astropy gives warning for a depricated date format in TheSkyX fits header, we dont need to see that so these two lines supress all warnings
# comment them out when testing
warnings.catch_warnings() 
warnings.simplefilter('ignore')


# define the start and end times as empty strings which will be updated by pipeline.py for email update
start_time = ''
end_time = ''

# variable definitions (do not change here, change from pipeline.py)
slow = False 
days_old = 1 
verbose_errors = False 



#####################################################################################################################################################
### define email update functions (for remote monitoring)
#####################################################################################################################################################

def sendError(message):
    '''Sends an email to recipients listed in email_recipients.txt whenever the program encounters an unexpected and fatal error '''
    
    # set up the SMTP server
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()

    print('Fatal error, sending email alert')
    sleep(0.5)

    # log into the gmail account
    address = 'gcdatapipeline@gmail.com' 
    password = '**Mintaka'
    s.login(address,password) 

    # begin the message
    msg = MIMEMultipart()
    msg['From'] = 'Guilford College Cline Observatory'
    msg['Subject'] = "Fatal Error: GC Data Pipeline %s" % strftime("%Y-%m-%d", localtime())
    
    # begin body of message with HTML formatting
    body = """<font="Courier">
    <b><h2>Fatal Error in Pipeline Run:</h2></b>
    <br />
    Today's pipeline run encountered a fatal error and did not finish. <br />
    Here is the error message:<br />
    <br />
    Error time: %s <br />
    %s <br />
    <br />
    Attached is the full error log. </font>
    """ % (strftime("%H:%M EST", localtime()), message)
    
    # add the body message to the string
    msg.attach(MIMEText(body, 'html'))
    
    # attach the error log
    filename = 'errorlog.txt'
    with open(filename,'rb') as attachment:    
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)
    text = msg.as_string()

    # open receipients file and store as list
    with open('email_recipients.txt','r') as f:
        recipients = f.read().splitlines()

    # make string of receipients just to print it out cleanly
    all_recipients = recipients[0]
    for x in range(1,len(recipients)):
        all_recipients += ', '+recipients[x]
    print('Sending error message to %s\n' % all_recipients)
    sleep(1)

    # for each recipient, change 'To' variable and send message
    for recipient in recipients:
        msg['To'] = recipient
        s.sendmail(address, recipient, text)
    
    # quit SMTP server
    s.quit()


def sendStatus():
    '''Run's at the end of the pipeline to send a summary of the run to recipients listed in email_recipients.txt'''

    # print header
    header('Sending Update')
    
    # read CSV file with output data
    with open('sources.csv') as csvFile:
        reader = csv.reader(csvFile)
        keys = next(reader)
    dictionary = dict()
    for i in keys:
        df = pd.read_csv('sources.csv')
        dictionary[i]=np.array(df[i])
    sources = dictionary

    # define variables using list comprehension from the output data
    images_processed = len(np.unique([sources['IMGNAME'][x] for x in range(len(sources['IMGNAME'])) if isinstance(sources['RUNTIME'][x],str) and datetime.strptime(sources['RUNTIME'][x],"%Y-%m-%d %H:%M GMT").day==datetime.utcnow().day]))
    stars_logged = len(np.unique([sources['id'][x] for x in range(len(sources['id'])) if isinstance(sources['RUNTIME'][x],str) and datetime.strptime(sources['RUNTIME'][x],"%Y-%m-%d %H:%M GMT").day==datetime.utcnow().day]))
    if not images_processed==0:
        stars_not_matched = round(float(len([sources['id'][x] for x in range(len(sources['id'])) if str(sources['id'][x])=='nan' and isinstance(sources['RUNTIME'][x],str) and datetime.strptime(sources['RUNTIME'][x],"%Y-%m-%d %H:%M GMT").day==datetime.utcnow().day]))/float(images_processed),2)
    else:
        stars_not_matched = 0

    # set up the SMTP server
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    print('Established SMTP server')
    sleep(0.5)

    # login to the gmail account
    address = 'gcdatapipeline@gmail.com'
    password = '**Mintaka'
    s.login(address,password)

    # begin the message
    msg = MIMEMultipart()
    msg['From'] = 'Guilford College Cline Observatory'
    msg['Subject'] = "GC Data Pipeline Update %s" % strftime("%Y-%m-%d", localtime())
    
    # begin the body of the message with HTML formatting and including variables
    body = """<font="Courier">
    <b><h2>Today's Pipeline Run:</h2></b>
    <br />
    Began %s <br />
    Completed %s<br />
    Unique images processed: %s<br />
    Unique stars logged: %s<br />
    Stars not matched to catalog (avg): %s<br /><br />

    """ % (start_time,end_time,images_processed,stars_logged,stars_not_matched)
    
    # same thing but without HTML
    printing = """Today's Pipeline Run:\n
    Began %s 
    Completed %s
    Unique images processed: %s
    Unique stars logged: %s
    Stars not matched to catalog (avg): %s
    """ % (start_time,end_time,images_processed,stars_logged,stars_not_matched)

    body += "Here are the log entries for today's run:\n<p style='font-size:8pt;'>"

    # include summary of error log for today
    filename = "errorlog.txt"
    with open(filename,'rb') as attachment:    
        for line in attachment:
            log_time = datetime.strptime(str(line[0:20]),"%Y-%m-%d %H:%M GMT")
            if log_time >= datetime.strptime(start_time,'%Y-%m-%d %H:%M GMT') and log_time <= datetime.strptime(end_time,"%Y-%m-%d %H:%M GMT"):
                body += line.strip()+'<br />'

    body += '\n</p>Attached is the full error log</font>'
    msg.attach(MIMEText(body, 'html'))
        
    # attach full error log
    with open(filename,'rb') as attachment:    
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)
    text = msg.as_string()

    # open recipient file
    with open('email_recipients.txt','r') as f:
        recipients = f.read().splitlines()

    # make string for recipients for printing it out
    all_recipients = recipients[0]
    for x in range(1,len(recipients)):
        all_recipients += ', '+recipients[x]
    print('Sending message to %s\n' % all_recipients)
    sleep(1)
    print(printing)
    
    # for each recipient, send message
    for recipient in recipients:
        msg['To'] = recipient
        s.sendmail(address, recipient, text)

    # quit SMTP server
    s.quit()



#####################################################################################################################################################
### define housekeeping functions for printing the output
#####################################################################################################################################################

def prnt(indent,strng,filename=False,alert=False):
    '''
    Internal function.
    Prints the ouput of the pipeline in a consistent way, using the length of the indent variable as the indent for the line and printing the strng variable. 
    If filename = True, it will print the filename as the indent. If alert = True it will put exclamation points in the line. 
    '''

    if alert:
        if slow:
            if not filename:
                print(' '*(len(indent)-2)+'!!! '+strng)
                sleep(0.3)
            else: 
                print(indent+': '+strng)
                sleep(0.3)
        else:
            if not filename:
                print(' '*(len(indent)-2)+'!!! '+strng)
            else: 
                print(indent+': '+strng)
    else:
        if slow:
            if not filename:
                print(' '*len(indent+': ')+strng)
                sleep(0.3)
            else: 
                print(indent+': '+strng)
                sleep(0.3)
        else:
            if not filename:
                print(' '*len(indent+': ')+strng)
            else: 
                print(indent+': '+strng)


def header(i,count=False):
    '''
    Internal function.
    Prints a header at the top of the screen that shows what process is going on
    Takes a count argument to show a counter of images processed and how many total
    '''

    print('\033c')
    if not count:
        print('-'*int((termsize-len(i)-2)/2)+' '+i+' '+'-'*int((termsize-len(i)-2)/2))
        print('')
    else:
        i = i+' '+str(count[0])+'/'+str(count[1])
        print('-'*int((termsize-len(i)-2)/2)+' '+i+' '+'-'*int((termsize-len(i)-2)/2))
        print('')



#####################################################################################################################################################
### function to write error to error log
#####################################################################################################################################################

def writeError(description):
    '''Writes description to errorlog.txt'''
    name = 'errorlog.txt'
    if not os.path.exists(name): # if the file doesn't exist,
        with open(name,'w') as erlog: # create it
            pass

    with open(name,'a') as erlog: # with the file open
        time = strftime("%Y-%m-%d %H:%M GMT", gmtime()) # define time
        description = time+': '+description+'\n' # add time to description
        erlog.write(description) # write desciption 



#####################################################################################################################################################
### daily image copying
#####################################################################################################################################################

def dailyCopy(writeOver=False):
    ''' 
    Copies files from dome computer to linus computer i.e. D:\Calibration\ ==> /data1/ArchCal and D:\SkyImages\ ==> /data1/ArchSky.
    Takes argument writeOver to determine whether files are overwritten if ArchSky/[date] or ArchCal/[date] already exists.
    '''
    
    header('Copying Files')
    
    # define paths
    copys = ['Calibration/','SkyImages/']
    archives = ['ArchCal/','ArchSky/']

    # copy each directory in a loop (only 2 iterations since only 2 directories)
    for i in range(2):
        print('\tCopying from %s ' % copys[i])
        sleep(1.5)
        
        # index the dates and find which match our days_old criteria
        all_dates = [f for f in os.listdir(copys[i]) if not f.startswith('.') and not os.path.isfile(f)] # all dates found in the Windows folder
        recent_dates = [datetime.strftime(datetime.utcnow()-timedelta(days=j),'%Y%m%d') for j in range(1,days_old+1)] # date names we are looking for based on days_old
        dates = list(set(all_dates) & set(recent_dates)) # combination of the two shows which match
        
        # string math for printing
        recent_dates_str = ''
        for x in recent_dates:
            recent_dates_str += x+' '
        
        dates_str = ''
        for x in dates:
            dates_str += x+' '

        # if no dates found
        if dates_str.strip()=='':
            print('\tNo directories in %s matched %s\n' % (copys[i],recent_dates_str))
            sleep(1) 
            continue # skip to next day in loop
        else:
            print('\tLooking for dates %s found %s in %s' % (recent_dates_str,dates_str,copys[i]))
        
        sleep(2)
        dates_src = [copys[i]+date+'/' for date in dates] # paths for directories to copy
        dates_dst = [archives[i]+date+'/' for date in dates] # paths for directories to copy *to*

        # loop through each directory and copy the files
        for j in range(len(dates_src)):
            print('\tAttempting copy of %s' % dates_src[j])
            writeError('     in dailyCopy: Attempting copy of %s' % dates_src[j])
            sleep(2)
            try:
                shutil.copytree(dates_src[j],dates_dst[j]) # copy files from source to destination
            except: # if encounter an error
                if writeOver: # if you want to overwrite 
                    if os.path.exists(dates_dst[j]): # then delete the file 
                        shutil.rmtree(dates_dst[j])
                        shutil.copytree(dates_src[j], dates_dst[j]) # and try to copy again
                    print('\tDirectory %s already exists, overwriting' % dates_dst[j]) 
                    sleep(3)
                    writeError('     in dailyCopy: Directory %s already exists, overwritten' % dates_dst[j]) 
                else: # if you dont want to overwrite 
                    print('\tDirectory %s already exists, skipping' % dates_dst[j]) # skip it
                    sleep(3)
                    writeError('     in dailyCopy: Directory %s already exists, skipped copying' % dates_dst[j])
                    continue # skip to  next day
            else: # if you don't encounter an error
                print('\tCopied directory %s to %s' % (dates_src[j],dates_dst[j]))
                sleep(3)
                writeError('     in dailyCopy: copied dir %s to %s' % (dates_src[j],dates_dst[j]))
            sleep(2)
            print('\tComplete')
            sleep(2)
            print('')


#####################################################################################################################################################
### make master calibration files
#####################################################################################################################################################

def makeMasters(directory=str,inPipeline=False,writeOver=False):
    '''
    Index calibration files and generate masters. 
    Searches for calibration files in the most recent date directory under 'ArchCal/'. 
    For example, makeMasters() will search 'ArchCal/20180701/' if that is the most recent date directory available.
    Opt. argument directory can be changed to specify a directory other than 'ArchCal/'.
    If inPipeline=False, will not look for specific date folders but will rather just search the directory argument
    Opt. argument writeOver=False can be changed to True to allow older bias & dark frames to be over written by more recent ones.
    '''
    # index folders of calibration files
    if inPipeline:
        dates = [datetime.strftime(datetime.utcnow()-timedelta(days=j),'%Y%m%d') for j in range(1,days_old+1)]
        dates = ['ArchCal/'+date+'/' for date in dates]
    else:
        dates = np.array([directory])

    # loop through each date path and make masters
    for path_to_cal in dates:
        header('Making Masters')

        # if you cannot find date path, skip day
        if not os.path.exists(path_to_cal):
            sleep(1.5)
            print('\tNo calibration date folder found %s' % path_to_cal)
            sleep(3)
            print('\tSkipping makeMasters for this date...')
            writeError('     in makeMasters: No path found at %s, skipped makeMasters for this date' % path_to_cal)
            sleep(3)
            continue

        # search filenames in date path
        filenames = [f for f in os.listdir(path_to_cal) if os.path.isfile(os.path.join(path_to_cal,f)) if not f.startswith('.')] # list of filenames to process

        # if no files in that date folder, skip the day 
        if len(filenames)==0:
            sleep(1.5)
            print('\tNo images in %s' % path_to_cal)
            sleep(3)
            print('\tSkipping makeMasters for this date')
            sleep(3)
            writeError('     in makeMasters: No images in %s, skipped makeMasters' % path_to_cal)
            continue

        #####################################################################################################################################################
        ### search and sort calibration files

        print('\tSearching %s for calibraton files...' % path_to_cal)
        print('\tIndexed %s files' % len(filenames))
        
        # lists are used to store the filename for each calibration file and then combine into a master
        binnings = ['1','2','3','4']
        for j in binnings: # initialize lists
            exec("bias"+j+",dark"+j+",Red"+j+",Green"+j+",Blue"+j+",R"+j+",V"+j+",B"+j+",Halpha"+j+",Lum"+j+",filters"+j+" = [],[],[],[],[],[],[],[],[],[],[]") 

        print('\tSorting files...')

        # sort the calibration filenames by type and store them in the lists
        for filename in filenames: # for each filename
            with fits.open(path_to_cal+filename) as hdulist: 
                hdr = hdulist[0].header # get the fits header
                typ = hdr['IMAGETYP'] # save image type as variable
                binn = str(hdr['XBINNING']) # save binning as variable
                if typ=='Bias Frame':
                    exec('bias'+binn+'_header=hdr') # save the header to write back into the master
                    exec('bias'+binn+'.append(filename)') # add the data to the list with respective type/binning
                if typ=='Dark Frame':
                    exec('dark'+binn+'_header=hdr')
                    exec('dark'+binn+'.append(filename)')
                if typ=='Flat Field':
                    exec(hdr['FILTER']+binn+'_header=hdr')
                    exec('filters'+binn+".append(hdr['FILTER'])") # store the filters found in this directory in a list
                    # so that we don't attempt to create new master flats with filters we did not have raw flats for
                    exec(hdr['FILTER']+binn+'.append(filename)') 

        # print what was detected
        print('')
        print('\tIndexed files:        Binning1x1  Binning2x2  Binning3x3  Binning4x4')
        print('\t\tBias:             %s          %s          %s          %s' % (len(bias1),len(bias2),len(bias3),len(bias4)))
        print('\t\tDark:             %s          %s          %s          %s' % (len(dark1),len(dark2),len(dark3),len(dark4)))
        print('\t\tRed Flat:         %s          %s          %s          %s' % (len(Red1),len(Red2),len(Red3),len(Red4)))
        print('\t\tGreen Flat:       %s          %s          %s          %s' % (len(Green1),len(Green2),len(Green3),len(Green4)))
        print('\t\tBlue Flat:        %s          %s          %s          %s' % (len(Blue1),len(Blue2),len(Blue3),len(Blue4)))
        print('\t\tR Flat:           %s          %s          %s          %s' % (len(R1),len(R2),len(R3),len(R4)))
        print('\t\tV Flat:           %s          %s          %s          %s' % (len(V1),len(V2),len(V3),len(V4)))
        print('\t\tB Flat:           %s          %s          %s          %s' % (len(B1),len(B2),len(B3),len(B4)))
        print('\t\tHalpha Flat:      %s          %s          %s          %s' % (len(Halpha1),len(Halpha2),len(Halpha3),len(Halpha4)))
        print('\t\tLum Flat:         %s          %s          %s          %s' % (len(Lum1),len(Lum2),len(Lum3),len(Lum4)))
        print('')

        
        #####################################################################################################################################################
        ### make master calibration files
        
        for i in binnings: 
            exec('s=np.size(bias'+i+')') # define var s as the size of the list
            if not s==0: # if the size is nonzero, there is data for that type & binning
                exec('filenames = bias'+i)
                master = []
                for filename in filenames: # for each filename
                    with fits.open(path_to_cal+filename) as hdulist:
                        img = hdulist[0].data
                        master.append(img) # add the image data to the master list
                exec('bias'+i+'_master=np.median(np.array(master),axis=0)') # define bias master as the median of each fame
                print('\tConstructed a master bias with binning %sx%s' % (i,i)) 

        for i in binnings:
            exec('s=np.size(dark'+i+')') 
            if not s==0:
                try: # try to  make dark master
                    exec('filenames = dark'+i)
                    master = []
                    for filename in filenames:
                        with fits.open(path_to_cal+filename) as hdulist:
                            img = hdulist[0].data
                            master.append(img)
                    exec('dark'+i+'_master=np.median(np.array(master)-bias'+i+'_master,axis=0)') # define the dark amster as the median of each frame with the bias already removed
                    print('\tConstructed a scalable master dark with binning %sx%s' % (i,i))
                except NameError: # you get a NameError if it cannot find the bias master variable
                    print('\tNo bias master for binning %sx%s, failed to create scalable dark. Wrote to DR_errorlog.txt' % (i,i)) # can't make the master dark without a bias
                    writeError('     in makeMasters: No bias master for binning %sx%s, failed to create dark' % (i,i))

        for j in binnings: 
            exec("dxptime=dark"+str(binn)+"_header['EXPTIME']")
            exec('f=np.unique(filters'+j+')') # establish unique filters 
            for i in f: # for each UNIQUE filter
                exec('s=np.size('+i+j+')')
                if not s==0: 
                    exec('filenames = '+i+j)
                    exec("fxptime = "+i+j+"_header['EXPTIME']")
                    master = []
                    for filename in filenames:
                        with fits.open(path_to_cal+filename) as hdulist:
                            img = hdulist[0].data
                            master.append(img)
                    master = np.array(master)
                    exec("master = master - bias"+j+"_master") # subtract the bias from each flat frame
                    exec("master = master - dark"+j+"_master * fxptime / dxptime") # subtract the dark from each flat frame
                    exec(i+j+"_master = np.median(master,axis=0)/np.max(np.median(master,axis=0))")  # define the flat field as the median of each frame normalized to the maximum
                    print('\tConstructed master %s flat with binning %sx%s' % (i,j,j))
        

        #####################################################################################################################################################
        ### write the masters to fits files

        for i in binnings:
            for j in ['bias','dark']: 
                if j+i+'_master' in locals(): # if the local variable is defined
                    try:
                        code = "fits.writeto('MasterCal/binning"+i+'/'+j+"_master.fit',"+j+i+'_master, header='+j+i+'_header,overwrite='+str(writeOver)+')' # write to MasterCal/binningi
                        exec(code)
                        print('\tWrote master %s to file MasterCal/binning%s/%s_master.fit' % (j,i,j))   
                    except:
                        print('\tBias or dark master already exists, no new file written')

        for i in binnings:
            exec('f=np.unique(filters'+i+')') 
            for j in f: # for each unique filter
                try:
                    code = "fits.writeto('MasterCal/binning"+i+'/'+"flat_master_"+j+".fit',"+j+i+"_master,header="+j+i+"_header,overwrite="+str(writeOver)+")"
                    exec(code)   
                    print('\tWrote master %s flat to file MasterCal/binning%s/flat_master_%s.fit' % (j,i,j))
                except:
                    print('\t%s Flat master already exists, no new file written' % j)
        
        print('\n\tComplete')
        sleep(3)
        print('\033c')




#####################################################################################################################################################
### per image operations contained withing Field object
#####################################################################################################################################################

class Field:
    def __init__(self):
        # when a Field object is created, define some variables
        # these variables can be changed from pipeline.py after defining the field object
        self.calibrated_path = 'Calibrated Images/' # path where calibrated images are saved
        self.uncalibrated_path = 'ArchSky/' # path where uncalibrated images are found
        self.path_to_masters = 'MasterCal/' # path where masters are found
        self.max_temp = -3.0 # maximum temp for calibration
        self.isCalibrated = False # variable defining whether the image is calibrated yet
        self.aperture_size = 30.0 # aperture size for photometry
        self.cutoff = True # cutoff outliers from annulus for photometry 
        self.counter = 0 # counter for how many images we have processed in this run 
    
    #####################################################################################################################################################
    ### open a fits file 
    #####################################################################################################################################################
    
    def openFits(self,filename,calibrated=False,inPipeline=False):
        self.filename = filename
        if not inPipeline: # portable functionality if we aren't running this command from inside the pipeline
            self.uncalibrated_path = '' 
            self.calibrated_path = ''
        if not calibrated: # if it hasnt been calibrated we need the uncalibrated path 
            with fits.open(self.uncalibrated_path+self.filename) as hdulist:
                self.hdr = hdulist[0].header
                img = hdulist[0].data
                self.img = np.array(img,dtype='<f4') # change dtype because of SourceExtractor (sep) 
        else: # otherwise we need the calibrated path
            with fits.open(self.calibrated_path+self.filename.replace('.fits','_calibrated.fits')) as hdulist:
                self.hdr = hdulist[0].header
                img = hdulist[0].data
                self.img = np.array(img,dtype='<f4')

    
    #####################################################################################################################################################
    ### save fits files after calibration
    #####################################################################################################################################################

    def saveFits(self,h,data,filename,inPipeline=True): 
        if inPipeline:
            if not os.path.exists(self.calibrated_path): 
                os.makedirs(self.calibrated_path) # make a directory if there isnt one
        else:
            self.calibrated_path = ''
        fits.writeto(self.calibrated_path+filename.replace(".fit","_calibrated.fit"),data,h,overwrite=True)
        prnt(self.filename,'Wrote file to '+self.calibrated_path)
        print(' ')
        self.isCalibrated = True # now its calibrated so we change this variable to True
    

    #####################################################################################################################################################
    ### for writingErrors to the error log (different than the function before because this includes filename)
    #####################################################################################################################################################
    
    def writeError(self,description):
        name = 'errorlog.txt'
        if not os.path.exists(name):
            with open(name,'w') as erlog:
                pass
        with open(name,'a') as erlog:
            time = strftime("%Y-%m-%d %H:%M GMT", gmtime())
            description = time+':      '+self.filename+': '+description.strip()+'\n'
            erlog.write(description)


    #####################################################################################################################################################
    ### check if image needs to be calibrated
    #####################################################################################################################################################

    def checkCalibration(self,h,image): # check to see whether or not we need to calibrate the file
        if np.size(image)==8487264 or np.size(image)==2121816 or np.size(image)==942748: # sizes for our three binning factors that we will use
            if h['CCD-TEMP']<=self.max_temp: 
                if h.get('CALSTAT',default=0)==0: 
                    return True # True means we calibrate
                if h.get('CALSTAT',default=0)=='BDF' or h.get('CALSTAT',default=0)=='DF':
                    return 'Redundant' # Redundant calibration
                if h.get('CALSTAT',default=0)=='D':
                    return 'OnlyDark' # already had an auto dark
            else:
                return 'Temp'    
        else:
            return 'Size'


    #####################################################################################################################################################
    ### write calibration to the header
    #####################################################################################################################################################

    def writeToHeader(self,h,dark=False,flat=False,bias=False):
        if h.get('CALSTAT',default=0)==0: # if there is no calstat field in the header
            h.append(('CALSTAT','BDF','Status of Calibration')) # add one
        else:
            h['CALSTAT']='BDF' # otherwise set the value of calstat to BDF
        
        for x in [dark,flat,bias]:
            if not x:
                pass
            else:
                h.append(('HISTORY','GC data pipeline correction with %s' % x,strftime("%Y-%m-%d %H:%M GMT", gmtime())))


    #####################################################################################################################################################
    ### initialize the pipeline process by indexing the files to be processed
    #####################################################################################################################################################

    def Initialize(self,day):
        '''Index the files we need to calibrate -- must be run before other methods such as Reduce(), Extract(), etc.'''

        self.calibrated_path = 'Calibrated Images/'
        self.uncalibrated_path = 'ArchSky/'

        header('Initialization') # print the header
        self.columnsWritten = True # if we need to write the columns into the sources.csv file
        
        # index dates according to days old
        dates = [datetime.strftime(datetime.utcnow()-timedelta(days=j),'%Y%m%d') for j in range(1,days_old+1)]
        self.uncalibrated_path = [self.uncalibrated_path+date+'/' for date in dates][day]
        self.calibrated_path = [self.calibrated_path+date+'/' for date in dates][day]

        # if no path for uncalibrated images, exit
        if not os.path.exists(self.uncalibrated_path):
            print('\tNo images found in %s' % self.uncalibrated_path)
            sleep(1)
            print('\tSkipping...')
            sleep(1.5)
            print("\033c")
            writeError('     in Initialize: Path %s does not exist, skipping pipeline run for this day' % self.uncalibrated_path)
            return False

        # if no path for calibrated images, make one
        if not os.path.exists(self.calibrated_path):
            os.makedirs(self.calibrated_path)

        # get list of files 
        self.list_of_files = [f.strip() for f in os.listdir(self.uncalibrated_path) if  not f.startswith('.') and os.path.isfile(os.path.join(self.uncalibrated_path,f)) and f.endswith('.fits') or f.endswith('.fit')]

        print('\tSearching %s for sky images...' % self.uncalibrated_path)
        sleep(1)
        print('\tSearching %s for calibration files...' % self.path_to_masters)
        sleep(1)
        print('\033c')
        return True


    #####################################################################################################################################################
    ### perform data reduction 
    #####################################################################################################################################################

    def Reduce(self,inPipeline=False):
        '''
        Perform data reduction on the images with filenames generated in Initialize()
        Takes optional argument inPipeline to facilitate running the function on images outside of the pipeline structure.
        '''
        self.isCalibrated = False # reset this variable for new images

        if inPipeline:
            header('Calibration & Source Extraction',count=(self.counter,len(self.list_of_files)))
        
        light_h,light = self.hdr,self.img # bring up the hdr and image
        prnt(self.filename,'Successfully opened %s image in %s' % (light_h['FILTER'],self.uncalibrated_path),filename=True)
        self.path_to_masters = 'MasterCal/binning%s/' % str(light_h['XBINNING']) # search for calibration files in binning-specific folder

        # get filter and store variable whether it is narrow band, since we don't want to do source detection later if it isnt
        filt = light_h['FILTER']
        if filt=='V' or filt=='R' or filt=='B':
            self.narrowBand = True
        else:
            self.narrowBand = False


        #####################################################################################################################################################
        ### open the bias master

        bias_filename = self.path_to_masters+'bias_master.fit'
        try: 
            bias_fits = fits.open(bias_filename) 
            prnt(self.filename,'Successfully opened bias master %s' % bias_filename)
        except: # if you encounter error
            prnt(self.filename,'Failed to open bias master %s' % bias_filename)
            sleep(2)
            self.writeError('     in Reduce: Missing bias master %s. Data reduction halted' % bias_filename)
            return # exit the program since you can't calibrate files without a bias frame

        bias_h = bias_fits[0].header # split into header and data
        bias = bias_fits[0].data


        #####################################################################################################################################################
        ### open the dark master

        dark_filename = self.path_to_masters+'dark_master.fit'
        try:
            dark_fits = fits.open(dark_filename) 
            prnt(self.filename,'Successfully opened dark master %s' % dark_filename)
        except:
            prnt(self.filename,'Failed to open dark master %s' % dark_filename)
            sleep(2)
            self.writeError('     in Reduce: Missing dark master %s. Data reduction halted' % dark_filename)
            return

        dark_h = dark_fits[0].header
        dark = dark_fits[0].data
        
        dxptime = dark_h['EXPTIME'] # store the exposure time for the dark master for scaling purposes
        exptime = light_h['EXPTIME'] # store light image exposure time

        #####################################################################################################################################################
        ### open filter-specific flat field

        flat_filename = self.path_to_masters+'flat_master_'+light_h['FILTER']+'.fit'
        try: 
            flat_fits = fits.open(flat_filename) 
            prnt(self.filename,'Successfully opened '+flat_filename)
        except:
            prnt(self.filename,'Failed to open flat master %s' % flat_filename)
            sleep(2)
            self.writeError('     in Reduce: Missing %s flat master in %s. Data reduction halted' % (light_h['FILTER'],self.path_to_masters))
            return
        
        flat_h = flat_fits[0].header
        flat = flat_fits[0].data


        #####################################################################################################################################################
        ### perform the actual data reduction

        # if we need to calibrate the image
        if self.checkCalibration(light_h,light)==True: 
            prnt(self.filename,'Calibrating image...' )

            bias_corrected_image = light - bias # subtract the bias
            dark_corrected_image = bias_corrected_image - (exptime/dxptime) * dark # scale the dark linearly w/ exptime and subtract
            final_image = dark_corrected_image / flat # divide by the flat field (already normalized)
            
            self.writeToHeader(light_h,flat=flat_filename,bias=bias_filename,dark=dark_filename)
            self.saveFits(light_h, final_image,self.filename,inPipeline=inPipeline)

        # if we only had an auto dark
        elif self.checkCalibration(light_h,light)=='OnlyDark': 
            prnt(self.filename,'Calibrating image...' )
            
            bias_corrected_image = light - bias
            final_image = bias_corrected_image / flat 

            self.writeToHeader(light_h,bias=bias_filename,flat=flat_filename)
            self.saveFits(light_h, final_image,self.filename,inPipeline=inPipeline)

        # if it was already calibrated
        elif self.checkCalibration(light_h,light)=='Redundant': 
            self.writeError('     in Reduce: Attempted redundant calibration')
            prnt(self.filename,'Image already calibrated')
            self.saveFits(light_h, light,self.filename,inPipeline=inPipeline) # still save the file because we can still use it

        # if its temperature is too high
        elif self.checkCalibration(light_h,light)=='Temp': 
            self.writeError('     in Reduce: Rejected calibration, taken at %s degrees C' % light_h['CCD-TEMP'])
            prnt(self.filename,'Image taken at > '+str(self.max_temp)+' degrees C')
            sleep(4)
        
        # if the size is incorrect, either because we used a subframe or because we were binning at something either than 1x1, 2x2, or 3x3
        elif self.checkCalibration(light_h,light)=='Size':
            self.writeError('     in Reduce: Rejected calibration, captured with subframe or non-standard binning')
            prnt(self.filename,'Rejected calibration, captured with subframe or non-standard binning')
            sleep(4)
        
        # close the images
        del self.hdr,self.img
        del flat_fits,bias_fits,dark_fits


    #####################################################################################################################################################
    ### detect sources
    #####################################################################################################################################################

    def Source(self):
        hdr,img = self.hdr,self.img

        bkg = sep.Background(img)
        bkg_data = bkg.back()
        bkg_rms = bkg.rms()

        img = img - bkg_data
        objects = sep.extract(img, 4, err=bkg_rms,minarea=120/hdr['XBINNING']/hdr['YBINNING'])
        prnt(self.filename,'Source detection complete with %s objects' % str(len(objects)))
        return objects


    def Convert(self): # converts obj list in pixel coordinate to RA-dec coordinates
        hdr = self.hdr
        try:
            test = hdr['WCSVER']
        except KeyError:
            return 'NOWCS'
        
        w = wcs.WCS(hdr) # gets WCS matrix from the header
        coords = zip(self.source['x'],self.source['y'])
        world = w.wcs_pix2world(coords, 1) # World Coorindate System function converts matrix in fits header to RA/Dec
        prnt(self.filename,'Converted source coordinates from pixel to world')
        return world


    def Photometry(self): 
        hdr,img = self.hdr,self.img
        egain = float(hdr['EGAIN'])

        #####################################################################################################################################################
        ### perform aperture photometry
        #####################################################################################################################################################
        
        prnt(self.filename,'Performing aperture photometry...')

        indices_to_remove,objects_to_remove = [],[]
        fluxes,fluxerrs = [],[]

        aperture_size = float(self.aperture_size) / float(hdr['XBINNING'])

        for i in range(len(self.source)):
            r_in = 1.5*aperture_size
            r_out = 2.0*aperture_size            
            
            ## manually measure annulus values
            annulus_values = []
            for dx in range(-int(r_out),int(r_out)):
                for dy in range(-int(r_out),int(r_out)):
                    if np.sqrt(dx*dx+dy*dy)>r_in and np.sqrt(dx*dx+dy*dy)<r_out:
                        x_index = int(self.source['x'][i]+dx)
                        y_index = int(self.source['y'][i]+dy)
                        try:
                            annulus_values.append(img[y_index,x_index])
                        except IndexError:
                            pass
            
            ## cutoff outliers from the annulus
            if self.cutoff:
                for j in range(3): # iteratively remove outliers
                    std = np.std(annulus_values)
                    mean = np.mean(annulus_values)
                    annulus_values = [a for a in annulus_values if a<=mean+3*std] # if outliers are above 3 std deviations 
            
            bkg_mean = np.mean(annulus_values) 
            img_temp = img - bkg_mean # create temporary image with bkg removed from each pixel

            flux, fluxerr, flag = sep.sum_circle(img_temp, self.source['x'][i], self.source['y'][i], aperture_size,gain=egain,subpix=0)

            ## check for error flags
            if not flag==0:
                if flag==16:
                    prnt(self.filename,'SEP flag #%s, incomplete aperture data, star discarded' % str(flag),alert=True)
                    if verbose_errors:
                        self.writeError('     in Photometry: Source Extractor flag #%s, star discarded from aperture photometry' % str(flag))
                    indices_to_remove.append(i)
                else:
                    prnt(self.filename,'SEP flag #%s' % str(flag),alert=True)
                    if verbose_errors:
                        writeError('     in Photometry: Source Extractor flag #%s' % str(flag))

            fluxes.append(flux)
            fluxerrs.append(fluxerr)


        flux = np.array(fluxes)
        ## check for negative values
        for j in range(len(flux)):
            if flux[j]<0:
                prnt(self.filename,'Negative flux at pixel position (%s,%s), star discarded' % (self.source['x'][j],self.source['y'][j]),alert=True)
                if verbose_errors:
                    self.writeError('     in Photometry: Calculated negative flux at pixel position (%s,%s), star discarded' % (self.source['x'][j],self.source['y'][j]))
                indices_to_remove.append(j)

        ## remove any objects flagged for removal 
        flux = np.delete(flux, (indices_to_remove), axis=0)
        indices_to_remove = np.append(indices_to_remove,objects_to_remove)
        objects = np.delete(self.world, (indices_to_remove), axis=0)

        imags = -2.5*np.log10(flux) # convert flux to instrumental magnitude
        imags_err= 1/np.array(fluxerrs) # includes Poisson noise

        prnt(self.filename, 'Completed aperture photometry, result %s inst. magnitudes' % len(flux))
        print('')
        prnt(self.filename, 'Preparing to match %s objects to catalog...' % len(objects))

        ## check to make sure we have the same number of objects as we have fluxes
        if not len(flux)==len(objects):
            self.writeError('     fatal error in Photometry: Number objects and fluxes do not match, resulting data is unreliable. System quit')
            exception = 'in image %s: Number objects to match to catalog and number and fluxes calculated do not match, resulting data not reliable' % self.filename
            sendError(exception)
            raise Exception(exception)




        #####################################################################################################################################################
        ### query catalog
        #####################################################################################################################################################
        
        v = Vizier(columns=['UCAC4','+_r','RAJ2000','DEJ2000','Bmag','Vmag','rmag']) # lookup data in the UCAC4 catalog by querying Vizier        

        time = hdr['DATE-OBS'] # time image was taken
        time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f') # convert string to datetime object
        filt = hdr['FILTER'] # filter of image
        output = OrderedDict([('id',[]),('RA_C',[]),('DEC_C',[]),('RA_M',[]),('DEC_M',[]),('DIF',[]),('MAG_R',[]),('MAG_V',[]),('MAG_B',[]),('MAG_err',[]),('CMAG_R',[]),('CMAG_V',[]),('CMAG_B',[]),('DATETIME',[]),('IMGNAME',[]),('RUNTIME',[])])
        
        
        cmags = [] # catalog magnitudes list we will update in the loop
        misfires = 0 # number of errors 
        objects_indices_matched = [] # will store the indices in the objects list of the ones we match to the catalog, so that we only use those stars to calculate offset

        for n in range(len(objects)): # for each star
            catalog = 'UCAC4'             
            # submit query at object coordinates with a radius of 2 arcseconds
            result = v.query_region(coord.SkyCoord(ra=objects[n,0], dec=objects[n,1],
            unit=(u.degree, u.degree), frame='fk5'),radius='3s',catalog=catalog) 
            
            try:
                result = result[0] # try to get the first result from the list of results (which is usually just 1 element)
            except:
                prnt(self.filename,'No star match within 3 arcseconds')
                misfires += 1 
                # manually fill in the data with mostly nan values 
                output['id'].append('nan')
                output['RA_C'].append('nan')
                output['DEC_C'].append('nan')
                output['RA_M'].append(objects[n,0])
                output['DEC_M'].append(objects[n,1])
                output['DIF'].append('nan')
                output['DATETIME'].append(time)
                output['IMGNAME'].append(self.filename)
                output['RUNTIME'].append(strftime("%Y-%m-%d %H:%M GMT", gmtime()))
                cmags.append('nan') 
                continue # skip to the next object by moving to the next iteration of the loop

            fluxtype = filt+'mag' # get a variable for fluxtype to match to catalog magnitude types
            if filt=='R':
                fluxtype = 'rmag'

            ## get results from query
            i = np.array(result['UCAC4'],str)[0] # get array of all the stars identified
            mag = np.array(result[fluxtype],float)[0] # store the filter catalog magnitude for the stars matched
            ra = np.array(result['RAJ2000'],float)[0] # get array of catalog RA for those stasr
            dec = np.array(result['DEJ2000'],float)[0] # catalog Dec for those stars
            dif = np.array(result['_r'],float)[0] # difference from target

            ## write results if not already written
            if i not in output['id']:
                prnt(self.filename,'Star match in %s, mag %s, residual %s arcsec' % (catalog,mag,dif))
                output['id'].append(i)
                output['RA_C'].append(ra)
                output['DEC_C'].append(dec)
                output['RA_M'].append(objects[n,0])
                output['DEC_M'].append(objects[n,1])
                output['DIF'].append(dif)
                output['DATETIME'].append(time)
                output['IMGNAME'].append(self.filename)
                output['RUNTIME'].append(strftime("%Y-%m-%d %H:%M GMT", gmtime()))
                cmags.append(mag)
                if not math.isnan(mag):
                    objects_indices_matched.append(n)
            else:
                prnt(self.filename,'Star already matched')
                misfires += 1 
                # manually fill in the data with mostly nan (not a number) values 
                output['id'].append('nan')
                output['RA_C'].append('nan')
                output['DEC_C'].append('nan')
                output['RA_M'].append(objects[n,0])
                output['DEC_M'].append(objects[n,1])
                output['DIF'].append('nan')
                output['DATETIME'].append(time)
                output['IMGNAME'].append(self.filename)
                output['RUNTIME'].append(strftime("%Y-%m-%d %H:%M GMT", gmtime()))
                cmags.append('nan') 
                continue # skip to the next object by moving to the next iteration of the loop

        prnt(self.filename,'Output %s stars' % len(set([v for v in output['id'] if v!='nan'])))
        prnt(self.filename,'Missed %s objects' % misfires)    



        #####################################################################################################################################################
        ### zero point / offset calculation
        #####################################################################################################################################################


        ## we only want to use these instrumental magnitudes to calculate the offset since we have catalog mags for them
        imags_cal = [imags[m] for m in objects_indices_matched] 
        cmags_cal = [m for m in cmags if not math.isnan(float(m))]
        
        ## check to make sure that we are comparing mags of the same stars
        if not len(imags_cal)==len(cmags_cal): 
            self.writeError('     fatal error in Photometry: Catalog comparison list not same length as instrumental magnitude list. System quit')
            exception = 'in image %s: catalog comparison list not same length as instrumental magnitude list, resulting calibrated magnitudes unreliable' % self.filename
            sendError(exception)
            raise Exception(exception)

        prnt(self.filename,'Using %s stars in offset calculation' % len(imags_cal))
        
        zero_point = np.array(cmags_cal) - np.array(imags_cal) # calculate the differences for each star
        for j in range(3): # iteratively remove outliers
            std = np.std(zero_point)
            mean = np.mean(zero_point)
            zero_point = [a for a in zero_point if a<=mean+3*std] # if outliers are above 3 std deviations 
        
        zero_point_err = np.std(zero_point)/np.sqrt(len(zero_point))
        zero_point = float(np.median(zero_point)) # take the MEDIAN of the difference - median does not consider outliers so a single variable star in the mix won't mess up our constant offset

        mags = imags+zero_point
        mags_err = np.sqrt(imags_err*imags_err+zero_point_err*zero_point_err)

        prnt(self.filename,'Completed offset calculation, mean mag for %s stars in field %s' % (len(mags),np.mean([x for x in mags if not math.isnan(x)])))
        

        ## write calibrated mags to output dict
        output['MAG_err'] = mags_err # go ahead and write the errors into the output dict
        for i in ['R','V','B']: # for each filter
            magtype = 'MAG_'+i 
            if i==filt: # if that is the filter the image used
                output[magtype] = mags # set the output array as the intrumental magnitudes + the constant offset
            else:
                output[magtype] = np.full(np.shape(imags),'---',dtype="S3") # otherwise fill with null values

        for i in ['R','V','B']: # same thing
            magtype = 'CMAG_'+i 
            if i==filt:
                output[magtype] = cmags # set the output as the catalog magnitudes
            else:
                output[magtype] = np.full(np.shape(cmags),'---',dtype="S3") # otherwise fill with null values

        prnt(self.filename,'Wrote magnitude data to sources.csv') 
        print(' ')
        sleep(4)
        
        return output

    def Plot(self):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Ellipse
        import matplotlib
        
        hdr, img = self.hdr, self.img
        proj = wcs.WCS(hdr)
        fig = plt.figure(figsize=(13,10)) 
        ax = fig.add_subplot(111,projection=proj)
        m, s = np.mean(img), np.std(img)
        im = ax.imshow(img, interpolation='nearest', cmap='gray',
                    vmin=m-s, vmax=m+s, origin='lower')

        overlay = ax.get_coords_overlay('fk5')
        overlay.grid(color='white', ls='dotted')
        overlay[0].set_axislabel('Right Ascension (J2000)')
        overlay[1].set_axislabel('Declination (J2000)')

        # plot an ellipse for each object
        for i in range(len(self.source['x'])):
            e = Ellipse(xy=(self.source['x'][i], self.source['y'][i]),
                        width=6*self.source['a'][i],
                        height=6*self.source['b'][i],
                        angle=self.source['theta'][i])
            e.set_facecolor('none')
            e.set_edgecolor('red')
            ax.add_artist(e)
        name = self.filename.replace('Calibrated Images/','plots/')
        name = name.replace('.fits','.jpg')
        plt.savefig(name)
        print('    Created plot of %s' % self.filename)



    def writeData(self):
        with open('sources.csv', 'a') as outfile:
            writer = csv.writer(outfile)
            if self.columnsWritten==False:
                writer.writerow(self.output.keys())
                self.columnsWritten = True
            writer.writerows(zip(*self.output.values()))
        self.writeError('     Wrote %s data points from image' % str(len(self.output['id'])))
        print('\033c')
   
    def Extract(self):
        self.source = self.Source()
        self.world = self.Convert()
        if self.world =='NOWCS':
            prnt(self.filename,'No WCS data exists in the header for this image, skipping...',alert = True)
            self.writeError('     No WCS data found in image header, image skipped')
            sleep(2)
        else:
            self.output = self.Photometry()
            self.writeData()