import egGTFS
gtfs=egGTFS.open('AkitaChuoKotsuGTFS')

targetShapeID='100-1'
m=gtfs.getShapeMap(targetShapeID)

m.save('ex_shape.html')
print('done: ex_shape.html is generated.')

