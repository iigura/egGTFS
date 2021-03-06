# written by Koji Iigura 2022

import sys
import os
import warnings
import math
import re
from types import MethodType
import inspect

import pandas as pd
import numpy as np

from geopy.distance import geodesic

import folium
from folium.plugins import HeatMap

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_binary

# usage:
#	import egGTFS
#	gtfs=egGTFS.open('targetGtfsDir')
#	gtfs.agency.dump()
#	gtfs.agency_jp.dump()

class Time:
    pattern=re.compile(r'([0-9]+):([0-9]+):([0-9]+)')

    @classmethod
    def totalSecond2hmsf(cls,inTotalSecond):
        s=inTotalSecond%60
        inTotalSecond//=60;	m=inTotalSecond%60
        h=inTotalSecond//60
        f = h>=0
        return h,m,s,f

    def __init__(self,inHour_or_TimeStr,inMinute=None,inSecond=None,positive=True):
        if isinstance(inHour_or_TimeStr,str):
            if inMinute!=None or inSecond!=None: raise ValueError('invalid argument')
            matchResult=Time.pattern.search(inHour_or_TimeStr)
            if matchResult==None: raise ValueError('invalid Time string')
            h=int(matchResult.group(1))
            m=int(matchResult.group(2))
            s=int(matchResult.group(3))
        elif isinstance(inHour_or_TimeStr,int) and isinstance(inMinute,int) and isinstance(inSecond,int):
            h=inHour_or_TimeStr
            m=inMinute
            s=inSecond
        else: raise ValueError('invalid argument')

        m+=s//60;	s%=60
        h+=m//60;	m%=60

        self.hour  =h
        self.minute=m
        self.second=s
        self.flag=1 if positive else -1
        self.totalSecond=self.flag*h*3600+m*60+s

    def __str__(self):
        hStr='{:02d}'.format(self.hour)
        mStr='{:02d}'.format(self.minute)
        sStr='{:02d}'.format(self.second)
        return ('-' if self.flag<0 else '')+hStr+':'+mStr+':'+sStr

    def __eq__(self,inOther):
        if not isinstance(inOther,Time): return NotImplemented
        return self.totalSecond==inOther.totalSecond

    def __ne__(self,inOther):
        if not isinstance(inOther,Time): return NotImplemented
        return self.totalSecond!=inOther.totalSecond

    def __lt__(self,inOther):
        if not isinstance(inOther,Time): return NotImplemented
        return self.totalSecond<inOther.totalSecond

    def __le__(self,inOther):
        if not isinstance(inOther,Time): return NotImplemented
        return self.totalSecond<=inOther.totalSecond

    def __gt__(self,inOther):
        if not isinstance(inOther,Time): return NotImplemented
        return self.totalSecond>inOther.totalSecond

    def __ge__(self,inOther):
        if not isinstance(inOther,Time): return NotImplemented
        return self.totalSecond>=inOther.totalSecond

    def __add__(self,inOther):
        if not isinstance(inOther,TimeDelta): return NotImplemented
        h,m,s,f=Time.totalSecond2hmsf(self.totalSecond+inOther.totalSecond)
        return Time(h,m,s,f)

    def __sub__(self,inOther):
        if isinstance(inOther,TimeDelta):
            h,m,s,f=Time.totalSecond2hmsf(self.totalSecond-inOther.totalSecond)
            return Time(h,m,s,f)
        elif isinstance(inOther,Time):
            h,m,s,f=Time.totalSecond2hmsf(self.totalSecond-inOther.totalSecond)
            return TimeDiff(h,m,s,f)
        else: return NotImplemented

    def __mul__(self,inOther):
        if not isinstance(inOther,(int,float)): return NotImplemented
        h,m,s,f=Time.totalSecond2hmsf(int(self.totalSecond*inOther))
        return Time(h,m,s,f)

    def __rmul__(self,inOther):
        if not isinstance(inOther,(int,float)): return NotImplemented
        h,m,s,f=Time.totalSecond2hmsf(int(self.totalSecond*inOther))
        return Time(h,m,s,f)

class TimeDelta(Time): pass
class TimeDiff(Time):  pass


# -------------------------------------------------------------------

class indexSet:
    def __init__(self,inHeaderIndex,inFieldNameList):
        for t in inFieldNameList: setattr(self,t,getIndex(inHeaderIndex,t))
        self.fieldNameList=inFieldNameList

def getDataFrame(inGtfsRootDir,inFileName,optional=False):
    path=os.path.join(inGtfsRootDir,inFileName)
    if not os.path.isfile(path):
        if optional:
            return None,False
        else:
            print('ERROR: no '+inFileName+'.'); sys.exit()	
    return pd.read_csv(path),True

