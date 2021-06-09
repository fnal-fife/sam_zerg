#! /usr/bin/env python

import thread,threading
import time
import collections
import psycopg2
from time_functions import localtimezone, utctimezone, epoch
import cherrypy
from datetime import datetime,timedelta
import logging

def median(i):
    data = list(i)
    if not data:
        return None
    if len(data) == 1:
        return data[0]
    data.sort()
    if len(data) % 2 == 0:
        # even
        return (data[ (len(data)//2)-1 ] + data[(len(data)//2) ]) / 2
    else:
        # odd
        return data[ len(data) // 2 ]

class InfoException(Exception): pass

class StationInfoException(InfoException): pass
class ProjectInfoException(InfoException): pass
class ProjectNotFound(ProjectInfoException): pass

# simple thread local connection pool.
# connections must be released in the same thread that they were acquired
class DBConnectionPool(object):
    def __init__(self):
        self.pools = {}

    def addPool(self, key, connectinfo):
        self.pools[key] = DBLocalConnectionPool(connectinfo)

    def getLocalPool(self, key):
        return self.pools[key]

    def get(self, key):
        return self.pools[key].get()

    def release(self,key):
        return self.pools[key].release()

class Watchdog(threading.Thread):
    def __init__(self, interval, callback):
        threading.Thread.__init__(self)
        self.daemon = True
        self.target = time.time()+interval
        self.callback = callback
        self.terminate = False
        self.cond = threading.Condition()

    def run(self):
        self.cond.acquire()
        try:
            while True:
                if self.terminate: return
                sleeptime = self.target - time.time()
                if sleeptime <= 0: break
                self.cond.wait(sleeptime)
        finally:
            self.cond.release()

        self.callback()

    def cancel(self):
        self.cond.acquire()
        self.terminate = True
        self.cond.notify()
        self.cond.release()

    def reset(self, newinterval):
        self.cond.acquire()
        self.target = time.time() + newinterval
        self.cond.notify()
        self.cond.release()

class DBLocalConnectionPool(object):

    dbtimeout = 15*60

    def __init__(self, connectinfo):
        self.connectinfo = connectinfo
        self.local = threading.local()

    def get(self):
        try:
            self.local.conn
        except AttributeError:
            self.local.conn = None
            self.local.count = 0
            self.local.watchdog = None
        if self.local.conn is None:
            self.local.conn = psycopg2.connect(self.connectinfo)
            cur = self.local.conn.cursor()

            # we're going to use cursors, but we always want to read all the data
            #cur.execute('set session cursor_tuple_fraction = 1.0')
            #self.local.conn.commit()

            self.local.count = 1
            self.local.watchdog = Watchdog(self.dbtimeout,self.cancel)
            self.local.watchdog.start()
	    #cherrypy.log('Opened DB connection for thread %s, use count %s' % (thread.get_ident(), self.local.count),
            #    context='DBLocalConnectionPool', severity=logging.DEBUG, traceback=False)
        else:
            self.local.count+=1
            self.local.watchdog.reset(self.dbtimeout)
        return self.local.conn

    def cancel(self):
         # cancel any running transaction, and close the connection
         try:
            if self.local.conn is not None:
                self.local.conn.cancel()
                self.local.conn.close()
         except Exception: pass
         self.local.conn = None

    def release(self):
        try:
            # roll back connection to clear temp table
            self.local.conn.rollback()
        except Exception: pass
        self.local.count-=1
        if self.local.count == 0:
	    #cherrypy.log('Closing DB connection for thread %s, use count %s' % (thread.get_ident(), self.local.count),
            #         context='DBLocalConnectionPool', severity=logging.DEBUG, traceback=False)
            try:
		#cherrypy.log('%s' % self.local.conn, context='DBLocalConnectionPool', severity=logging.DEBUG)
                self.local.conn.close()
		#cherrypy.log('closed', context='DBLocalConnectionPool', severity=logging.DEBUG)
            except Exception:
		cherrypy.log('Exception while closing DB connection', context='DBLocalConnectionPool', severity=logging.DEBUG, traceback=True)
            self.local.conn = None
            self.local.watchdog.cancel()
            self.local.watchdog = None

dbpool = DBConnectionPool()

class FileInfo(object):
    __slots__ = ('id', 'name', 'status', 'closeTime', 'transferTime', 'openTime', 'waitedFor', 'transferredFor', 'busyFor', 'processId', 'completedTime')

    def __init__(self, fileId, fileName, status, closeTime, transferTime, openTime, processid, completedTime):
        self.id = fileId
        self.name = fileName
        self.status = status
        self.closeTime = closeTime
        self.transferTime = transferTime
        self.openTime = openTime
        self.waitedFor = None
        self.transferredFor = None
        self.busyFor = None
        self.processId = processid
        self.completedTime = completedTime

class ProcessInfo(object):
    __slots__ = ('project', 'id', 'nodeName', 'startTime', 'endTime', 'completedTime', \
        'description', 'files', 'waittimes', 'transfertimes', 'busytimes', 'updatetime', 'status')

    def __init__(self, updatetime, project, process_id, node_name, process_status, start_time, 
                 end_time, completed_time, process_desc):
        self.project = project
        self.id = process_id
        self.nodeName = node_name
        
        self.startTime = start_time
        self.description = process_desc
        self.update(updatetime,process_status, end_time, completed_time)

        self.files = []

        self.waittimes = []
        self.transfertimes = []
        self.busytimes = []

    def clearFileInfo(self):
        self.files = []
        self.waittimes = []
        self.transfertimes = []
        self.busytimes = []

    def update(self, updatetime, process_status, end_time, completedTime):
        self.updatetime = updatetime
        self.status = process_status
        # The DB only stores times to 1 s resolution. To make sure the end date comes after any other
        # activity, add a fudge factor
        if end_time and self.status not in ('active','idle'):
            self.endTime = end_time + timedelta(microseconds=50)
        else:
            self.endTime = None
        if completedTime and self.status == 'completed':
            self.completedTime = completedTime+ timedelta(microseconds=50)
        else:
            self.completedTime = None

    def __lt__(self, other):
        return self.id < other.id

    def isWaiting(self):
        if self.status != 'active' or self.project.hasAllFiles():
            return False
        if self.files:
            return self.files[-1].status not in ('delivered','transferred')
        else: return True

    def isBusy(self):
        if self.status != 'active':
            return False
        if self.files:
            return self.files[-1].status in ('delivered','transferred')
        else: return False

    def isError(self):
        return self.status in ('error','bad')

    def isFinished(self):
        return self.status in ('finished','completed')

    def isActive(self):
        return self.status in ('active', ) and not self.project.hasAllFiles()

    def isCancelled(self):
        return self.status == 'cancelled'

    def lastFile(self):
        if self.files:
            return self.files[-1]
        else: return None

    def lastStateChange(self):
        if self.endTime:
            return self.endTime, 'process ended - %s' % self.status
        f = self.lastFile()
        if f:
            if f.closeTime is None:
                return f.openTime, f.status
            return f.closeTime, f.status
        else:
            return self.startTime, 'process started'

    def getEndTime(self):
        return self.endTime

    def getCompletedTime(self):
        return self.completedTime
    
    def getMedianTimes(self):
        if self.waittimes:
            tmp_waittimes = sorted(self.waittimes)
            medianwait = median(tmp_waittimes) 
        else:
            medianwait = None

        if self.transfertimes:
            tmp_transfertimes = sorted(self.transfertimes)
            mediantransfer = median(tmp_transfertimes)
        else:
            mediantransfer = None

        if self.busytimes:
            tmp_busytimes = sorted(self.busytimes)
            medianbusy = median(tmp_busytimes)
        else:
            medianbusy = None
        return medianwait, mediantransfer, medianbusy


    def calcFileTimes(self):
        waitstart = self.startTime
        for f in self.files:
            wait = f.openTime - waitstart
            self.waittimes.append(wait)
            f.waitedFor = wait
            if f.closeTime:
                if f.transferTime:
                    busytime = f.closeTime - f.transferTime
                    xfer_time = f.transferTime - waitstart
                    f.transferredFor = xfer_time
                    self.transfertimes.append(xfer_time)
                else:
                    busytime = f.closeTime - f.openTime
                self.busytimes.append(busytime)
                f.busyFor = busytime
            waitstart = f.closeTime or f.openTime
        # if the last state is error, then this overestimates the waiting, since we don't
        # really know when it exited
        if self.endTime:
            # if no files were ever delivered, or the last file was not being processed, add the wait before the job exits
            if not self.files or (self.files and self.files[-1].status not in ('delivered', 'transferred')):
                endwaittime = self.endTime - waitstart
                # want to ignore any small wait time at the end of the job
                # - it might just be time between polling
                if endwaittime > timedelta(minutes=1):
                    self.waittimes.append(endwaittime)
                

class ProjectInfo(object):
    def __init__(self, station, project_name):

        self.station=station
        self.lock = threading.Lock()
        self.updatetime = None
        self.id = None
        self.name = project_name
        self.owner = None
        self.status = None
        self.startTime = None
        self.endTime = None
        self.datasetDef = None
        self.projSnapId = None
        self.fileCount = None
        self.lastActivityTime = None
        self.lastStatus = None
        self.lastFileName = None
        self.filesSeen = 0
        self.files = []

        self.processes = {}
        self.invalid = False

        self.complete = False # set when we have all info and there's no need to get more
        self.update()

    def update(self):
        self.lock.acquire()
        try:
            # don't query the db too often
            if self.updatetime and datetime.now(localtimezone)<self.updatetime+timedelta(minutes=1):
                return
            self.updatetime = datetime.now(localtimezone)
            try:
                self._queryDB()
            except psycopg2.Error, ex:
                cherrypy.log('DB query failed', traceback=True)
                raise ProjectInfoException(str(ex))
        finally:
            self.lock.release()

    def getWaitTimes(self):
        waits = []
        for p in self.processes.itervalues():
            waits+=p.waittimes
        return waits
    waittimes = property(getWaitTimes)

    def getTransferTimes(self):
        transfers = []
        for p in self.processes.itervalues():
            transfers+=p.transfertimes
        return transfers
    transfertimes = property(getTransferTimes)

    def getBusyTimes(self):
        busies = []
        for p in self.processes.itervalues():
            busies+=p.busytimes
        return busies
    busytimes = property(getBusyTimes)

    def isRunning(self):
        return self.status == 'running'

    def countWaitingProcesses(self):
        return len([p for p in self.processes.itervalues() if p.isWaiting()])

    def countBusyProcesses(self):
        return len([p for p in self.processes.itervalues() if p.isBusy()])

    def countErrorProcesses(self):
        return len([p for p in self.processes.itervalues() if p.isError()])

    def countFinishedProcesses(self):
        return len([p for p in self.processes.itervalues() if p.isFinished()])

    def countActiveProcesses(self):
        return len([p for p in self.processes.itervalues() if p.isActive()])

    def countCancelledProcesses(self):
        return sum(1 for p in self.processes.itervalues() if p.isCancelled())

    def getProcesses(self):
        return sorted(self.processes.itervalues())

    def hasAllFiles(self):
        return self.filesSeen == self.fileCount

    # get the last activity time of the longest waiting process
    def longestWaitingProcess(self):
        oldesttime = None
        oldeststate = None
        processes = self.processes.values()
        #if not processes:
        #    return self.startTime, 'project started'
        for p in processes: 
            if p.isWaiting():
                ptime, pstate = p.lastStateChange()
                if not oldesttime or ptime < oldesttime:
                    oldesttime = ptime
                    oldeststate = pstate
                    
        return oldesttime, oldeststate

    def currentWaitTimes(self):
        waits = []
        for p in self.processes.itervalues():
            if p.isWaiting():
                ptime, pstate = p.lastStateChange()
                waits.append(p.updatetime-ptime)
        return waits

    def _queryDB(self):
        if self.invalid: return
        cherrypy.log('Querying project %s' % (self.name),
                     context='ProjectInfo', severity=logging.DEBUG, traceback=False)
        conn = self.station.dbpool.get()
        try:
            cur = conn.cursor()

            # Get all the info if we don't already have it
            if self.id is None or self.startTime is None:

                cur.execute("""select project_id,username,project_status,start_time,end_time,proj_def_name,ap.proj_snap_id 
                               from analysis_projects ap
                               join stations using (station_id) 
                               join persons using (person_id)
                               join project_snapshots ps on (ap.proj_snap_id = ps.proj_snap_id)
                               join project_definitions using (proj_def_id)
                               where project_name = %s and station_name = %s""",
                            (self.name,self.station.name))
                row = cur.fetchone()
                if not row: raise ProjectNotFound("Project name '%s' doesn't exist in the database for station '%s'" % (self.name,self.station.name))
                self.id, self.owner, self.status,self.startTime,self.endTime,self.datasetDef,self.snapshotId = row

                self.lastActivityTime = self.startTime
                self.lastStatus = 'project started'

                cur.execute("select count(*) from project_files where proj_snap_id = %s",(self.snapshotId,))
                self.fileCount = int(cur.fetchone()[0])

                if self.startTime is None:
                    # nothing interesting to query
                    return
                
            else:
                # just the bits that change
                cur.execute("""select project_status,end_time from analysis_projects
                               where project_name = %s""",(self.name,))
                row = cur.fetchone()
                self.status, self.endTime = row

            # get info on each consumer
            cur = conn.cursor('processes')
            cur.execute("""select process_id, node_name, process_status, start_time, 
                           end_time, completed_time, process_desc
                           from processes join nodes using (node_id) 
                           where process_id in (select process_id from processes where project_id = %(projectId)s)
                           order by process_id""", { 'projectId' : self.id })
            for row in cur:
                if len(self.processes) > 100000:
                    self.invalid = True
                    self.processes = {}
                    return
                processid, process_status, end_time, completed_time = row[0],row[2],row[4],row[5]
                try:
                    p = self.processes[processid]
                except KeyError:
                    p = ProcessInfo(self.updatetime,self,*row)
                    self.processes[processid] = p
                else:
                    p.update(self.updatetime,process_status, end_time, completed_time)

                if self.status != 'running' and p.status == 'active':
                    # if project is ended, but process claims to be active, set the end time
                    p.endTime = self.endTime
                # set the last process activity time
                if p.endTime and p.endTime > self.lastActivityTime:
                    self.lastActivityTime = p.endTime
                    self.lastStatus = 'process ended'
                    self.lastFileName = None
                elif p.startTime > self.lastActivityTime:
                    self.lastActivityTime = p.startTime
                    self.lastStatus = 'process started'
                    self.lastFileName = None

            # set the last activity if the project has ended. We do it after the processes have been
            # checked in case the process status has been modified after the project end
            if self.endTime:
                self.lastActivityTime = self.endTime
                self.lastStatus = 'project ended'
                self.lastFileName = None

            if self.complete: return # no need to go on
            # get files
            process_ids = list(self.processes)
            projectfiles = []

            while process_ids:
                next_batch = process_ids[:250]
                process_ids = process_ids[250:]
                cur = conn.cursor('files')
                cur.execute("""select cf.process_id, df.file_id, df.file_name, cf.consumed_file_status, 
                               cf.open_time, cf.transfer_time, cf.close_time, cf.completed_time
                               from consumed_files cf
                               join project_files pf on (cf.proj_snap_id = pf.proj_snap_id and cf.file_number = pf.file_number)
                               join data_files df on (pf.file_id = df.file_id)
                               where
                               cf.process_id in (%s)""" % ','.join('%d' % pid for pid in next_batch))
                # reorder them according to last change time
                for row in cur:
                    processId, fileId, fileName, status, openTime, transferTime, closeTime, completedTime = row
                    if closeTime is None:
                        # delivered files must be sorted after consumed. Since the DB only stores times to
                        # second resolution, add a fudge factor to make them look later
                        sortdate = transferTime or openTime
                        if status in ('consumed', 'failed', 'skipped'):
                            # I don't know how the status can be consumed without the updateDate being set, but apparently it happens
                            sortdate = closeTime = openTime
                    else: sortdate = closeTime
                    projectfiles.append( (sortdate, processId, fileId, fileName, status, openTime, transferTime, closeTime, completedTime) )
                cur.close()

            projectfiles.sort()

            self.filesSeen = len(projectfiles) # not really the best name

            # update the last activity if it was due to a file
            if projectfiles:
                lastfile = projectfiles[-1]
                lastftime = lastfile[0]
                if lastftime > self.lastActivityTime:
                    self.lastActivityTime = lastftime
                    self.lastFileName = lastfile[3]
                    self.lastStatus = 'file %s' % lastfile[4]

            # clear existing file info (if any)
            self.files = []
            for p in self.processes.itervalues():
                p.clearFileInfo()
            # add the new file info
            for f in projectfiles:
                (sortdate, processId, fileId, fileName, status, openTime, transferTime, closeTime, completedTime ) = f
                fileinfo = FileInfo(fileId, fileName, status, closeTime, transferTime, openTime, processId, completedTime) 
                self.processes[processId].files.append(fileinfo) 
                self.files.append(fileinfo)

            # calculate averages
            for p in self.processes.itervalues():
                p.calcFileTimes()

            # project is finished, no need to get file info again
            if self.endTime: self.complete = True

        finally:
            self.station.dbpool.release()

    def getMedianTimes(self):
        waittimes = []
        transfertimes = []
        busytimes = []

        for p in self.processes.itervalues():
            for t in p.waittimes:
                waittimes.append(t)
            for t in p.transfertimes:
                transfertimes.append(t)
            for t in p.busytimes:
                busytimes.append(t)

        medianwait = median(sorted(waittimes))
        mediantransfer = median(sorted(transfertimes))
        medianbusy = median(sorted(busytimes))
        return medianwait, mediantransfer, medianbusy

class StationInfo(object):
    def __init__(self, experiment, station):
        self.dbpool = dbpool.getLocalPool(experiment)
        self.lock = threading.Lock()
        self.name = station
        self.projectslock = threading.Lock()
        self.projects = {}
        self.nrunningprojects = 0
        self.updatetime=datetime.now(localtimezone)
        self.earliest_time = self.updatetime
        self.lastquerytime = None

        self.summaryupdatetime = datetime.now(localtimezone)
        self.nactiveprocs = 0
        self.nwaitprocs = 0
        self.currentwaitproctimes = []
        self.waithistory = collections.deque()

    def getProject(self, project):
        self.projectslock.acquire()
        try:
            proj = self.projects.get(project)
            if proj:
                proj.update()
            else:
                try:
                    proj = ProjectInfo(self, project)
                except ProjectNotFound:
                    raise KeyError()
                if proj.endTime and proj.endTime < self.earliest_time:
                    # don't cache old projects
                    pass
                else:
                    self.projects[project] = proj
        finally:
            self.projectslock.release()
        return proj

    def update(self,fullupdate=False):
        # if query is recent, then don't requery
        if not fullupdate and datetime.now(localtimezone) < self.updatetime + timedelta(minutes=1): return

        self.lock.acquire()
        try:
            try:
                conn = self.dbpool.get()
                try:
                    if fullupdate or self.lastquerytime is None:
                        self._queryDB(conn)
                    else:
                        self._queryDBincremental(conn)
                finally:
                    self.dbpool.release()
            except psycopg2.Error, ex:
                cherrypy.log('DB query failed', traceback=True)
                raise StationInfoException(str(ex))
            except Exception, ex:
                raise
                #raise InfoException(str(ex))
        finally:
            self.lock.release()

    def lastActivity(self):
        if not self.projects: return None, None
        lastActivityTime = datetime(1970,1,1, tzinfo=localtimezone)
        lastActivity = ''
        for p in self.projects.itervalues():
            if p.lastActivityTime is not None and p.lastActivityTime > lastActivityTime:
                lastActivityTime = p.lastActivityTime
                lastActivity = p.lastStatus
        return lastActivityTime, lastActivity 

    def _queryDBincremental(self, conn):
        cherrypy.log('Incremental query for station %s since %s' % (self.name, self.lastquerytime),
                     context='StationInfo', severity=logging.DEBUG, traceback=False)
        cur = conn.cursor()
        lastquerytime = self.lastquerytime
        self.lastquerytime = datetime.now(localtimezone)
        cur.execute("""select project_name 
                       from analysis_projects ap
                       join stations using (station_id)
                       where station_name = %(stationName)s
                       and start_time >= %(startTime)s
                       order by project_id""",{'stationName':self.name, 
                                               'startTime' : lastquerytime})
        self.updatetime = datetime.now(localtimezone)
        for row in cur:
            projectname, = row
            self.projectslock.acquire()
            try:
                try:
                    p = self.projects[projectname]
                except KeyError:
                    p = ProjectInfo(self, projectname)
                    self.projects[projectname] = p
                    if p.status == 'running': self.nrunningprojects+=1
                else:
                    p.update()
                self.updatetime = datetime.now(localtimezone)

            finally:
                self.projectslock.release()

        cherrypy.log('Finished querying station %s' % self.name, context='StationInfo', severity=logging.DEBUG, traceback=False)

    def _queryDB(self, conn):
        cherrypy.log('Querying station %s' % self.name, context='StationInfo', severity=logging.DEBUG, traceback=False)

        self.earliest_time = datetime.now(localtimezone) - timedelta(hours=6)
        # round down to 10 minute boundary
        minute = self.earliest_time.minute
        minute = minute - (minute % 10)
        self.earliest_time = self.earliest_time.replace(minute=minute,second=0,microsecond=0)

        cur = conn.cursor()
        nrunningprojects=0
        self.lastquerytime = datetime.now(localtimezone)
        cur.execute("""select project_name 
                       from analysis_projects ap
                       join stations using (station_id)
                       where station_name = %(stationName)s
                       and ( project_status = 'running' or end_time > %(endTime)s )
                       order by project_id""", {'stationName':self.name, 'endTime' : self.earliest_time})
        self.updatetime = datetime.now(localtimezone)
        cherrypy.log('Finished querying station %s' % self.name, context='StationInfo', severity=logging.DEBUG, traceback=False)
        knownprojects = set()
        nactiveprocs = nwaitprocs = 0
        waitproctimes = []
        for row in cur:
            projectname, = row
            self.projectslock.acquire()
            try:
                try:
                    p = self.projects[projectname]
                except KeyError:
                    p = ProjectInfo(self,projectname)
                    self.projects[projectname] = p
                else:
                    p.update()
                     
                if p.status == 'running': nrunningprojects+=1
                knownprojects.add(projectname)
                self.nrunningprojects=max(self.nrunningprojects,nrunningprojects)
                self.updatetime = datetime.now(localtimezone)

                nactiveprocs += p.countActiveProcesses()
                nwaitprocs += p.countWaitingProcesses()
                waitproctimes.extend(p.currentWaitTimes())
            finally:
                self.projectslock.release()

        self.nrunningprojects=nrunningprojects
        # clear out old projects
        oldprojects = set(self.projects) - knownprojects
        self.projectslock.acquire()
        try:
            for p in oldprojects:
                del self.projects[p]
        finally:
            self.projectslock.release()
        self.nactiveprocs = nactiveprocs
        self.nwaitprocs = nwaitprocs
        self.currentwaitproctimes = waitproctimes
        self.summaryupdatetime = datetime.now(localtimezone)

        self.waithistory.append( (self.summaryupdatetime, nwaitprocs, nactiveprocs, median(t.days*1440 + t.seconds/60.0 for t in self.currentwaitproctimes) ))
        # trim old information
        while self.waithistory and self.waithistory[0][0] < self.summaryupdatetime - timedelta(hours=24):
            self.waithistory.popleft()


if __name__ == '__main__':
    sinfo = StationInfo('clued0')
    for project in sinfo.projects:
        print project.name
        print project.lastFileName, project.lastFileStatus, project.lastFileTime
        print len(project.processes)
