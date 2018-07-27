# Guilford College Cline Observatory Data Analyis & Photometry Pipeline

At Guilford College in the summer of '18, we set up a data analysis pipeline for automated calibration of images and aperture photometry. It currently performs the following tasks daily:
  - Copy any new astronomical image .FITS files onto the CentOS server where data analysis is performed
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

The making of master calibration files is performed with the `makeMasters()` *function* in the `observatory` module. The function takes no required input, but includes an optional writerOver argument which controls the overwrite behavior for bias & dark frames. The program will automatically search the 'ArchCal/' path and expand it into 'ArchCal/20180629' or whatever the most recent date folder is. It will index the files in that folder and separate them by binning, type, and filter (for flat fields). It will then take whatever matching files it finds and construct masters versions: for example, it would turn a series of 3x3 binned bias frames into a single 3x3 binned bias master, or a series of 1x1 binned R flats into a single 1x1 binned R flat master. The math it does to construct the masters is:
  * `Bias_Master = median(Bias1, Bias2, ..., BiasN)`, a simple median operation
  * `Dark_Master = median(Dark1 - Bias_Master, Dark2 - Bias_Master, ..., DarkN - Bias_Master)`, a median operation but with the bias frame already subtracted from the dark, as this makes the dark scalable to different exposure times
  * `Flat_Master = median(Flat1, Flat2, ..., FlatN)/max(median(Flat1, Flat2, ..., FlatN))`, a median operation and a subsequent normalization so that when we divide by the flat frame later it maintains correct pixel counts

The program then writes these masters back into .fits files in the directory `MasterCal/binning1/` or whichever the respective binning is. Currently, the pipeline is only set up to handle binning factors of 1x1, 2x2, 3x3, or 4x4, as we do not typically use anything else at our observatory. When the pipeline is fully set up and being used for data analysis, we will be keeping a full set of 10 calibration frames in each folder (binning 1x1, 2x2, 3x3, and 4x4). 

## 3. Performing Data Reduction / Calibrating Images 

**A Brief Note on Syntax and Programming Technicalities: **
The `observatory.py` file makes extensive use of Python's object-oriented programming capabilities. A complex explanation of OOP in Python can be found [https://realpython.com/python3-object-oriented-programming/](here), but the gist of it is that the code defines an //object// of class `Field`, which represents a field of stars and must be defined with a filename parameter. The `observatory.py` file provides all of the code to facilitate the definition of this object, but does not actually define one, as that is done with the line `f = observatory.Field()` in `pipeline.py`. The former file also defines several functions, called 'methods' when they are a part of a class, that can only act on a Field object. The most important of these methods are `initialize()`, which must be ran before any files can be calibrated, `openFits()`, which opens a file, `Reduce()`, which performs data reduction, and `Extract()`, which performs photometry. 

In broad strokes, data reduction is performed by opening the fits file, checking whether or not we need to calibrate, and if so, checking the header to determine the binning and filter, opening the correct bias, dark, and flat frames, and performing the following math:
  * `bias_corrected_image = image - bias_master`
  * `dark_corrected_image = bias_corrected_image - (exptime/dark_exptime) * dark_master`
  * `final_image = dark_corrected_image / flat_master`

In 'narrow strokes,' this process ends up being significantly more complex and prone to many errors. It involves opening several files, and if one of them is missing it throws off the entire process. Furthermore, if any of the images are binned abnormally, captures as subframes, lacking a header, taken at the wrong temperature, the program can fail and/or the data can be less valuable. As such, the `Reduce()` function uses Python's `try: except:` syntax to write to an error log if any of these issues arise. 


## 4. Gathering Source Extraction Data 

