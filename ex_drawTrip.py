import egGTFS
gtfs=egGTFS.open('bus-akitachuoukotsu.zip')

targetIndex=int(len(gtfs.trips.data)/2)
targetTripID=gtfs.trips.trip_id(targetIndex)
print("generation trip shape '"+gtfs.trips.trip_id(targetIndex)+"' ...")
m=gtfs.getTripMap(targetTripID)

m.save('ex_trip.html')
print('done: ex_trip.html is generated.')
