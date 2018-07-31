import observatory
observatory.checkversion()

observatory.makeMasters()

f = observatory.Field()
f.aperture_size = 30
# f.max_temp = -3.0

f.initialize()

for filename in f.list_of_files:
    f.openFits(filename,calibrated=False)
    f.Reduce()
    if f.calibrated:
        f.openFits(filename,calibrated=True)
        f.Extract()




