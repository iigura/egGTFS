import egGTFS

targetGtfsFilePath='bus-akitachuoukotsu.zip'
gtfs=egGTFS.open(targetGtfsFilePath)
m=gtfs.getAllStopsMap()
m.save('ex_AllBusStops.html')
print('done: ex_AllBusStops.html is generated.')

