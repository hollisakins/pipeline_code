# standard packages
import numpy as np 
import math 
import os # for interacting with the terminal 
import warnings # for suppressing warnings
import csv # for reading/writing from csv files
import sys # for interacting with the computer, shutting down the program, etc
import shutil # solely for copying .SRC files between directories 
from datetime import datetime,timedelta
from time import strftime, gmtime, strptime, sleep, localtime
import datetime as dt
from collections import OrderedDict # make Python 2.7 dictionary act like 3.6 dictionary 
from email.MIMEMultipart import MIMEMultipart
import smtplib
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

# astro packages
from astropy.io import fits # fits module for opening and writing to fits files
from astropy import wcs # world coordinate system module for converting .SRC file data to RA/Dec
from astroquery.vizier import Vizier # for looking up stars in catalogs listed in Vizier
import astropy.coordinates as coord # for inputting coordinates into Vizier
import astropy.units as u # for units for the coord module
import sep # source extraction package based on the SExtractor application

def checkversion():
    vers = '%s.%s' % (sys.version_info[0],sys.version_info[1])
    if not vers=='2.7':
        raise Exception("Must be using Python 2.7")

# defines the width of the console to print output more clearly 
rows, columns = os.popen('stty size', 'r').read().split()
termsize = int(columns)

# astropy gives warning for a depricated date format in TheSkyX fits header,
# we dont need to see that so these two lines supress all warnings
# comment them out when testing

warnings.catch_warnings() 
warnings.simplefilter('ignore')

start_time = ''
end_time = ''

slow = False # if slow=True it will pause between printing each line just to make it easier to read, good for testing since it can go really fast
days_old = 1
verbose_errors = False

def sendStatus():
    header('Sending Update')
    import pandas as pd
    
    with open('sources.csv') as csvFile:
        reader = csv.reader(csvFile)
        keys = next(reader)
    dictionary = dict()
    for i in keys:
        df = pd.read_csv('sources.csv')
        dictionary[i]=np.array(df[i])
    sources = dictionary

    images_processed = len(np.unique([sources['IMGNAME'][x] for x in range(len(sources['IMGNAME'])) if isinstance(sources['RUNTIME'][x],str) and datetime.strptime(sources['RUNTIME'][x],"%Y-%m-%d %H:%M GMT").day==datetime.utcnow().day]))
    stars_logged = len(np.unique([sources['id'][x] for x in range(len(sources['id'])) if isinstance(sources['RUNTIME'][x],str) and datetime.strptime(sources['RUNTIME'][x],"%Y-%m-%d %H:%M GMT").day==datetime.utcnow().day]))
    stars_not_matched = len([sources['id'][x] for x in range(len(sources['id'])) if str(sources['id'][x])=='nan' and isinstance(sources['RUNTIME'][x],str) and datetime.strptime(sources['RUNTIME'][x],"%Y-%m-%d %H:%M GMT").day==datetime.utcnow().day])

    # set up the SMTP server
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    print('\tEstablished SMTP server')
    sleep(0.5)
    address = 'gcdatapipeline@gmail.com'
    password = '**Mintaka'

    s.login(address,password)

    msg = MIMEMultipart()
    msg['From'] = 'Guilford College Cline Observatory'
    msg['Subject'] = "GC Data Pipeline Update %s" % strftime("%Y-%m-%d", localtime())
    
    body = """
    Today's Pipeline Run:\n
    
    Began %s, completed %s
    Unique images processed: %s
    Unique stars logged: %s
    Stars not matched to catalog: %s\n
    """ % (start_time,end_time,images_processed,stars_logged,stars_not_matched)
    printing = body
    body += "Here are the log entries for today's run:\n"

    filename = "errorlog.txt"
    with open(filename,'rb') as attachment:    
        for line in attachment:
	    log_time = datetime.strptime(str(line[0:20]),"%Y-%m-%d %H:%M GMT")
            if log_time >= datetime.strptime(start_time,'%Y-%m-%d %H:%M GMT') and log_time <= datetime.strptime(end_time,"%Y-%m-%d %H:%M GMT"):
                body += line.strip()+'\n'

    body += '\nAttached is the full error log'
    msg.attach(MIMEText(body, 'plain'))
        
    with open(filename,'rb') as attachment:    
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)

    text = msg.as_string()

    recipients = open('email_recipients.txt','r').read().splitlines()

    all_recipients = recipients[0]
    for x in range(1,len(recipients)):
        all_recipients += ', '+recipients[x]

    print('\tSending message to %s\n' % all_recipients)
    sleep(1)
    print(printing)
    

    for recipient in recipients:
        msg['To'] = recipient
        s.sendmail(address, recipient, text)
    s.quit()


