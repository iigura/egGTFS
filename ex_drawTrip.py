import egGTFS
gtfs=egGTFS.open('AkitaChuoKotsuGTFS')

# targetTripID=gtfs.trips.trip_id(0)
targetTripID='広面御所野線（平日）400広面御所野線(1)20'
m=gtfs.getTripMap(targetTripID)

m.save('ex_trip.html')
print('done: ex_trip.html is generated.')
