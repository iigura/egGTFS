import egGTFS

import sys
import folium

if len(sys.argv)<3:
    print("usage: python ex_drawAllRoute.py inGTFS outHTML")
    print("ex   : python ex_drawAllRoute.py BidaiRelatedGTFS.zip BidaiRelatedRoute.html")
    sys.exit(-1)

gtfs=egGTFS.open(sys.argv[1])

routeIDs=[]
for route in gtfs.routes:
    if route.route_id not in routeIDs: routeIDs.append(route.route_id)

shapeIDs=[]
for trip in gtfs.trips:
    if trip.route_id not in routeIDs: continue
    if trip.shape_id not in shapeIDs: shapeIDs.append(trip.shape_id)

m=folium.Map()
targetArea=egGTFS.AreaRect()
for shapeID in shapeIDs:
    area=gtfs.drawShape(m,shapeID,weight=9,color="#FF0022")
    targetArea.union(area)

targetArea.applyScale(1.1)
m.fit_bounds(targetArea.getBounds())

m.save(sys.argv[2])