# function for printing the output consistently 
def prnt(indent,strng,filename=False,alert=False):
    # if filename=True it will print the name of the file at the left
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

# simple function to print a line at the top of the screen that shows what process is going on 
def header(i,count=False):
    print('\033c')
    if not count:
        print('-'*int((termsize-len(i)-2)/2)+' '+i+' '+'-'*int((termsize-len(i)-2)/2))
        print('')
    else:
        i = i+' '+str(count[0])+'/'+str(count[1])
        print('-'*int((termsize-len(i)-2)/2)+' '+i+' '+'-'*int((termsize-len(i)-2)/2))
        print('')

def writeError(description):
    name = 'errorlog.txt'
    if not os.path.exists(name):
        with open(name,'w') as erlog:
            pass
    with open(name,'a') as erlog:
        time = strftime("%Y-%m-%d %H:%M GMT", gmtime())
        description = time+': '+description+'\n'
        erlog.write(description)


def dailyCopy(overwrite=False):
    header('Copying Files')
    copys = ['Calibration/','SkyImages/']
    archives = ['ArchCal/','ArchSky/']

    for i in range(2):
        print('\tCopying from %s ' % copys[i])
        sleep(1.5)
        all_dates = [f for f in os.listdir(copys[i]) if not f.startswith('.') and not os.path.isfile(f)]
        recent_dates = [datetime.strftime(datetime.utcnow()-timedelta(days=j),'%Y%m%d') for j in range(1,days_old+1)]
        dates = list(set(all_dates) & set(recent_dates))
	recent_dates_str = ''
	for x in recent_dates:
	    recent_dates_str += x+' '
	dates_str = ''
	for x in dates:
	    dates_str += x+' '
	if dates_str.strip()=='':
	    print('\tNo directories in %s matched %s' % (copys[i],recent_dates_str))
        else:
	    print('\tLooking for dates %s found %s in %s' % (recent_dates_str,dates_str,copys[i]))
        sleep(2)
	dates_src = [copys[i]+date+'/' for date in dates]
        dates_dst = [archives[i]+date+'/' for date in dates]

        for j in range(len(dates_src)):
	    print('\tAttempting copy of %s' % dates_src[j])
	    writeError('     in dailyCopy: Attempting copy of %s' % dates_src[j])
            sleep(2)
	    try:
                shutil.copytree(dates_src[j],dates_dst[j])
            except:
                if overwrite:
                    if os.path.exists(dates_dst[j]):
                        shutil.rmtree(dates_dst[j])
                        shutil.copytree(dates_src[j], dates_dst[j])
                    print('\tDirectory %s already exists, overwriting' % dates_dst[j])
		    sleep(3)
		    writeError('     in dailyCopy: Directory %s already exists, overwritten' % dates_dst[j]) 
                else:
                    print('\tDirectory %s already exists, skipping' % dates_dst[j])
		    sleep(3)
                    writeError('     in dailyCopy: Directory %s already exists, skipped copying' % dates_dst[j])
            else:
                print('\tCopied directory %s to %s' % (dates_src[j],dates_dst[j]))
		sleep(3)
                writeError('     in dailyCopy: copied dir %s to %s' % (dates_src[j],dates_dst[j]))
        sleep(2)
        print('\tComplete')
        sleep(2)
        print('')








