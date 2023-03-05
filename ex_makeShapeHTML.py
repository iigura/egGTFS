import egGTFS
targetGtfsFilePath="bus-akitachuoukotsu.zip"
gtfs=egGTFS.open(targetGtfsFilePath)

targetTripIndex=int(len(gtfs.trips.data)/2)
targetTripID=gtfs.trips.trip_id(targetTripIndex)
targetShapeID=gtfs.getShapeIdByTripID(targetTripID)

m=gtfs.getShapeMap(targetShapeID,weight=10,color="#EE1155")

m.save('ex_shape.html')
print('done: ex_shape.html is generated.')

