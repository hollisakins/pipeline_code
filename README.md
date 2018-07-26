# Guilford College Cline Observatory Data Analyis & Photometry Pipeline

At Guilford College in the summer of '18, we set up a data analysis pipeline for automated calibration of images and aperture photometry. It currently performs the following tasks daily:
  - Copy any new astronomical image .FITS files onto the CentOS 7 server where data analysis is performed
  - Make new master calibration files if necessary
  - Calibrate the images with bias/dark/flat correction
  - Gather data saved from any Image Link Astrometry done on the image
  - Perform circular aperture photometry and global background subtraction on sources detected by Image Link to calculate instrumental magnitudes
  - Calibrate those instrumental magnitudes to the UCAC4 star catalog using an ensemble photometry method
  - Save the calibrated magnitudes to a database for access later
  - Access that data and plot light curves for each star

Most of these processes are automated through Python scripts and executed using a CRON job. 
## 1. Copying Files

Copying files is executed through a `perl` script but is at present not included in this documentation. 

## 2. Making Master Calibration Files 

There are two `.py` files that control the majority of pipeline: `observatory.py` and `pipeline.py`. The former acts as a module, in which all of the dependent packages are imported, and functions, classes, and methods are defined. The latter is a much smaller file in which the observatory module is imported and the functions are executed. In other words, all the code lives in the former file but isn't executed until the latter file is run. 

**A Brief Note on Syntax and Programming Technicalities:**
The makeMasters function makes extensive use of the `exec()` function built into Python, which takes in a text string and executes it as if it were code. For example, instead of typing out `print('Hello World!')`, you would define a string such as `my_string = "print('Hello World!')"` and run `exec(my_string)` to yield the same output. 

The making of master calibration files is performed with the `makeMasters()` function in the `observatory` module. The function takes as required input the path to the calibration files, which for our pipeline should remain 'ArchCal/'. The program will automatically expand this path into 'ArchCal/20180629' or whatever the most recent date folder is. It will index the files in that folder and separate them by binning, type, and filter (for flat fields). It will then take whatever matching files it finds and construct masters versions: for example, it would turn a series of 3x3 binned bias frames into a single 3x3 binned bias master, or a series of 1x1 binned R flats into a single 1x1 binned R flat master. The math it does to construct the masters is:
  * `Bias_Master = median(Bias1, Bias2, ..., BiasN)`, a simple median operation
  * `Dark_Master = median(Dark1 - Bias_Master, Dark2 - Bias_Master, ..., DarkN - Bias_Master)`, a median operation but with the bias frame already subtracted from the dark, as this makes the dark scalable to different exposure times
  * `Flat_Master = median(Flat1, Flat2, ..., FlatN)/max(median(Flat1, Flat2, ..., FlatN))`, a median operation and a subsequent normalization so that when we divide by the flat frame later it maintains correct pixel counts

The program then writes these masters back into .fits files in the directory `MasterCal/binning1/` or whichever the respective binning is. When the pipeline is fully set up and being used for data analysis, we will be keeping a full set of 10 calibration frames in each folder (binning 1x1, 2x2, and 3x3). If you want to look through the code for the making of masters or the rest of the pipeline, it is available in a GitHub repo [[https://github.com/hollisakins/full_pipeline/blob/master/observatory.py|here]]. 

## 3. Performing Data Reduction / Calibrating Images 

**A Brief Note on Syntax and Programming Technicalities: **
The `observatory.py` file makes extensive use of Python's object-oriented programming capabilities. A complex explanation of OOP in Python can be found [[https://realpython.com/python3-object-oriented-programming/|here]], but the gist of it is that the code defines an //object// of class `Field`, which represents a field of stars and must be defined with a filename parameter. The `observatory.py` file provides all of the code to facilitate the definition of this object, but does not actually define one, as that is done with the line `f = observatory.Field()` in `pipeline.py`. The former file also defines several functions, called 'methods' when they are a part of a class, that can only act on a Field object. The most important of these methods are `initialize()`, which must be ran before any files can be calibrated, `openFits()`, which opens a file, `Reduce()`, which performs data reduction, and `Extract()`, which performs photometry. 

In broad strokes, data reduction is performed by opening the fits file, checking whether or not we need to calibrate, and if so, checking the header to determine the binning and filter, opening the correct bias, dark, and flat frames, and performing the following math:
  * `bias_corrected_image = image - bias_master`
  * `dark_corrected_image = bias_corrected_image - (exptime/dark_exptime) * dark_master`
  * `final_image = dark_corrected_image / flat_master`

In 'narrow strokes,' this process ends up being significantly more complex and prone to many errors. It involves opening several files, and if one of them is missing it throws off the entire process. Furthermore, if any of the images are binned abnormally, captures as subframes, lacking a header, taken at the wrong temperature, the program can fail and/or the data can be less valuable. As such, the `Reduce()` function uses Python's `try: except:` syntax to write to an error log if any of these issues arise. 


## 4. Gathering Source Extraction Data 

Rather than attempting to implement the nova.astrometry.net API or run a native astrometry program, we chose to use the Image Link protocol built into SoftwareBisque's telescope control software __TheSkyX__. When an image is Image Linked, the program writes into the FITS header WCS (world coordinate system) data in the form of a matrix which can be interpreted by another program. It also generates a `.SRC` file that stores the pixel positions of each star recognized in the image. These pieces of data can be combined to get Right Ascension and Declination coordinates for each star in the image. 


## 5. Aperture Photometry 


## 6. Photometric Calibration 


## 7. Data management and storage 



## 8. Data access and light curve plotting 

The data for each star we have identified is stored in `sources.csv`. While it is possible to access and plot this data manually, it makes sense to have a simple method for plotting light curves from this data. 

The python program `light_curves.py` provides programatic access to this data through a simple command line interface. 