def makeMasters(writeOver=False):
    '''Index calibration files and generate masters. 

    Searches for calibration files in the most recent date directory under 'ArchCal/'. 
    For example, makeMasters() will search 'ArchCal/20180701/' if that is the most recent date directory available.

    Opt. Argument writeOver=False can be changed to True to allow older bias & dark frames to be
    over written by more recent ones.
    '''

    dates = [datetime.strftime(datetime.utcnow()-timedelta(days=j),'%Y%m%d') for j in range(1,days_old+1)]
    dates = ['ArchCal/'+date+'/' for date in dates]

    for path_to_cal in dates:
        header('Making Masters')

        if not os.path.exists(path_to_cal):
            sleep(1.5)
            print('\tNo calibration date folder found %s' % path_to_cal)
            sleep(3)
            print('\tSkipping makeMasters for this date...')
            writeError('     in makeMasters: No path found at %s, skipped makeMasters for this date' % path_to_cal)
            sleep(3)
            continue

        filenames = [f for f in os.listdir(path_to_cal) if os.path.isfile(os.path.join(path_to_cal,f)) if not f.startswith('.')] # list of filenames to process
        if len(filenames)==0:
            sleep(1.5)
            print('\tNo images in %s' % path_to_cal)
            sleep(3)
            print('\tSkipping makeMasters for this date')
            sleep(3)
            writeError('     in makeMasters: No images in %s, skipped makeMasters' % path_to_cal)
            continue

        print('\tSearching %s for calibraton files...' % path_to_cal)
        print('\tIndexed %s files' % len(filenames))
        binnings = ['1','2','3','4']

        bias1,dark1,Red1,Green1,Blue1,R1,V1,B1,Halpha1,Lum1,filters1 = [],[],[],[],[],[],[],[],[],[],[] # initialize lists
        bias2,dark2,Red2,Green2,Blue2,R2,V2,B2,Halpha2,Lum2,filters2 = [],[],[],[],[],[],[],[],[],[],[] # initialize lists
        bias3,dark3,Red3,Green3,Blue3,R3,V3,B3,Halpha3,Lum3,filters3 = [],[],[],[],[],[],[],[],[],[],[] # initialize lists
        bias4,dark4,Red4,Green4,Blue4,R4,V4,B4,Halpha4,Lum4,filters4 = [],[],[],[],[],[],[],[],[],[],[] # initialize lists
        # lists are used to store the filename for each calibration file and then combine into a master

        print('\tSorting files...')

        # sort the calibration images by type and store them in arrays
        for filename in filenames:
            with fits.open(path_to_cal+filename) as hdulist: 
                hdr = hdulist[0].header
                typ = hdr['IMAGETYP'] # save image type as variable
                binn = hdr['XBINNING'] # save binning as variable
                if typ=='Bias Frame':
                    exec('bias'+str(binn)+'_header=hdr') # save the header to write back into the master
                    exec('bias'+str(binn)+'.append(filename)') # add the data to the list with respective type/binning
                if typ=='Dark Frame':
                    exec('dark'+str(binn)+'_header=hdr')
                    exec('dark'+str(binn)+'.append(filename)')
                if typ=='Flat Field':
                    exec(hdr['FILTER']+str(binn)+'_header=hdr')
                    exec('filters'+str(binn)+".append(hdr['FILTER'])") # store the filters found in this directory in a list
                    # so that we don't attempt to create new master flats with filters we did not have raw flats for
                    exec(hdr['FILTER']+str(binn)+'.append(filename)') 


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



        ## make the masters
        for i in binnings: # for each binning factor 
            exec('s=np.size(bias'+i+')') # define var s as the size of the list
            if not s==0: # if the size is nonzero, there is data for that type & binning
                exec('filenames = bias'+i)
                master = []
                for filename in filenames:
                    with fits.open(path_to_cal+filename) as hdulist:
                        img = hdulist[0].data
                        master.append(img)
                exec('bias'+i+'_master=np.median(np.array(master),axis=0)') # define bias master as the 
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
                    exec('dark'+i+'_master=np.median(np.array(master)-bias'+i+'_master,axis=0)') # make dark master by removing the bias first
                    print('\tConstructed a scalable master dark with binning %sx%s' % (i,i))
                except NameError: # if you get a NameError:
                    print('\tNo bias master for binning %sx%s, failed to create scalable dark. Wrote to DR_errorlog.txt' % (i,i))
                    writeError('     in makeMasters: No bias master for binning %sx%s, failed to create dark' % (i,i))

        for j in binnings: 
            exec('f=np.unique(filters'+j+')') # establish unique filters 
            for i in f: # for each UNIQUE filter
                exec('s=np.size('+i+j+')')
                if not s==0: 
                    exec('filenames = '+i+j)
                    master = []
                    for filename in filenames:
                        with fits.open(path_to_cal+filename) as hdulist:
                            img = hdulist[0].data
                            master.append(img)
                    exec(i+j+"_master = np.median(master,axis=0)/np.max(np.median(master,axis=0))")  # normalize flat field and make master
                    print('\tConstructed master %s flat with binning %sx%s' % (i,j,j))
        

        # write the masters to fits files
        for i in binnings:
            for j in ['bias','dark']: # for now: do not overwrite old bias / dark masters
                if j+i+'_master' in locals():
                    try:
                        code = "fits.writeto('MasterCal/binning"+i+'/'+j+"_master.fit',"+j+i+'_master, header='+j+i+'_header,overwrite='+str(writeOver)+')'
                        exec(code)
                        print('\tWrote master %s to file MasterCal/binning%s/%s_master.fit' % (j,i,j))   
                    except:
                        print('\tBias or dark master already exists, no new file written')

        for i in ['1','2','3','4']:
            exec('f=np.unique(filters'+i+')')
            for j in f: # only overwrite flats for the unique filters that we chose to update that night
                code = "fits.writeto('MasterCal/binning"+i+'/'+"flat_master_"+j+".fit',"+j+i+"_master,header="+j+i+"_header,overwrite=True)"
                exec(code)   
                print('\tWrote master %s flat to file MasterCal/binning%s/flat_master_%s.fit' % (j,i,j))
        
        print('\n\tComplete')
        sleep(3)
        print('\033c')