# idx=inHeaderIndex, name=inFieldNameStr
def getIndex(idx,name): return idx.get_loc(name) if name in idx else -1
def getValue(lst,idx):  return lst[idx] if 0<=idx else None

def getField(inSelf,inFieldName,inRecordOrNo):
    if type(inRecordOrNo) is int:
        n=inRecordOrNo
        record=inSelf.data[n]
    else:
        record=inRecordOrNo
    return getValue(record,getattr(inSelf.index,inFieldName))

def getFieldForSingle(inSelf,inFieldName):
    return getValue(inSelf.data[0],getattr(inSelf.index,inFieldName))

def makeFieldFunc(inFieldName):
    def fieldFuncBody(self,inRecordOrNo): return getField(self,inFieldName,inRecordOrNo)
    return fieldFuncBody

def makeFieldFuncForSingle(inFieldName):
    def fieldFuncBody(self): return getFieldForSingle(self,inFieldName)
    return fieldFuncBody


# add getter methods:
#     ex: gtfs.shapes.shape_id(100) <--- self.data[100]
#            or
#         gtfs.shapes.shape_id(gtfs.shapes.data[100])
def addGetters(inSelf,inFieldNameList):
    for fieldName in inFieldNameList:
        setattr(inSelf,fieldName,MethodType(makeFieldFunc(fieldName),inSelf))

def addGettersForSingle(inSelf,inFieldNameList):
    for fieldName in inFieldNameList:
        setattr(inSelf,fieldName,
                getValue(inSelf.data[0],getattr(inSelf.index,fieldName)))


def getitemBody(inSelf,inID):
    if inSelf.valid==False: return None
    t=inSelf.data[inSelf.data[:,inSelf.primaryFieldNo]==inID]
    n=len(t)
    if n==0: return None
    if n==1 and inSelf.recordClass!=None: return inSelf.recordClass(t[0])
    return t

def initReader(inSelf,inGtfsRootDir,inFileName,inFieldNameList,inPrimaryFieldName='',inRecordClass=None):
    inSelf.valid=False
    inSelf.fileName=inFileName
    inSelf.df,df_result=getDataFrame(inGtfsRootDir,inFileName)
    inSelf.fieldNameList=inFieldNameList
    inSelf.index=indexSet(inSelf.df.columns,inSelf.fieldNameList)
    inSelf.data=np.asarray(inSelf.df)
    if len(inSelf.data)>0:
        inSelf.hasRecord=True
    else:
        inSelf.hasRecord=False
    addGetters(inSelf,inSelf.fieldNameList)

    inSelf.primaryFieldName=inPrimaryFieldName
    if inPrimaryFieldName!='':
        inSelf.primaryFieldNo=getattr(inSelf.index,inPrimaryFieldName)

    inSelf.recordClass=inRecordClass

    if inRecordClass!=None:
        inSelf.__getitem__=MethodType(getitemBody,inSelf)

    inSelf.valid=True

def initReaderOptional(inSelf,inGtfsRootDir,inFileName,inFieldNameList):
    inSelf.valid=False
    inSelf.fileName=inFileName
    inSelf.df,df_result=getDataFrame(inGtfsRootDir,inFileName,optional=True)
    if df_result==False: return

    # same as initReader
    inSelf.fieldNameList=inFieldNameList
    inSelf.index=indexSet(inSelf.df.columns,inSelf.fieldNameList)
    inSelf.data=np.asarray(inSelf.df)
    addGetters(inSelf,inSelf.fieldNameList)
    inSelf.valid=True

# -------------------------------------------------------------------
#   base classes
# -------------------------------------------------------------------
class RecordSet:
    def __init__(self,inGtfsRootDir,inFileName,inFieldNameList,
                 inPrimaryFieldName,inRecordClass,
                 optional=False):
        self.valid=False
        self.hasRecord=False
        self._index=-1
        self.fileName=inFileName
        self.df,df_result=getDataFrame(inGtfsRootDir,inFileName,optional=optional)
        if optional and df_result==False: return

        self.fieldNameList=inFieldNameList
        self.index=indexSet(self.df.columns,self.fieldNameList)
        self.data=np.asarray(self.df)
        if len(self.data)>0: self.hasRecord=True
        addGetters(self,self.fieldNameList)
        self.primaryFieldName=inPrimaryFieldName
        self.primaryFieldNo=getattr(self.index,inPrimaryFieldName)
        self.recordClass=inRecordClass
        self.valid=True

        if inRecordClass!=None:
            inRecordClass.fieldNameList=inFieldNameList
            inRecordClass.index=self.index
            def recordInit(self,inArray):
                self.record=inArray
                for fieldName in self.fieldNameList:
                    columnNo=getattr(self.index,fieldName)
                    self.__dict__[fieldName]=self.record[columnNo] if columnNo>=0 else None
            inRecordClass.__init__=recordInit
            inRecordClass.__str__=lambda self: str(self.record)

    def __getitem__(self,inID): return getitemBody(self,inID)

    def __iter__(self):
        self._index=0
        return self

    def __next__(self):
        if self._index==len(self.data): raise StopIteration()
        ret=self.recordClass(self.data[self._index])
        self._index+=1
        return ret
    
