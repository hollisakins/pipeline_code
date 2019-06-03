# several of these functions have an optional "inPipeline" Boolean option, which allows 
# them to be used outside of the pipeline structure if desired. For example, if you wanted to write 
# a script that soleley calibrates your images, you can use f.openFits(...) and f.Reduce(...) with the inPipeline options set to false


import observatory as obs
from time import strftime,gmtime
import traceback


obs.writeError('Beginning daily run...')
obs.start_time = strftime("%Y-%m-%d %H:%M GMT", gmtime())


try:
    # obs.slow = True #(default false)
    #obs.days_old = 2 #(default 1)
    # obs.verbose_errors = True #(default False, uncomment if haing difficulties in automated pipeline run)

    obs.dailyCopy(writeOver=False) 
    # change writeOver to True if you want to overwrite files on the Linux box with updates ones on the Dome computer

    obs.makeMasters(inPipeline=True,writeOver=False) 
    # change writeOver to True if you want to overwrite the old masters with new ones (only do this if you know yours
    # are better than the ones we already have or if the old ones are outdated)

    f = obs.Field() 

    f.path_to_masters = 'MasterCal/'
    f.uncalibrated_path = 'ArchSky/'
    f.calibrated_path = 'ReducedImages/'
    f.aperture_size = 30 #(default 30)
    # f.cutoff = False #(default True)
    # f.max_temp = -2.0 #(default -3.0)

    for j in range(obs.days_old):
        i = 1
        if f.Initialize(j):
            for filename in f.list_of_files:
                f.counter = i
                i += 1
                f.openFits(filename,calibrated=False,inPipeline=True)
                f.Reduce(inPipeline=True)
                if f.isCalibrated and f.narrowBand:
                    f.openFits(filename,calibrated=True,inPipeline=True)
                    f.Extract()

except KeyboardInterrupt:
    raise
except:
    tb = traceback.format_exc()
    obs.writeError(tb)
    obs.sendError(tb)
    raise 

obs.writeError('Completed daily run...')
obs.end_time = strftime("%Y-%m-%d %H:%M GMT", gmtime())
obs.sendStatus()