class Field:
    def __init__(self):
        # when a Field object is created, define some variables
        self.calibrated_path = 'Calibrated Images/' 
        self.uncalibrated_path = 'ArchSky/'
        self.path_to_masters = 'MasterCal/'
        self.isCalibrated = False
        self.aperture_size = 30.0
        self.max_temp = -3.0
        self.cutoff = True
        self.counter = 0
    

    def openFits(self,filename,calibrated=False):
        self.filename = filename
        if not calibrated: # if it hasnt been calibrated we need the uncalibrated path 
            with fits.open(self.uncalibrated_path+self.filename) as hdulist:
                self.hdr = hdulist[0].header
                img = hdulist[0].data
                self.img = np.array(img,dtype='<f4') 
        else: # otherwise we need the calibrated path
            with fits.open(self.calibrated_path+self.filename.replace('.fits','_calibrated.fits')) as hdulist:
                self.hdr = hdulist[0].header
                img = hdulist[0].data
                self.img = np.array(img,dtype='<f4')

    def writeError(self,description):
        name = 'errorlog.txt'
        if not os.path.exists(name):
            with open(name,'w') as erlog:
                pass
        with open(name,'a') as erlog:
            time = strftime("%Y-%m-%d %H:%M GMT", gmtime())
            description = time+':      '+self.filename+': '+description.strip()+'\n'
            erlog.write(description)


    def Initialize(self,day):
        '''Index the files we need to calibrate -- must be run before other methods such as Reduce(), Extract(), etc.'''
        self.calibrated_path = 'Calibrated Images/'
        self.uncalibrated_path = 'ArchSky/'
        header('Initialization') # print the header
        self.columnsWritten = True # if we need to write the columns into the sources.csv file
        
        dates = [datetime.strftime(datetime.utcnow()-timedelta(days=j),'%Y%m%d') for j in range(1,days_old+1)]
        self.uncalibrated_path = [self.uncalibrated_path+date+'/' for date in dates][day]
        self.calibrated_path = [self.calibrated_path+date+'/' for date in dates][day]
        # if no path for uncalibrated images, exit
        if not os.path.exists(self.uncalibrated_path):
            print('\tNo images found in %s' % self.uncalibrated_path)
            sleep(1)
            print('\tExiting...')
            sleep(1.5)
            print("\033c")
            writeError('     in Initialize: Path %s does not exist, exiting pipeline run for today' % self.uncalibrated_path)
            return False

        # if no path for calibrated images, make one
        if not os.path.exists(self.calibrated_path):
            os.makedirs(self.calibrated_path)


        # all_files = [f for f in os.listdir(self.uncalibrated_path) if os.path.isfile(os.path.join(self.uncalibrated_path,f)) and not f.startswith('.')]
        self.list_of_files = [f.strip() for f in os.listdir(self.uncalibrated_path) if  not f.startswith('.') and os.path.isfile(os.path.join(self.uncalibrated_path,f)) and f.endswith('.fits') or f.endswith('.fit')]
        # self.list_of_files  = [f.strip() for f in all_files if f.endswith('.fits') or f.endswith('.fit')]

        # src_files = [f for f in all_files if f.endswith('.SRC')]
        print('\tSearching %s for sky images...' % self.uncalibrated_path)
        sleep(1)
        print('\tSearching %s for calibration files...' % self.path_to_masters)
        sleep(1)
        print('\033c')
        return True

    def checkCalibration(self,h,image): # check to see whether or not we need to calibrate the file
        if np.size(image)==8487264 or np.size(image)==2121816 or np.size(image)==942748: 
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

    def writeToHeader(self,h):
        if h.get('CALSTAT',default=0)==0: # if there is no calstat field in the header
            h.append(('CALSTAT','BDF','Status of Calibration')) # add one
        else:
            h['CALSTAT']='BDF' # otherwise set the value of calstat to BDF

    def saveFits(self,h,data,filename):
        if not os.path.exists(self.calibrated_path): 
            os.makedirs(self.calibrated_path) # make a directory if there isnt one
        
        fits.writeto(self.calibrated_path+filename.replace(".fit","_calibrated.fit"),data,h,overwrite=True)
        prnt(self.filename,'Wrote file to '+self.calibrated_path)
        print(' ')
        self.isCalibrated = True # now its calibrated so we change this variable to True


    def Reduce(self):
        header('Calibration & Source Extraction',count=(self.counter,len(self.list_of_files)))
        
        light_h,light = self.hdr,self.img # bring up the hdr and image
        prnt(self.filename,'Successfully opened %s image in %s' % (light_h['FILTER'],self.uncalibrated_path),filename=True)
        self.path_to_masters = 'MasterCal/binning%s/' % str(light_h['XBINNING']) # search for calibration files in binning-specific folder
     
        # open bias frame
        try: 
            bias_fits = fits.open(self.path_to_masters+'bias_master.fit') 
            prnt(self.filename,'Successfully opened bias master %s' % self.path_to_masters+'bias_master.fit')
        except: # if you encounter error
            prnt(self.filename,'Failed to open bias master %s' % self.path_to_masters+'bias_master.fit')
	    sleep(2)
            self.writeError('     in Reduce: Missing bias master in %s. Data reduction halted' % self.path_to_masters)
            return # exit the program since you can't calibrate files without a bias frame

        bias_h = bias_fits[0].header # split into header and data
        bias = bias_fits[0].data

        # open dark frame
        try:
            dark_fits = fits.open(self.path_to_masters+'dark_master.fit') 
            prnt(self.filename,'Successfully opened dark master %s' % self.path_to_masters+'dark_master.fit')
        except:
            prnt(self.filename,'Failed to open dark master %s' % self.path_to_masters+'dark_master.fit')
	    sleep(2)
            self.writeError('     in Reduce: Missing dark master in %s. Data reduction halted' % self.path_to_masters)
            return

        dark_h = dark_fits[0].header
        dark = dark_fits[0].data
        
        dxptime = dark_h['EXPTIME'] # store the exposure time for the dark master for scaling purposes
        exptime = light_h['EXPTIME'] # store light image exposure time

        # open filter-specific flat field
        try: 
            flat_fits = fits.open(self.path_to_masters+'flat_master_'+light_h['FILTER']+'.fit') 
            prnt(self.filename,'Successfully opened '+self.path_to_masters+'flat_master_'+light_h['FILTER']+'.fit')
        except:
            prnt(self.filename,'Failed to open flat master %s' % self.path_to_masters+'flat_master_'+light_h['FILTER']+'.fit')
	    sleep(2)
            self.writeError('     in Reduce: Missing %s flat master in %s. Data reduction halted' % (light_h['FILTER'],self.path_to_masters))
            return
        
        flat_h = flat_fits[0].header
        flat = flat_fits[0].data

        # perform the actual data reduction
        if self.checkCalibration(light_h,light)==True: # if we need to calibrated
            prnt(self.filename,'Calibrating image...' )

            bias_corrected_image = light - bias # subtract the bias
            dark_corrected_image = bias_corrected_image - (exptime/dxptime) * dark # scale the dark linearly w/ exptime and subtract
            final_image = dark_corrected_image / flat # divide by the flat field (already normalized)
            
            self.writeToHeader(light_h)
            self.saveFits(light_h, final_image,self.filename)


        elif self.checkCalibration(light_h,light)=='OnlyDark': # if we only had an auto dark
            prnt(self.filename,'Calibrating image...' )
            
            final_image = light / flat # divide by the flat field

            self.writeToHeader(light_h)
            self.saveFits(light_h, final_image,self.filename)


        elif self.checkCalibration(light_h,light)=='Redundant': # if it was already calibrated
            self.writeError('     in Reduce: Attempted redundant calibration')
            prnt(self.filename,'Image already calibrated')
            self.saveFits(light_h, light,self.filename) # still save the file because we can still use it

        elif self.checkCalibration(light_h,light)=='Temp': # if its temp is wrong
            self.writeError('     in Reduce: Rejected calibration, taken at %s degrees C' % light_h['CCD-TEMP'])
            prnt(self.filename,'Image taken at > '+str(self.max_temp)+' degrees C')
	    sleep(4)

        elif self.checkCalibration(light_h,light)=='Size':
            self.writeError('     in Reduce: Rejected calibration, captured with subframe or non-standard binning')
            prnt(self.filename,'Rejected calibration, captured with subframe or non-standard binning')
	    sleep(4)
 
        del flat_fits,bias_fits,dark_fits

    def Source(self):
        hdr,img = self.hdr,self.img

        bkg = sep.Background(img)
        bkg_data = bkg.back()
        bkg_rms = bkg.globalrms

        img = img - bkg_data
        objects = sep.extract(img, 2, err=bkg.globalrms,minarea=60/hdr['XBINNING']/hdr['YBINNING'])
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
        ### perform aperture photometry
        hdr,img = self.hdr,self.img
        egain = float(hdr['EGAIN'])
        prnt(self.filename,'Performing aperture photometry...')

        indices_to_remove,objects_to_remove = [],[]
        fluxes,fluxerrs = [],[]
        objects = self.world 

        for i in range(len(self.source)):
            # if self.source['fwhm'][i]<=0:
            #     prnt(self.filename,'FWHM leq zero at pixel position (%s,%s), star discarded' % (self.source['X'][i],self.source['Y'][i]),alert=True)
            #     self.writeError('SRC FWHM less than or equal to 0 at pixel position (%s,%s), star discarded from aperture photometry' % (self.source['X'][i],self.source['Y'][i]))
            #     objects_to_remove.append(i)
            # else:

            r_in = 1.5*self.aperture_size
            r_out = 2.0*self.aperture_size
            flux, fluxerr, flag = sep.sum_circle(img, self.source['x'][i], self.source['y'][i], self.aperture_size,gain=egain)
            if not flag==0:
                if flag==16:
                    prnt(self.filename,'SEP flag #%s, corrupted aperture data, star discarded' % str(flag),alert=True)
                    if verbose_errors:
                        self.writeError('     in Photometry: Source Extractor flag #%s, star discarded from aperture photometry' % str(flag))
                    indices_to_remove.append(i)
                else:
                    prnt(self.filename,'SEP flag #%s' % str(flag),alert=True)
                    if verbose_errors:
                        writeError('     in Photometry: Source Extractor flag #%s' % str(flag))
            
            # flux_annulus, fluxerr_annulus, flag_annulus = sep.sum_circann(img,self.source['X'][i], self.source['Y'][i], r_in, r_out,gain=egain)
            # bkg_mean = flux_annulus / (math.pi*(r_out*r_out-r_in*r_in))
            # flux = flux - bkg_mean * (math.pi*self.aperture_size*self.aperture_size)
            
            annulus_values = []
            for dx in range(-int(2*self.aperture_size),int(2*self.aperture_size)):
                for dy in range(-int(2*self.aperture_size),int(2*self.aperture_size)):
                    if np.sqrt(dx*dx+dy*dy)>r_in and np.sqrt(dx*dx+dy*dy)<r_out:
                        x_index = int(self.source['x'][i]+dx)
                        y_index = int(self.source['y'][i]+dy)
                        try:
                            annulus_values.append(img[y_index,x_index])
                        except IndexError:
                            pass
            
            if self.cutoff:
                q75, q25 = np.percentile(annulus_values, [75 ,25])
                iqr = q75 - q25
                cutoff = np.mean(annulus_values)+1.5*iqr
                annulus_values = [a for a in annulus_values if a<=cutoff]
            
            bkg_mean = np.mean(annulus_values)
            flux = flux - bkg_mean * math.pi * self.aperture_size * self.aperture_size
            fluxerr = np.sqrt(fluxerr*fluxerr+np.sum(annulus_values))
            fluxes.append(flux)
            fluxerrs.append(fluxerr)

        # get flux values from source extraction package
        flux = np.array(fluxes)

        for j in range(len(flux)): # if background subtraction isn't working correctly you can get negative flux values
            if flux[j]<0:
                prnt(self.filename,'Negative flux at pixel position (%s,%s), star discarded' % (self.source['x'][j],self.source['y'][j]),alert=True)
                if verbose_errors:
                    self.writeError('     in Photometry: Calculated negative flux at pixel position (%s,%s), star discarded' % (self.source['x'][j],self.source['y'][j]))
                indices_to_remove.append(j)

        flux = np.delete(flux, (indices_to_remove), axis=0)
        indices_to_remove = np.append(indices_to_remove,objects_to_remove)
        objects = np.delete(objects, (indices_to_remove), axis=0)

        instmag = -2.5*np.log10(flux) # convert flux to instrumental magnitude
        # snr = np.sqrt(flux) # calculate the signal to noise ratio (SNR)
        # instmag_err = 1/snr # convert SNR to the uncertainty in the instrumental magnitudes

        instmag_err = 1/np.array(fluxerrs)
        prnt(self.filename, 'Completed aperture photometry, result %s inst. magnitudes' % len(flux))
        print('')
        prnt(self.filename, 'Preparing to match %s objects to catalog...' % len(objects))
        if not len(flux)==len(objects):
            self.writeError('     in Photometry: Number objects and fluxes do not match, resulting data is unreliable')
            raise Exception('Number object and fluxes do not match, resulting data not reliable. System exited')

        ### retrieve magnitudes from catalog
        time = hdr['DATE-OBS'] # time image was taken
        time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f') # convert string to datetime object
        filt = hdr['FILTER'] # filter of image

        # lookup data in the UCAC4 catalog by querying Vizier
        v = Vizier(columns=['UCAC4','+_r','RAJ2000','DEJ2000','Bmag','Vmag','rmag'])
        output = OrderedDict([('id',[]),('RA_C',[]),('DEC_C',[]),('RA_M',[]),('DEC_M',[]),('DIF',[]),('MAG_R',[]),('MAG_V',[]),('MAG_B',[]),('MAG_err',[]),('CMAG_R',[]),('CMAG_V',[]),('CMAG_B',[]),('DATETIME',[]),('IMGNAME',[]),('RUNTIME',[])])
        output['MAG_err'] = instmag_err # go ahead and write the errors into the output dict
        cmags = [] # catalog magnitudes list we will update in the loop
        misfires = 0 # number of errors 
        objects_indices_matched = [] # will store the indices in the objects list of the ones we match to the catalog, so that we only use those stars to calculate offset

        for n in range(len(objects)):
            catalog = 'UCAC4' # specify catalog 
            #(if needed, we can implement a method to change this based on the object, which is why it is defined *inside* the loop)
            
            result = v.query_region(coord.SkyCoord(ra=objects[n,0], dec=objects[n,1],
            unit=(u.degree, u.degree), frame='fk5'),radius='2s',catalog=catalog) # submit query at object coordinates with a radius of 2 arcseconds
            
            try:
                # query_region returns result which is a TableList and we only need the first Table in the List
                result = result[0] # try to get the first result from the list of results (which is usually just 1 element)
                # but if there are NO tables in the list...
            except: # !! important, if we do not find a match we still save the data as this may be an anomoly or an object like an asteroid
                prnt(self.filename,'No star match within 2 arcseconds')
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

            # these lists are usually just 1 element but its important to have them to store every star located if we were looking in a very crowded field
            ids = np.array(result['UCAC4'],str) # get array of all the stars identified
            ra = np.array(result['RAJ2000'],float) # get array of catalog RA for those stasr
            dec = np.array(result['DEJ2000'],float) # catalog Dec for those stars
            dif = np.array(result['_r'],float) # difference from target
            
            fluxtype = filt+'mag' # get a variable for fluxtype to match to catalog magnitude types
            if filt=='R':
                fluxtype = 'rmag'
            
            flux = np.array(result[fluxtype],float) # store the filter catalog magnitude for the stars matched

            for i in range(len(ids)): # for all the stars matched, 
                if dif[i] <= 2 and i==np.argmin(dif) and ids[i] not in output['id']: # pick the star w the min residual value and less than 2 arcsec off and hasn't been identified yet
                    prnt(self.filename,'Star match in %s, mag %s, residual %s arcsec' % (catalog,flux[i],dif[i]))
                    output['id'].append(ids[i]) # add this data to the output dictionary 
                    output['RA_C'].append(ra[i])
                    output['DEC_C'].append(dec[i])
                    output['RA_M'].append(objects[n,0])
                    output['DEC_M'].append(objects[n,1])
                    output['DIF'].append(dif[i])
                    output['DATETIME'].append(time)
                    output['IMGNAME'].append(self.filename)
                    output['RUNTIME'].append(strftime("%Y-%m-%d %H:%M GMT", gmtime()))
                    cmags.append(flux[i])
                    if not math.isnan(flux[i]):
                        objects_indices_matched.append(n)

                else: # if the star has already been identified 
                    prnt(self.filename,'No star match within 2 arcseconds')
                    misfires += 1
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
                    continue


        prnt(self.filename,'Output %s stars' % len(set([v for v in output['id'] if v!='nan'])))
        prnt(self.filename,'Missed %s objects' % misfires)    
        instmags_to_median = [instmag[m] for m in objects_indices_matched] # instrumental magnitudes that matched to the catalog
        # we only want to use these instrumental magnitudes to calculate the offset since we have catalog mags for them
	
        cmags_nonan = [k for k in cmags if not math.isnan(float(k))] # get rid of the nan values 
        if not len(instmags_to_median)==len(cmags_nonan): # the two lists above must be the same length to gaurantee that we are using the same stars for offset calculation
            self.writeError('     in Photometry: Catalog comparison list not same length as instrumental magnitude list. Photometry halted')
            raise Exception('Catalog comparison list not same length as instrumental magnitude list')

        d = np.array(cmags_nonan) - np.array(instmags_to_median) # calculate the differences for each star
        d = float(np.median(d)) # take the MEDIAN of the difference - median does not consider outliers so a single variable star in the mix won't mess up our constant offset

        for i in ['R','V','B']: # for each filter
            magtype = 'MAG_'+i 
            if i==filt: # if that is the filter the image used
                output[magtype] = instmag+d # set the output array as the intrumental magnitudes + the constant offset
            else:
                output[magtype] = np.full(np.shape(instmag),'---',dtype="S3") # otherwise fill with null values

        for i in ['R','V','B']: # same thing
            magtype = 'CMAG_'+i 
            if i==filt:
                output[magtype] = cmags # set the output as the catalog magnitudes
            else:
                output[magtype] = np.full(np.shape(cmags),'---',dtype="S3") # otherwise fill with null values

        
        prnt(self.filename,'Wrote magnitude data to sources.csv') 
        sleep(3)
        print(' ')
        sleep(1)

        header('Calibration & Source Extraction',count=(self.counter,len(self.list_of_files)))
        
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