class Record:
    def __setattr__(self,inName,inValue):
        if inName in self.fieldNameList: raise Exception('it is read ony.')
        self.__dict__[inName]=inValue

class SingleRecord:
    def __init__(self,inGtfsRootDir,inFileName,inFieldNameList,inPrimaryFieldName,
                 optional=False):
        self.valid=False
        self.hasRecord=False
        self.fileName=inFileName
        self.df,df_result=getDataFrame(inGtfsRootDir,inFileName,optional=optional)
        if optional and df_result==False: return

        self.fieldNameList=inFieldNameList
        self.index=indexSet(self.df.columns,self.fieldNameList)
        self.data=np.asarray(self.df)
        if len(self.data)>0: self.hasRecord=True
        if len(self.data)!=1: warnings.warn(inFileName+': ?????????????????????????????????')
        addGettersForSingle(self,self.fieldNameList)
        if inPrimaryFieldName!=None:
            self.primaryFieldNo=getattr(self.index,inPrimaryFieldName)
        self.valid=True

    def maxFieldNameLength(self):
        ret=0
        for s in self.fieldNameList: ret=max(ret,len(s))
        return ret

    def dump(self):
        if self.valid:
            n=self.maxFieldNameLength()
            for s in self.fieldNameList: print(s.ljust(n)+' = '+str(getattr(self,s)))
        else:
            print('NO '+self.fileName)

# -------------------------------------------------------------------

# ??? (x1,y1) ??? (x2,y2) ????????????????????? (x,y) ?????????????????????
def distFromLine(inX1,inY1,inX2,inY2,inX,inY):
    a=inY2-inY1; b=inX1-inX2
    if a==0 and b==0: raise ValueError('invalid argument')
    x=inX-inX1;  y=inY-inY1
    return abs(a*x+b*y)/math.sqrt(a*a+b*b)

# ??? (x1,y1) ??? (x2,y2) ????????????????????? (x,y) ?????????????????????????????????
# ???????????????????????? (x1,y1) ??? (x2,y2) ?????????????????????????????????????????????????????????????????????
# ??????????????????????????? True ?????????????????????????????? False ????????????
def isOnSegment(inX1,inY1,inX2,inY2,inX,inY):
    p=inX2-inX1; q=inY2-inY1
    if p==0 and q==0: raise ValueError('invalid argument')
    x=inX-inX1;  y=inY-inY1
    #dot=x*p+y*q
    #return 0<=dot and dot<=p*p+q*q
    d1=x*p+y*q
    d2=(inX-inX2)*(-p)+(inY-inY2)*(-q)
    return 0<d1 and 0<d2

# return nearestPos,distance
def getNearestPosOnSegment(inX1,inY1,inX2,inY2,inX,inY):
    p=inX2-inX1; q=inY2-inY1
    if p==0 and q==0: raise ValueError('invalid argument')
    if isOnSegment(inX1,inY1,inX2,inY2,inX,inY)==False: return None,-1
    tx=inX-inX1;  ty=inY-inY1
    t=(p*tx+q*ty)/math.sqrt(p*p+q*q)
    x=p*t+inX1
    y=q*t+inY1
    return [x,y],distFromLine(inX1,inY1,inX2,inY2,inX,inY)

def sqrDistPos(inPos1,inPos2):
    dx=inPos1[0]-inPos2[0]
    dy=inPos1[1]-inPos2[1]
    return dx*dx+dy*dy


#--------------------------------------------------------------------
# for agency.txt
#--------------------------------------------------------------------
class agency(SingleRecord):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'agency.txt',
                         ['agency_id','agency_name','agency_url',
                          'agency_timezone','agency_lang','agency_phone',
                          'agency_fare_url','agency_email'],'agency_id')

#--------------------------------------------------------------------
# for agency_jp.txt
#--------------------------------------------------------------------
class agency_jp(SingleRecord):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'agency_jp.txt',
                         ['agency_id','agency_official_name','agency_zip_number',
                          'agency_address','agency_president_pos',
                          'agency_president_name'],'agency_id',optional=True)

