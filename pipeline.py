import observatory as obs
from time import strftime,gmtime
obs.checkversion()
obs.writeError('Beginning daily run...')
obs.start_time = strftime("%Y-%m-%d %H:%M GMT", gmtime())

# obs.slow = True #(default false)
obs.days_old = 2 #(default 1)
# obs.verbose_errors = True #(default False, uncomment if haing difficulties in automated pipeline run)

# obs.dailyCopy(overwrite=False)

# obs.makeMasters(inPipeline=True,writeOver=False) 

f = obs.Field()
# f.path_to_masters = 'MasterCal/'
# f.uncalibrated_path = 'ArchSky/'
# f.calibrated_path = 'Calibrated Images/'
f.aperture_size = 15 #(default 30)
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

obs.writeError('Completed daily run...')
obs.end_time = strftime("%Y-%m-%d %H:%M GMT", gmtime())
obs.sendStatus()





