import egGTFS
import folium
from folium.plugins import HeatMap

gtfsFilePath='bus-akitachuoukotsu.zip'
searviceID='平日'
searchStartTime=egGTFS.Time(7,0,0)
searchEndTime  =egGTFS.Time(8,0,0)
searchTimeDelta=egGTFS.TimeDelta(0,1,0)

gtfs=egGTFS.open(gtfsFilePath)
if searchEndTime<=searchStartTime: raise ValueError('invalid search time.')

latMin,latMax=180,0
lonMin,lonMax=180,0
resultMap=folium.Map()
for trip in gtfs.trips:
    if trip.service_id!=searviceID: continue
    tripID=trip.trip_id
    stopTimes=gtfs.stop_times.getSeqByTripID(tripID)
    startTime=egGTFS.Time(stopTimes[ 0].arrival_time)
    endTime  =egGTFS.Time(stopTimes[-1].departure_time)
    if searchEndTime<startTime or endTime<searchStartTime: continue
    print('prcessing:"'+str(tripID)+'" time=['+str(startTime)+' - '+str(endTime)+']')
    t=searchStartTime
    posList=[]
    firstError=True
    while t<searchEndTime:
        try:
            busPos=gtfs.getBusPos(tripID,str(t),epsilon=0.001)
        except ValueError as e:
            if firstError: print(e)
            firstError=False
            t+=searchTimeDelta
            continue
        if busPos!=None:
            posList.append(busPos)
            latMin,latMax=min(latMin,busPos[0]),max(latMax,busPos[0])
            lonMin,lonMax=min(lonMin,busPos[1]),max(lonMax,busPos[1])
        t+=searchTimeDelta
    HeatMap(posList,radius=5,blur=10).add_to(resultMap)

resultMap.fit_bounds([[latMin,lonMin],[latMax,lonMax]])
resultMap.save('busHeatMap.html')
print('done: busHeatMap.html is generated.')