#--------------------------------------------------------------------
# for stops.txt
#--------------------------------------------------------------------
class stops(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'stops.txt',
                         ['stop_id','stop_code','stop_name','stop_desc',
                          'stop_lat','stop_lon','zone_id','stop_url',
                          'location_type','parent_station','stop_timezone',
                          'wheelchair_boarding','platform_code'],
                         'stop_id',stops_record)

    # [ latitude,longitude ]
    def pos(self,inStop): return [inStop[self.index.stop_lat],
                                  inStop[self.index.stop_lon]]

    def latLon(self,inStop):
        return inStop[self.index.stop_lat],inStop[self.index.stop_lon]

    def name(self,inRecordOrNo): return self.stop_name(inRecordOrNo)

    def getByStopID(self,inStopID):
        return self.data[self.data[:,self.index.stop_id]==inStopID][0]

    def getPosByStopID(self,inStopID):
        stop=self.getByStopID(inStopID)
        return self.pos(stop)

    def getNameByStopID(self,inStopID):
        stop=self.getByStopID(inStopID)
        return self.stop_name(stop)

class stops_record(Record): pass


#--------------------------------------------------------------------
# for routes.txt
#--------------------------------------------------------------------
class routes(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'routes.txt',
                         ['route_id','agency_id',
                          'route_short_name','route_long_name',
                          'route_desc','route_type','route_url','route_color',
                          'route_text_color','jp_parent_route_id'],
                          'route_id',routes_record)

    def dump(self):
        for t in self.data: print(t)

class routes_record(Record): pass


#--------------------------------------------------------------------
# for routes_jp.txt
#--------------------------------------------------------------------
class routes_jp(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'routes_jp.txt',
                         ['route_id','route_update_date',
                          'origin_stop','via_stop','destination_stop'],
                          'route_id',routes_jp_record,
                          optional=True)

class routes_jp_record(Record): pass


#--------------------------------------------------------------------
# for trips.txt
#--------------------------------------------------------------------
class trips(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'trips.txt',
                         ['route_id','service_id','trip_id','trip_headsign',
                          'trip_short_name','direction_id','block_id',
                          'shape_id','wheelchair_accessible','bikes_allowed',
                          'jp_trip_desc','jp_trip_desc_symbol','jp_office_id'],
                         'trip_id',trips_record)

class trips_record(Record): pass


#--------------------------------------------------------------------
# for office_jp.txt
#--------------------------------------------------------------------
class office_jp(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'office_jp.txt',
                         ['office_id','office_name','office_url','office_phone'],
                         'office_id',office_jp_record,
                         optional=True)

class office_jp_record(Record): pass


#--------------------------------------------------------------------
# for stop_times.txt
#--------------------------------------------------------------------
class stop_times(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'stop_times.txt',
                         ['trip_id','arrival_time','departure_time',
                          'stop_id','stop_sequence','stop_headsign',
                          'pickup_type','dtop_off_type','shape_dist_traveled',
                          'timepoint'],
                         'trip_id',stop_times_record)

    def __getitem__(self,inID):
        records=getitemBody(self,inID)
        if records is None: return None
        sortedSeq=records[np.argsort(records[:,self.index.stop_sequence])]
        ret=[]
        for t in sortedSeq: ret.append(stop_times_record(t))
        return ret

    def arrivalTimeAndDepartureTime(self,inRecord):
        arrivalTimeStr  =self.arrival_time(inRecord)
        departureTimeStr=self.departure_time(inRecord)
        return Time(arrivalTimeStr),Time(departureTimeStr)

    # ?????????
    #     ???????????? trip_id ???????????????????????? stop_times ????????? 2 ???????????????????????????
    #     ?????????????????????????????????????????????????????? stop_sequence ??????????????????????????????
    #     ??????????????????
    def getSeqByTripID(self,inTripID):
        if self.valid==False: return []
        if self.index.trip_id<0: return []
        extracted=self.data[self.data[:,self.index.trip_id]==inTripID]
        records=extracted[np.argsort(extracted[:,self.index.stop_sequence])]
        ret=[]
        n=len(records)
        for i in range(n): ret.append(stop_times_record(records[i]))
        return ret

    def getStartEndRecordsByTime(self,inTripID,inTime):
        tripSeq=self.getSeqByTripID(inTripID)
        n=len(tripSeq)
        targetTime = inTime if isinstance(inTime,Time) else Time(inTime)
        segmentStartRecord=None; segmentEndRecord=None
        found=False
        for i in range(n-1):
            r1=tripSeq[i]   # start segment record
            r2=tripSeq[i+1] # end segment record
            at1,dt1=self.arrivalTimeAndDepartureTime(r1)
            at2,dt2=self.arrivalTimeAndDepartureTime(r2)
            if targetTime<at1 or dt2<targetTime: continue
            segmentStartRecord=r1; segmentEndRecord=r2
            found=True
            break
        if found: return segmentStartRecord,segmentEndRecord
        lastSegmentRecord=tripSeq[n-1]
        lastAt,lastDt=self.arrivalTimeAndDepartureTime(lastSegmentRecord)
        if lastAt<=targetTime and targetTime<=lastDt:
            return lastSegmentRecord,lastSegmentRecord
        return None,None

