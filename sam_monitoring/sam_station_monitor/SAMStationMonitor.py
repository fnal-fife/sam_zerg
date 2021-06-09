
import os, sys, time,threading, logging, csv, cStringIO, itertools, math, json
from datetime import datetime,timedelta
import string

import cherrypy
try:
    from cherrypy.lib import httputil
except ImportError:
    from cherrypy.lib import http as httputil
from cherrypy.lib import cptools
from mako.template import Template
from mako.lookup import TemplateLookup

from StationProjectInfo import StationInfo,ProjectInfo,InfoException, dbpool, localtimezone, utctimezone, epoch

def makeJSTime(dt):
    return long(1000*(dt-epoch).total_seconds())

def combine_string_iterable(iterable, minlen=(15*1024)):
    """ Take a iterable over strings, and yield them joined so that each
    output is at least minlen in length (except for the last) """
    if isinstance(iterable, basestring):
        # if the iterable is a string, just dump the whole thing out
        yield iterable
        return

    strings = []
    curlen = 0
    for i in iterable:
        strings.append(i)
        curlen+=len(i)
        if curlen>=minlen:
            yield ''.join(strings)
            strings = []
            curlen = 0
    # output any trailing stuff
    if strings:
        yield ''.join(strings)

_templates = TemplateLookup(directories='./templates')

# Set the page expiry time in seconds
page_expire_seconds = 60

class PeriodicDBQuery(cherrypy.process.plugins.SimplePlugin):
    def __init__(self, bus, site, stationnames):
        cherrypy.process.plugins.SimplePlugin.__init__(self, bus)
        self.thread = None
        self.site = site
        self.stationnames = stationnames

    def start(self):
        if self.thread is None:
            cherrypy.log("starting thread for %s" % self.site, context='dbthread', severity=logging.DEBUG)
            self.thread = DBQueryThread(self.site, self.stationnames)
            self.thread.start()

    def stop(self):
        if self.thread is not None:
            cherrypy.log("stopping thread", context='dbthread', severity=logging.DEBUG)
            self.thread.cancel()
            self.thread.join()
            self.thread = None

    def getAllStations(self):
        if self.thread is not None:
            return self.thread.getAllStations()
        else: return []

    def getStation(self, station):
        station = self.thread.stations[station]
        return station

    def getProject(self, station, project):
        return self.getStation(station).getProject(project)

    def getProcess(self, station, project, processid):
        return self.getProject(station,project).processes[processid]

class DBQueryThread(threading.Thread):
    def __init__(self,site,stationnames):
        threading.Thread.__init__(self)
        self.site = site
        self.stations = {}
        self.stationnames = stationnames
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.finished=False

    def run(self):
        # first query
        for s in self.stationnames:
            self.stations[s] = StationInfo(self.site,s)

        while True:
            for s in self.stations:
                sinfo = self.stations[s]
                try:
                    sinfo.update(fullupdate=True)
                except:
                    # can't do much here except wait for the next update
                    cherrypy.log("Exception while querying station %s" % (s,), context='dbthread', severity=logging.ERROR, traceback=True)
            # Calculate time to next 30 min boundary (more than 15 mins ahead)
            nextrun = (datetime.now() + timedelta(minutes=45)).replace(second=0,microsecond=0)
            nextrun = nextrun.replace(minute = nextrun.minute - (nextrun.minute % 30))
            cherrypy.log("DB query for %s completed, waiting until %s" % (self.site,nextrun), context='dbthread', severity=logging.DEBUG, traceback=False)   
            self.lock.acquire()
            try:
                while( not self.finished and datetime.now() < nextrun):
                    waittime= nextrun-datetime.now()
                    waitsecs = waittime.seconds + waittime.microseconds/1000000.0
                    #cherrypy.log("waiting %s seconds" % waitsecs, context='dbthread')
                    self.cond.wait(waitsecs)
                if self.finished: return 
            finally:
                self.lock.release()

    def cancel(self):
        self.lock.acquire()
        self.finished = True
        self.cond.notifyAll()
        self.lock.release()

    def getAllStations(self):
        stations = []
        for s in self.stationnames:
            sinfo = self.stations.get(s)
            if sinfo is not None: stations.append(sinfo)
        return stations

