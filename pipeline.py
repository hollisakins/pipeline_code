import sys

vers = '%s.%s' % (sys.version_info[0],sys.version_info[1])
if not vers=='2.7':
    raise Exception("Must be using Python 2.7")

import observatory

# observatory.makeMasters()

f = observatory.Field()
f.aperture_size = 30
f.initialize()

for filename in f.list_of_files:
    f.openFits(filename,calibrated=False)
    f.Reduce()
    if f.calibrated:
        f.openFits(filename,calibrated=True)
        f.Extract()