class stop_times_record(Record): pass


#--------------------------------------------------------------------
# for calendar.txt
#--------------------------------------------------------------------
class calendar(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'calendar.txt',
                         ['service_id','monday','tuesday','wednesday','thursday',
                          'friday','saturday','sunday','start_date','end_date'],
                         'service_id',calendar_record)

class calendar_record(Record): pass


#--------------------------------------------------------------------
# for calendar_dates.txt
#--------------------------------------------------------------------
class calendar_dates(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'calendar_dates.txt',
                         ['service_id','date','exception_type'],
                         'service_id',calendar_dates_record)

    def __getitem__(self,inID):
        records=getitemBody(self,inID)
        if records is None: return None
        ret=[]
        for t in records: ret.append(calendar_dates_record(t))
        return ret

class calendar_dates_record(Record): pass


#--------------------------------------------------------------------
# for fare_attributes.txt
#--------------------------------------------------------------------
class fare_attributes(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'fare_attributes.txt',
                         ['fare_id','price','currency_type',
                          'payment_method','transfers','transfer_duration'],
                         'fare_id',fare_attributes_record)

class fare_attributes_record(Record): pass

#--------------------------------------------------------------------
# for fare_rules.txt
#--------------------------------------------------------------------
class fare_rules(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'fare_rules.txt',
                         ['fare_id','route_id','origin_id',
                          'destination_id','contains_id'],
                         'route_id',fare_rules_record)

    def __getitem__(self,inID):
        records=getitemBody(self,inID)
        if records is None: return None
        ret=[]
        for t in records: ret.append(fare_rules_record(t))
        return ret

class fare_rules_record(Record): pass

#--------------------------------------------------------------------
# for shapes.txt
#--------------------------------------------------------------------
class shapes(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'shapes.txt',
                         ['shape_id','shape_pt_lat','shape_pt_lon',
                          'shape_pt_sequence','shape_dist_traveleded'],
                         'shape_id',shapes_record,
                         optional=True)

    def __getitem__(self,inID):
        records=getitemBody(self,inID)
        if records is None: return None
        records[np.argsort(records[:,self.index.shape_pt_sequence])]
        ret=[]
        for t in records: ret.append(shapes_record(t))
        return ret

    def getShapeArray(self,inShapeID):
        if self.valid==False: return []
        if self.index.shape_id<0: return []
        extracted=self.data[self.data[:,self.index.shape_id]==inShapeID]
        return extracted[np.argsort(extracted[:,self.index.shape_pt_sequence])]

    # [ latitude,longitude ]
    def pos(self,inShape): return [inShape[self.index.shape_pt_lat],
                                   inShape[self.index.shape_pt_lon]]

    def latLon(self,inShape):
         return inShape[self.index.shape_pt_lat],inShape[self.index.shape_pt_lon]

class shapes_record(Record):
    def pos(self): return [self.shape_pt_lat,self.shape_pt_lon]

#--------------------------------------------------------------------
# for frequencies.txt
#--------------------------------------------------------------------
class frequencies(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'frequencies.txt',
                         ['trip_id','start_time','end_time',
                          'headway_secs','exact_times'],
                         'trip_id',frequencies_record,
                         optional=True)

class frequencies_record(Record): pass


#--------------------------------------------------------------------
# for transfers.txt
#--------------------------------------------------------------------
class transfers(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'transfers.txt',
                         ['from_stop_id','to_stop_id',
                          'transfer_type','min_transfer_type'],
                          'from_stop_id',transfers_record,
                          optional=True)

class transfers_record(Record): pass


#--------------------------------------------------------------------
# for feed_info.txt
#--------------------------------------------------------------------
class feed_info(SingleRecord):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'feed_info.txt',
                         ['feed_publisher_name','feed_publisher_url','feed_lang',
                          'feed_start_datefeed_end_date','feed_version'],None)


#--------------------------------------------------------------------
# for translations.txt
#--------------------------------------------------------------------
class translations(RecordSet):
    def __init__(self,inGtfsRootDir):
        super().__init__(inGtfsRootDir,'translations.txt',
                         ['trans_id','lang','translation'],
                          'trans_id',translations_record,
                          optional=True)

class translations_record(Record): pass