class StationHandler(object):

    def __init__(self, stationname, monitor):
        self.stationname = stationname
        self.monitor = monitor
        self._cache = {}
        self.lock = threading.Lock()

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('projects')

    @cherrypy.expose
    def projects(self, projectname=None, group=None, value=None, **params):
        lock = None
        if group is not None:
            if group == 'processes':
                try: processid = long(value)
                except (ValueError, TypeError): raise cherrypy.NotFound()
            elif group == 'plots':
                return self._makePlotData(projectname,value)
            else:
                raise cherrypy.NotFound()
        else:
            processid = None
        templateargs = self.monitor.getTemplateArgs()
        try:
            stationinfo = self.monitor.dbquery.getStation(self.stationname)
        except KeyError: return self.monitor.errorPage("Station '%s' not found" % self.stationname)
        templateargs['stationinfo'] = stationinfo
        if projectname is None:
            stationinfo.update()
            template = _templates.get_template('station-projects.html') 
            now = datetime.now(localtimezone)
            def _nprocs(p):
                if p.invalid: return -1
                else: return len(p.processes)
            sortkeys = {
                'name' : lambda p: p.name,
                'id' : lambda p: p.id,
                'owner' : lambda p: p.owner,
                'status' : lambda p: p.status,
                'snapfiles' : lambda p: p.fileCount,
                'seenfiles' : lambda p: p.filesSeen,
                'nprocs' : _nprocs,
                'nwait' : ProjectInfo.countWaitingProcesses,
                'lastactivity' : lambda p: p.lastActivityTime,
                'longestwait' : lambda p: now - (p.longestWaitingProcess()[0] or now),
                'medianwait' : lambda p: p.getMedianTimes()[0] or timedelta(-1),
                'mediantransfer' : lambda p: p.getMedianTimes()[1] or timedelta(-1),
                'medianbusy' : lambda p: p.getMedianTimes()[2] or timedelta(-1),
                }
            templateargs['sorttype'] = params.get('sort','id')
            templateargs['sortkey'] = sortkeys[templateargs['sorttype']]
            templateargs['sortorder'] = params.get('order','asc')

            try:
                showcompleted = bool(int(params.get('completed',0)))
            except ValueError: showcompleted = False
            templateargs['showcompleted'] = showcompleted

            # lock at the project list level
            lock = templateargs['stationinfo'].projectslock
            
        else:
            try:
                projectinfo = self.monitor.dbquery.getProject(self.stationname, projectname)
            except KeyError: return self.monitor.errorPage("Project '%s' not found" % projectname)
            templateargs['projectinfo']  =projectinfo
            lock = projectinfo.lock
            if processid is None:
                if len(projectinfo.processes) > 50000: raise cherrypy.HTTPError(413, "Project %s has %d processes which is more than this server can display" % (projectname, len(projectinfo.processes)))
                elif projectinfo.invalid: raise cherrypy.HTTPError(413, "Project %s has too many processes for the monitoring to work correctly" % (projectname, ))
                template = _templates.get_template('project.html')
            else:
                try:
                    processinfo = self.monitor.dbquery.getProcess(self.stationname, projectname, processid)
                except KeyError: return self.monitor.errorPage("Process %d not found" % processid)

                templateargs['processinfo'] = processinfo
                template = _templates.get_template('process.html')
                
        # Make sure we acquire a lock while rendering
        if lock is not None:
            lock.acquire()
        try:
            return template.render(**templateargs)
        finally:
            if lock is not None: lock.release()

    @cherrypy.expose
    def process_wait_history_json(self):
        try:
            stationinfo = self.monitor.dbquery.getStation(self.stationname)
        except KeyError: return self.monitor.errorPage("Station '%s' not found" % self.stationname)
        with self.lock:
            cherrypy.response.headers['Last-Modified'] = httputil.HTTPDate(time.mktime(stationinfo.summaryupdatetime.timetuple()))
            cptools.validate_since()
            # output: time, nwaiting, nactive, median wait
            waithistory = [ (makeJSTime(tm), wt, ac, md if md else 0.0) for (tm, wt, ac, md) in stationinfo.waithistory ]

            cherrypy.response.headers['Content-Type'] = 'text/json'
            return json.dumps(waithistory)

    @cherrypy.expose
    def processes(self):
        templateargs = self.monitor.getTemplateArgs()
        try:
            templateargs['stationinfo'] = self.monitor.dbquery.getStation(self.stationname)
        except KeyError: return self.monitor.errorPage("Station '%s' not found" % self.stationname)
        template = _templates.get_template('station-processes.html')
        return template.render(**templateargs)

    def _makePlotData(self,projectname,plot):
        try:
            projectinfo = self.monitor.dbquery.getProject(self.stationname, projectname)
        except KeyError: raise cherrypy.NotFound()
        projectinfo.lock.acquire()
        try:
            if plot == 'waittimes.csv':
                cherrypy.response.headers['Content-Type'] = 'text/csv'
                return self._makeHisto([ d.total_seconds()/60.0 for d in projectinfo.waittimes], "waittime", minval=0)
            elif plot == 'transfertimes.csv':
                cherrypy.response.headers['Content-Type'] = 'text/csv'
                return self._makeHisto([ d.total_seconds()/60.0 for d in projectinfo.transfertimes], "transfertime", minval=0)
            elif plot == 'busytimes.csv':
                cherrypy.response.headers['Content-Type'] = 'text/csv'
                return self._makeHisto([ d.total_seconds()/60.0 for d in projectinfo.busytimes], "busytime", minval=0)
            elif plot == 'processes.json':
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return self._makeProjectDeliveryHistory(projectinfo)
            else:
                raise cherrypy.NotFound()
        finally:
            projectinfo.lock.release()

    def _makeHisto(self, data, label,minval=None,maxval=None):
        out= cStringIO.StringIO()
        writer = csv.writer(out)
        writer.writerow([ label, "frequency" ])
        k = int( 2*len(data)**(1.0/3) + 0.5) # this is the "Rice rule for histogram bins"
        minval, maxval = float("inf") if minval is None else float(minval), float("-inf") if maxval is None else float(maxval)
        for v in data:
            if v < minval: minval = v
            if v > maxval: maxval = v
        # round off the max and min
        ndigits = int(round(math.log( maxval - minval )/math.log(10)))
        maxval = round(maxval + 0.4999*10**ndigits, -ndigits)
        minval = round(minval - 0.4999*10**ndigits, -ndigits)

        range = maxval - minval
        binwidth = range/k
        bins = [ minval + i*binwidth for i in xrange(k) ]
        bindata = [0] * k
        for v in data:

            idx = int(k*(v-minval)/range)
            try:
                bindata[idx]+=1
            except IndexError:
                # assume overflow due to precision
                bindata[-1]+=1
        writer.writerows( itertools.izip(bins, bindata) )
        writer.writerow( [ maxval, 0 ] ) # An extra to provide the upper bound
        return out.getvalue()

    def _makeProjectDeliveryHistory(self, projectinfo):
        processes = []
        for p in projectinfo.processes.itervalues():
            process = { "process_id":p.id,
                        "start_time" : makeJSTime(p.startTime),
                        "end_time" : makeJSTime(p.endTime) if p.endTime else None,
                        "status" : p.status,
                        "description" : p.description,
                        "node_name" : p.nodeName,
                        }
            process['files'] = [ {"file_id" : f.id, "file_name" : f.name, "status" : f.status,
                "close_time" : makeJSTime(f.closeTime) if f.closeTime else None,
                "transfer_time" : makeJSTime(f.transferTime) if f.transferTime else None,
                "completed_time" : makeJSTime(f.completedTime) if f.completedTime else None,
                "open_time" : makeJSTime(f.openTime),
                "waited_for" : f.waitedFor.total_seconds() if f.waitedFor is not None else None,
                "transferred_for" : f.transferredFor.total_seconds() if f.transferredFor is not None else None,
                "busy_for" : f.busyFor.total_seconds() if f.busyFor is not None else None} for f in p.files ]

            processes.append(process)

        cherrypy.response.stream = True
        return combine_string_iterable(json.JSONEncoder().iterencode(processes))

