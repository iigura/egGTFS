import egGTFS

srcGtfsFilePath='bus-akitachuoukotsu.zip'
dstGtfsFilePath='bidaiRelatedGTFS.zip'

gtfs=egGTFS.open(srcGtfsFilePath)

targetBusStopIDs=[]
def stopFilter(inGtfs,inStop):
    if '美術' in inStop.stop_name:
        if inStop.stop_id not in targetBusStopIDs:
            targetBusStopIDs.append(inStop.stop_id)
    return False
gtfs.stops.filter(stopFilter,update=False)

targetTripIDs=[]
def stopTimesFilter(inGtfs,inStopTime):
    if inStopTime.stop_id in targetBusStopIDs:
        if inStopTime.trip_id not in targetTripIDs:
            targetTripIDs.append(inStopTime.trip_id)
    return False
gtfs.stop_times.filter(stopTimesFilter,update=False)

targetRouteIDs=[]
def tripFilter(inGtfs,inTrip):
    if inTrip.trip_id in targetTripIDs:
        if inTrip.route_id not in targetRouteIDs:
            targetRouteIDs.append(inTrip.route_id)
    return False
gtfs.trips.filter(tripFilter,update=False)

gtfs.routes.filter(lambda gtfs,route: route.route_id in targetRouteIDs)

gtfs.save(dstGtfsFilePath)

