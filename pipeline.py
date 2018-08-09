import observatory
observatory.checkversion()

# observatory.slow = True #(default false)
# observatory.days_old = 2 #(default 1)
# observatory.verbose_errors = True #(default False, uncomment if haing difficulties in automated pipeline run)
observatory.writeError('Beginning daily run...')
observatory.makeMasters() 

f = observatory.Field()
# f.path_to_masters = 'MasterCal/'
# f.uncalibrated_path = 'ArchSky/'
# f.calibrated_path = 'Calibrated Images/'
# f.aperture_size = 30 #(default 30 (need to make relative to binning))
# f.cutoff = False #(default True)
# f.max_temp = -2.0 #(default -3.0)

f.Initialize()
i = 1

for filename in f.list_of_files:
    f.counter = i
    i += 1
    f.openFits(filename,calibrated=False)
    f.Reduce()
    if f.isCalibrated:
        f.openFits(filename,calibrated=True)
        f.Extract()
    else:
        continue

observatory.writeError('Completed daily run...')