#====================================================================
# egGTFS 
#====================================================================
class egGTFS:
    def __init__(self,inGtfsRootDir):
        self.rootDir        =inGtfsRootDir
        self.agency         =agency(inGtfsRootDir)
        self.agency_jp      =agency_jp(inGtfsRootDir)
        self.stops          =stops(inGtfsRootDir)
        self.routes         =routes(inGtfsRootDir)
        self.routes_jp      =routes_jp(inGtfsRootDir)
        self.trips          =trips(inGtfsRootDir)
        self.office_jp      =office_jp(inGtfsRootDir)
        self.stop_times     =stop_times(inGtfsRootDir)
        self.calendar       =calendar(inGtfsRootDir)
        self.calendar_dates =calendar_dates(inGtfsRootDir)
        self.fare_attributes=fare_attributes(inGtfsRootDir)
        self.fare_rules     =fare_rules(inGtfsRootDir)
        self.shapes         =shapes(inGtfsRootDir)
        self.frequencies    =frequencies(inGtfsRootDir)
        self.transfers      =transfers(inGtfsRootDir)
        self.feed_info      =feed_info(inGtfsRootDir)
        self.translations   =translations(inGtfsRootDir)

    def makeName(self,inName):
        beginSpan='<span style="white-space: nowrap;">'
        endSpan='</span>'
        return beginSpan+inName+endSpan

    def getAllStopsMap(self):
        m=folium.Map()
        latMin,latMax=180,0
        lonMin,lonMax=180,0
        for s in self.stops.data:
            pos=self.stops.pos(s)
            folium.Marker(location=pos,
                          popup=self.makeName(self.stops.name(s))).add_to(m)
            latMin,latMax=min(latMin,pos[0]),max(latMax,pos[0])
            lonMin,lonMax=min(lonMin,pos[1]),max(lonMax,pos[1])
        m.fit_bounds([[latMin,lonMin],[latMax,lonMax]])
        return m

    def getAllStopsDensityMap(self,radius=8,blur=3):
        m=folium.Map()
        latMin,latMax=180,0
        lonMin,lonMax=180,0
        posList=[]	
        for s in self.stops.data:
            pos=stops.pos(s)
            posList.append(pos)
            latMin,latMax=min(latMin,pos[0]),max(latMax,pos[0])
            lonMin,lonMax=min(lonMin,pos[1]),max(lonMax,pos[1])
        HeatMap(posList,radius=4,blur=3).add_to(m)
        m.fit_bounds([[latMin,lonMin],[latMax,lonMax]])
        return m

    def getShapeMap(self,inShapeID):
        m=folium.Map()
        latMin,latMax=180,0
        lonMin,lonMax=180,0
        shapesRecord=self.shapes[inShapeID]
        points=[]
        for s in shapesRecord:
            pos=s.pos()
            points.append(pos)
            latMin,latMax=min(latMin,pos[0]),max(latMax,pos[0])
            lonMin,lonMax=min(lonMin,pos[1]),max(lonMax,pos[1])
        folium.PolyLine(points).add_to(m)
        m.fit_bounds([[latMin,lonMin],[latMax,lonMax]])
        return m

    def getStopPosSeqByTripID(self,inTripID):
        stopTimeSeq=self.stop_times.getSeqByTripID(inTripID)
        if len(stopTimeSeq)==0: return []
        result=[]
        for t in stopTimeSeq:
            stop=self.stops.getByStopID(t[self.stop_times.index.stop_id])
            result.append(stop)
        return result

    def getShapeIdByTripID(self,inTripID):
        trip=self.trips[inTripID]
        return trip.shape_id if trip!=None else None

    def getTripMap(self,inTripID):
        m=folium.Map()
        latMin,latMax=180,0
        lonMin,lonMax=180,0
        shapeID=self.getShapeIdByTripID(inTripID)
        shapeArray=self.shapes.getShapeArray(shapeID)
        points=[]
        for s in shapeArray:
            pos=self.shapes.pos(s)
            points.append(pos)
            latMin,latMax=min(latMin,pos[0]),max(latMax,pos[0])
            lonMin,lonMax=min(lonMin,pos[1]),max(lonMax,pos[1])
        folium.PolyLine(points).add_to(m)

        stopArray=self.stop_times.getSeqByTripID(inTripID)
        for s in stopArray:
            stopID=s.stop_id
            latLon=self.stops.getPosByStopID(stopID)
            folium.Marker(location=latLon,popup=self.makeName(self.stops.getNameByStopID(stopID))).add_to(m)
            latMin,latMax=min(latMin,latLon[0]),max(latMax,latLon[0])
            lonMin,lonMax=min(lonMin,latLon[1]),max(lonMax,latLon[1])

        m.fit_bounds([[latMin,lonMin],[latMax,lonMax]])
        return m

    def getBusPos(self,inTripID,inHour_or_TimeStr,inMinute=None,inSecond=None,
                  epsilon=0.00003):
        if self.shapes.valid==False or self.shapes.hasRecord==False: return None
        if isinstance(inHour_or_TimeStr,str):
            targetTime=Time(inHour_or_TimeStr)
        else:
            targetTime=Time(inHour_or_TimeStr,inMinute,inSecond)
        trip=self.trips[inTripID]
        if trip==None: raise ValueError('no such a trip ID')

        stopTimes=self.stop_times[inTripID]
        if stopTimes==None: raise ValueError('invalid GTFS-JP (no such a stop_times)')
        numOfStopTimes=len(stopTimes)
        if numOfStopTimes==0: raise ValueError('invalid GTFS-JP (zero stop_times)')

        tripStartTime=Time(stopTimes[ 0].arrival_time)
        tripEndTime  =Time(stopTimes[-1].departure_time)

        # for debug
        #print('START:'+str(tripStartTime))
        #print('END  :'+str(tripEndTime))
        #print('TARGET:'+str(targetTime))

        if targetTime<tripStartTime or tripEndTime<targetTime: return None

        if trip.shape_id==None: raise ValueError('no shape ID')
        shapeID=trip.shape_id
        shapes=self.shapes[shapeID]
        if shapes==None: raise ValueError('invalid GTFS-JP (no such a shape ID)')

        for stop in stopTimes:
            if Time(stop.arrival_time)<=targetTime<=Time(stop.departure_time):
                return self.getPosByStopID(stop.stop_id)

        targetStopSegmentIndex=self.getStopIdSegmentIndex(stopTimes,targetTime)
        if targetStopSegmentIndex==None:
            raise ValueError('invalid GTFS-JP (stop_times may be corrupt.')

        segmentStartTime=Time(stopTimes[targetStopSegmentIndex  ].departure_time)
        segmentEndTime  =Time(stopTimes[targetStopSegmentIndex+1].arrival_time)

        startStopPos=self.getPosByStopID(stopTimes[targetStopSegmentIndex].stop_id)
        endStopPos  =self.getPosByStopID(stopTimes[targetStopSegmentIndex+1].stop_id)
        #print('start stop pos='+str(startStopPos))
        #print('end stop pos  ='+str(endStopPos))
        #print('start stop='+str(self.stops[stopTimes[targetStopSegmentIndex].stop_id]))
        #print('end   stop='+str(self.stops[stopTimes[targetStopSegmentIndex+1].stop_id]))

        targetSegmentPosList=self.getTargetSegmentPosList(shapes,startStopPos,endStopPos,epsilon=epsilon)
        # print('targetSegmentPosList='+str(targetSegmentPosList))

        shapeTripDistance=self.getPosListDistance(targetSegmentPosList)
        # print('shape trip distance[m]='+str(shapeTripDistance))

        distanceRatio=(targetTime-segmentStartTime).totalSecond/(segmentEndTime-segmentStartTime).totalSecond
        ret=self.getPosOnPosList(targetSegmentPosList,shapeTripDistance*distanceRatio)
        return ret

    def getPosByStopID(self,inStopID): return self.stops.getPosByStopID(inStopID)

    # inTargetTime ???????????????????????????????????????????????????????????????????????????????????? n ????????????
    # targetTime in [n,n+1]
    def getStopIdSegmentIndex(self,inStopTimes,inTargetTime):
        n=len(inStopTimes)
        for i in range(n-1):
            t1=Time(inStopTimes[i].arrival_time)
            t2=Time(inStopTimes[i+1].departure_time)
            if t1<=inTargetTime<=t2: return i
        return None
            
    def getTargetSegmentPosList(self,inShapes,inStartPos,inEndPos,epsilon=0.00003):
        if inShapes[-1].shape_pt_lat==inStartPos[0] and inShapes[-1].shape_pt_lon==inStartPos[1]:
            raise ValueError('invalid shapes or inStartPos')

        ret=[]
        n=len(inShapes)

        p,startIndex=self.getNearestPos(inShapes,inStartPos,epsilon=epsilon)
        if p!=None:
            ret.append(p)
        else:
            startIndex=self.getNearestShapePointIndex(inShapes,0,inStartPos)
            ret.append(inStartPos)

        if startIndex>=n: raise ValueError('invalid shapes')
        #print('segment start shape index='+str(startIndex))

        #t=self.isShapePoint(inShapes,inEndPos,searchFrom=startIndex,epsilon=epsilon) 
        #if startIndex<=t<n:
        #    for i in range(startIndex+1,t):
        #        ret.append([inShapes[i].shape_pt_lat,inShapes[i].shape_pt_lon])
        #    ret.append(inEndPos)
        #    return ret
        
        p,t=self.getNearestPos(inShapes,inEndPos,searchFrom=startIndex,epsilon=epsilon)
        if p==None: t=self.getNearestShapePointIndex(inShapes,startIndex,inEndPos)
        for i in range(startIndex+1,t+1):
            ret.append([inShapes[i].shape_pt_lat,inShapes[i].shape_pt_lon])
        #print('segment end shape index='+str(t))
        if ret[-1]!=inEndPos: ret.append(inEndPos)
        return ret

    def getNearestShapePointIndex(self,inShapes,inSearchStartIndex,inPos):
        dLat=inShapes[inSearchStartIndex].shape_pt_lat-inPos[0]
        dLon=inShapes[inSearchStartIndex].shape_pt_lon-inPos[1]
        minDist2=dLat*dLat+dLon*dLon
        nearestIndex=inSearchStartIndex
        n=len(inShapes)
        for i in range(inSearchStartIndex+1,n):
            dLat=inShapes[i].shape_pt_lat-inPos[0]
            dLon=inShapes[i].shape_pt_lon-inPos[1]
            d2=dLat*dLat+dLon*dLon
            if d2<minDist2:
                minDist2=d2
                nearestIndex=i
        return nearestIndex

    # shapes ?????????????????????????????????????????????????????????????????????????????????
    # ?????????????????? -1 ????????????
    # default epsilon 0.00001 (??? 1m???
    def isShapePoint(self,inShapes,inPos,searchFrom=0,epsilon=0.00001):
        n=len(inShapes)
        e2=epsilon*epsilon
        for i in range(searchFrom,n):
            dLat=inPos[0]-inShapes[i].shape_pt_lat
            dLon=inPos[1]-inShapes[i].shape_pt_lon
            d2=dLat*dLat+dLon*dLon
            if d2<e2: return i
        return -1
            
    # return pos,startSegmentIndex
    # epsilon ?????????????????????????????????????????????????????????
    # ????????? 1 ??????????????????????????? 111 km = 111000 ????????? 10 ???m
    # ?????? 35 ??????????????? 1 ???????????????????????? 91 km ????????? 9 ???m ????????????
    # 10 ????????? 1 ?????? 1 m ???????????????????????????????????????
    # ????????????????????? 0.00003 ????????? ??3 m ???????????????????????????????????????
    def getNearestPos(self,inShapes,inPos,epsilon=0.00003,searchFrom=0):
        n=len(inShapes)
        minDist=abs(epsilon*10)
        nearestRelatedIndex=-1
        nearestPos=None
        tx=inPos[0]
        ty=inPos[1]
        #print('searchFrom='+str(searchFrom))
        for i in range(searchFrom,n-1):
            p1=[inShapes[i  ].shape_pt_lat,inShapes[i  ].shape_pt_lon]
            p2=[inShapes[i+1].shape_pt_lat,inShapes[i+1].shape_pt_lon]
            p,d=getNearestPosOnSegment(p1[0],p1[1],p2[0],p2[1],tx,ty)
            if p!=None and d<minDist:
                #print('updated!',p1[0],p1[1],p2[0],p2[1],tx,ty)
                #print('isOnSegment='+str(isOnSegment(p1[0],p1[1],p2[0],p2[1],tx,ty)))
                #print('update dist from='+str(minDist)+' to='+str(d))
                minDist,nearestRelatedIndex,nearestPos=d,i,p

        #if minDist<epsilon:
        #    print('target point ='+str(inPos))
        #    print('segment start='+str(inShapes[nearestRelatedIndex]))
        #    print('segment end  ='+str(inShapes[nearestRelatedIndex+1]))
        #    print('dist         ='+str(minDist))

        if minDist<epsilon: return nearestPos,nearestRelatedIndex
        # print('no nearest pos minDist='+str(minDist))
        return None,-1

    # ??????????????? [[lat1,lon1],[lat2,lon2],...]  ????????????????????????????????????????????????
    def getPosListDistance(self,inPosList):
        n=len(inPosList)
        ret=0
        for i in range(n-1): ret+=geodesic(inPosList[i],inPosList[i+1]).m
        return ret

    # inTargetDistance ??????????????????????????????????????????
    def getPosOnPosList(self,inPosList,inTargetDistance):
        if self.getPosListDistance(inPosList)<inTargetDistance:
            raise ValueError('inPosList is shorter than inTargetDistance.')
        rest=inTargetDistance
        n=len(inPosList)
        for i in range(n-1):
            d=geodesic(inPosList[i],inPosList[i+1]).m
            if rest>d:
                rest-=d
                continue
            else:
                break
        if d==rest: return inPosList[i+1]
        t=rest/d
        dLat=inPosList[i+1][0]-inPosList[i][0]
        dLon=inPosList[i+1][1]-inPosList[i][1]
        lat=t*dLat+inPosList[i][0]
        lon=t*dLon+inPosList[i][1]
        return [lat,lon]


def open(inGtfsRootDir):
    if os.path.exists(inGtfsRootDir)==False:
        raise FileNotFoundError("ERROR: no such GTFS root dir '"+inGtfsRootDir+"'")
    return egGTFS(inGtfsRootDir)

def isArray(x): return hasattr(x,'__len__')

def getMapImage(inURL,pngFileName='screenshot.png',width=800,height=800):
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get(inURL)
    driver.set_window_size(width,height)
    driver.save_screenshot(pngFileName)
    driver.quit()