Rather than attempting to implement the nova.astrometry.net API or run a native astrometry program, we chose to use the Image Link protocol built into SoftwareBisque's telescope control software __TheSkyX__. When an image is Image Linked, the TheSkyX writes into the FITS header WCS (world coordinate system) data in the form of a matrix which can be interpreted by another program, representing the RA/Dec coordinates of the image. It also generates a `.SRC` file that stores the pixel positions of each star recognized in the image. These pieces of data can be combined to get Right Ascension and Declination coordinates for each star in the image. This process is controlled through the `Source()` and `Convert()` methods under the `Field` class. Both are run as part of the `Extract()` method which gathers the source data, converts it, performs the photometry, and writes the data. 

The `Source()` method is very simple: it opens up the `.SRC` file and stores the data in arrays and returns a python dictionary with all the data. 

The `Convert()` method uses the astropy `WCS` module to interpret the WCS matrix in the FITS header for each image and convert the object list from the `.SRC` file from pixel coordinates to RA/Dec. It then returns the object list in RA/Dec coordinates. 


## 5. Aperture Photometry 

The code to perform aperture photometry is stored in the `Photometry()` method. Most of the code within this method is for calibrating our magnitudes to the catalog (in the following section), as aperture photometry on its own is fairly simple. We use the SEP (Source Extractor for Python) package to perform photometry, which is based on the SExtractor Windows Executable. The package includes a built in background-estimator function which generates an array the size of the image containing an estimate of the background noise for the image. We then subtract this background from the image to isolate the sources in the image. We then use the `sum_circle()` function to add all the counts within an aperture of fixed radius for each object in our object list. The aperture size is stored as a class variable so that it can be changed from `pipeline.py` as needed. The `sum_circle()` function returns the flux values for each object, which we convert to instrumental magnitudes by taking the log and multiplying by -2.5. 

We also calculate the uncertainty in the measurement by calculating the signal-to-noise ratio, the square root of the number of counts within the aperture. The inverse of the signal to noise ratio is the fractional uncertainty in the instrumental magnitude. 

## 6. Photometric Calibration 

Instrumental magnitudes really don't tell us anything scientific about the stars, as the instrumental magnitudes are dependent on the telescope, camera, location, and even exposure time of the image. In order to get legitimate data, we need to calibrate our magnitudes to a catalog. This is called differential photometry, and we are using a form of differential photometry called ensemble photometry, in which we compare each star to every other star in the image to determine how far off it is from the catalog magnitude. A good explanation of differential photometry and the special case of ensemble photometry is available [http://spiff.rit.edu/classes/phys373/lectures/diff_photom/diff_photom.html](here), but the gist of it is as follows: 
 * We determine the instrumental magnitudes for the stars in our image
 * We match the stars in our image to their catalog entries to determine the catalog magnitude for each star. In practice, we cannot usually match every star to the catalog, but this is OK. 
 * We take the difference of the two arrays of magnitudes, only including the instrumental magnitudes for the stars that we were able to match. i.e. we would do `[star1_cmag,star2_cmag,star3_cmag,...] - [star1_imag,star2_imag,star3_imag,...]`. 
 * We then take the median of this result to get our offset value, which should be constant for every star in the image. We use the median instead of the mean because the median is less susceptible to outliers, so if one of our stars is variable it will not impact the offset. 
 * We then add this constant offset to our instrumental magnitudes to get our new, calibrated magnitude. 

The catalog matching is done through Vizier, an interface that allows us to access several star catalogs, although we are only using the UCAC4 catalog right now. The astroquery python package allows us to directly query Vizier and get the data we need by searching a small radius around the target star. 


## 7. Data management and storage 

The data gathered from Vizier including star ID, catalog RA and Dec, and catalog magnitude for the specific filter are exported to the sources.csv file along with the filename of the image, the measured RA and Dec from Image Link, and our calibrated measured magnitude for the specific filter. 


## 8. Data access and light curve plotting 

The data for each star we have identified is stored in `sources.csv`. While it is possible to access and plot this data manually, it makes sense to have a simple and consistent method for plotting light curves from this data. 

The python program `light_curves.py` provides programatic access to this data through a self-explanatory command line interface. 