class Stations(object):
    def __init__(self,monitor,stationnames):
        # create handlers for each station we know about
        self.monitor = monitor
        for s in stationnames:
            setattr(self,s.replace('-','_'),StationHandler(s,monitor))

    @cherrypy.expose
    def index(self):
        index_template = _templates.get_template('stations.html')
        templateargs = self.monitor.getTemplateArgs()
        return index_template.render(stations=self.monitor.dbquery.getAllStations(),**templateargs)

    @cherrypy.expose
    def debug(self):
        return "<pre> %s </pre>" % repr(self.__dict__).replace('<','&lt;')

class StationMonitor(object):

    # Add an expires header (inherited by handlers down the tree)
    _cp_config = {'tools.expires.on' : True,
                  'tools.expires.secs' : page_expire_seconds}

    def __init__(self, display_name, base_path, site, config ):
        
        self.site = site

        stationnames = config['stations'].split()
        dbconnect = config['postgres_connect']
        dbpool.addPool(self.site,dbconnect)        

        # handler for the stations
        self.stations = Stations(self,stationnames)
        
        self.waitwarntime = timedelta(minutes=60)
        self.templateargs = { 'base_path' : base_path,
                              'site' : site,
                              'site_display_name' : display_name,
                              'waitwarntime' : self.waitwarntime }

        self.dbquery = PeriodicDBQuery(cherrypy.engine, self.site,stationnames)
        self.dbquery.subscribe()

    def getTemplateArgs(self):
        return self.templateargs.copy()

    def errorPage(self,msg):
        template = _templates.get_template('error.html')
        return template.render(errormsg=msg,**self.getTemplateArgs())
    
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('stations/')

class SAMStationMonitor(object):

    def __init__(self):
        pass

    def start(self, app):
        self.sites = app.config['SAMStationMonitor']['monitor'].split()
        self.site_data = {}
        for site in self.sites:
            config = app.config[site]
            display_name = config.get('display_name',site)
            path = config.get('path',site)
            self.site_data[site] = (display_name, path)
            monitor = StationMonitor(display_name, app.script_name, path, config)
            setattr(self, path, monitor)

    @cherrypy.expose
    def index(self):
        if len(self.sites) == 1:
            path = list(self.site_data.values())[0][1]
            raise cherrypy.HTTPRedirect(path)
        else:
            template = _templates.get_template('top_level.html')
            return template.render(base_path=cherrypy.request.app.script_name, sites=self.sites, site_data = self.site_data)
