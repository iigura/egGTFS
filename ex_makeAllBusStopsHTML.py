import egGTFS

gtfs=egGTFS.open('AkitaChuoKotsuGTFS')
m=gtfs.getAllStopsMap()
m.save('ex_AllBusStops.html')
print('done: ex_AllBusStops.html is generated.')

