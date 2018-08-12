import observatory as obs

d = 'CopiedCal/'
#obs.makeMasters(directory=d,inPipeline=False)

f = obs.Field()

filename = 'HIP 95497_Light_V_20180729_00000578.fits'

f.openFits(filename,calibrated=False,inPipeline=False)
f.Reduce(inPipeline=False)


