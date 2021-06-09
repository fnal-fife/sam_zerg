#! /usr/bin/env python

import psycopg2
import time
import datetime
import cPickle
import struct
import socket
import os
import sys
import fcntl

UTC = psycopg2.tz.FixedOffsetTimezone(0, 'UTC')
epoch = datetime.datetime(1970,1,1,0,0,0, tzinfo=UTC)

databases = { 
        'nova' : "dbname=sam_nova_prd host=sampgsdb01.fnal.gov port=5433",
        'mu2e' : 'dbname=sam_mu2e_prd host=sampgsdb02.fnal.gov port=5433',
        'lariat' : 'dbname=sam_lariat_prd host=sampgsdb03.fnal.gov port=5440',
        'minos' : 'dbname=sam_minos_prd host=sampgsdb03.fnal.gov port=5439',
        'minerva' : 'dbname=sam_minerva_prd host=sampgsdb03.fnal.gov port=5441',
        'uboone' : 'dbname=sam_uboone_prd host=sampgsdb02.fnal.gov port=5437',
        #'holometer' : 'dbname=sam_holometer_prd host=cspgsprd2.fnal.gov port=5441',
        #'darkside' : 'dbname=sam_darkside_prd host=cspgsprd1.fnal.gov port=5436',
        'dune' : 'dbname=sam_dune_prd host=sampgsdb03.fnal.gov port=5435',
        'gm2' : 'dbname=sam_gm2_prd host=sampgsdb03.fnal.gov port=5437',
        'coupp' : 'dbname=sam_coupp_prd host=sampgsdb03.fnal.gov port=5434',
        'seaquest' : 'dbname=sam_seaquest_prd host=sampgsdb03.fnal.gov port=5443',
        'numix' : 'dbname=sam_numix_prd host=sampgsdb03.fnal.gov port=5442',
	'icarus' : 'dbname=sam_icarus_prd host=sampgsdb03.fnal.gov port=5436',
	'noble' : 'dbname=sam_noble_prd host=sampgsdb03.fnal.gov port=5438',
        }

def parse_date(timestr):
    for tmformat in ('%Y-%m-%d', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            t = datetime.datetime.strptime( timestr, tmformat)
        except ValueError:
            continue
    else:
        t = t.replace(tzinfo=psycopg2.tz.LocalTimezone())
        return t
    raise ValueError('Unknown time string: %s' % timestr)

def get_file_data(experiment, conn, currenttime, lastdata=None):

    if lastdata is None: lastdata = {}

    path_base = 'dh.sam.%s.metadata.files' % experiment
    stats = []

    cur = conn.cursor()

    filecount_key = path_base + '.all.count'
    activefilecount_key = path_base + '.active.count'
    activefilesize_key = path_base + '.active.size'

    # check if we have values from a previous run
    if filecount_key in lastdata:
        last_time = datetime.datetime.utcfromtimestamp(lastdata[filecount_key][0]).replace(tzinfo=UTC)
        last_count = lastdata[filecount_key][1]
    else:
        last_count = 0
        last_time = epoch

    ts = int((currenttime - epoch).total_seconds())
    cur.execute("""select count(*), sum(file_size_in_bytes)
    from data_files 
    where create_date > %(starttime)s and create_date < %(endtime)s""", {'starttime' : last_time, 'endtime': currenttime})
    file_count, file_size = cur.fetchone()

    total_file_count = last_count + file_count
    stats.append(  ( filecount_key, (ts, total_file_count) ) )
    
    # check if we have values from a previous run
    if activefilecount_key in lastdata and activefilesize_key in lastdata:
        last_time = datetime.datetime.utcfromtimestamp(lastdata[activefilesize_key][0]).replace(tzinfo=UTC)
        last_activecount = lastdata[activefilecount_key][1]
        last_activesize = lastdata[activefilesize_key][1]
    else:
        last_activecount = 0
        last_activesize = 0
        last_time = epoch

    # file sizes with locations
    # look for files with locations in the time range which do not have locations added
    # in an earlier time (because we should have those already)
    if last_time != epoch:
        cur.execute("""select count(*), sum(file_size_in_bytes)
        from data_files df 
        where exists ( select 1 from data_file_locations dfl where dfl.file_id = df.file_id and dfl.create_date >= %(starttime)s and dfl.create_date < %(endtime)s)
        and not exists (select 1 from data_file_locations dfl where dfl.file_id = df.file_id and (dfl.create_date < %(starttime)s or dfl.create_date is null))
        and df.retired_date is null""", {'starttime' : last_time, 'endtime': currenttime})
    else:
        cur.execute("""select count(*), sum(file_size_in_bytes)
        from data_files df 
        where exists ( select 1 from data_file_locations dfl where dfl.file_id = df.file_id and (dfl.create_date < %(endtime)s or dfl.create_date is null))
        and df.retired_date is null""", {'starttime' : last_time, 'endtime': currenttime})

    active_file_count , active_file_size = cur.fetchone()
    total_active_file_count = last_activecount + active_file_count
    total_active_file_size = last_activesize + long(active_file_size or 0)

    stats.extend( [(activefilecount_key, (ts, total_active_file_count)), (activefilesize_key, (ts, total_active_file_size))])
    if active_file_count > 0:
        stats.append( (path_base + '.active.mean_size', (ts, float(active_file_size)/float(active_file_count))))
    return stats
        
def get_project_data(experiment, conn, currenttime):

    path_base = 'dh.sam.%s.projects' % experiment
    ts = int((currenttime - epoch).total_seconds())
    stats = []

    cur = conn.cursor()

    cur.execute("""select username, count(*), sum(file_size_in_bytes)
    from data_files df
    join project_files pf on (df.file_id = pf.file_id)
    join consumed_files cf on (pf.proj_snap_id = cf.proj_snap_id and pf.file_number = cf.file_number)
    join processes proc on (proc.process_id = cf.process_id)
    join analysis_projects proj on (proj.project_id = proc.project_id)
    join persons per on (per.person_id = proj.person_id)
    where cf.open_time >= %(endtime)s - interval '5 minutes' and cf.open_time < %(endtime)s
    group by username
    """, {'endtime': currenttime})

    for username, count, size in cur:
        count = int(count)
        size = long(size)
        stats.extend( [ ( '%s.files.user.%s.delta_count' % (path_base, username), (ts, count)),
                        ( '%s.files.user.%s.delta_size' % (path_base, username), (ts, size)),
                        ]
                    )

    cur.execute("""select username, count(*) from processes proc
            join analysis_projects proj on (proj.project_id = proc.project_id)
            join persons per on (per.person_id = proj.person_id)
            where ( %(time)s between proc.start_time and proc.end_time) or (proc.end_time is null and proc.start_time <= %(time)s and proc.process_status = 'active')
            group by username
            """, {'time' : currenttime} )

    for username, count in cur:
        count = int(count)
        stats.extend( [ ('%s.processes.user.%s.count' % (path_base, username), (ts, count)) ] )

    return stats

def get_database_stats(experiment, conn):
    # these are always current; can't get them for a past time
    path_base = 'dh.sam.%s.database' % experiment
    cur = conn.cursor()
    stats = []
    cur.execute("""select current_database(), pg_database_size(current_database())""")
    dbname, total_size = cur.fetchone()
    stats.append( ('%s.%s.total_size' % (path_base, dbname), (int(time.time()), total_size)) )
    return stats

persistent_file = '.sam_stats_last_run'

def round_time(dt):
    # round a datetime to the 5 min reporting period
    return dt.replace(minute= starttime.minute - (starttime.minute % 5), second=0, microsecond=0)

# send to graphite
def send_to_graphite(stats):
    payload = cPickle.dumps(stats, protocol=2)
    header = struct.pack("!L", len(payload))
    message = header + payload

    try:
        sock = socket.create_connection( graphite_server, 60)
        sock.sendall(message)
        sock.close()
    except socket.error as ex:
        print 'Socket error for %s: %s' % (graphite_server, ex)


def get_args(args):
    graphite_server = tuple(args[1].split(":",1))

    passwd_spec = args[2]
    if passwd_spec.startswith('file:'):
        passwd = open(passwd_spec[5:]).read().strip()
    else:
        passwd = passwd_spec

    now = datetime.datetime.now(psycopg2.tz.LocalTimezone())

    if len(args) > 3:
        starttime = parse_date( args[3] )
    else:
        starttime = now - datetime.timedelta(minutes=5)
    starttime = round_time(starttime)
    
    if len(args) > 4:
        endtime = parse_date( args[4] )
    else:
        endtime = now
     
    return program_name, graphite_server, passwd, starttime, endtime


def set_processing_mutex(program_name):
    # Mutex: If ran frequently, previous iteration may still be processing
    mfile = os.path.basename(program_name) + '_lock'
    mutfd = os.open(os.path.join('/tmp', mfile), os.O_RDWR | os.O_CREAT)
    try:
        fcntl.lockf(mutfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print 'Already running'
        sys.exit(1)
    os.ftruncate(mutfd, 0)
    os.write(mutfd, '%s' % os.getpid())


if __name__ == '__main__':
    # Arguments
    #sys.argv[0] = program_name
    #sys.argv[1] = graphite server
    #sys.argv[2] = password / password file 
    #sys.argv[3] = start time 
    #sys.argv[4] = end time 

    # Parse the arguments
    program_name, graphite_server, passwd, start_time, end_time = get_args(sys.argv)

    set_processing_mutex(program_name)


    # Once a day do a full query, else try to use an existing stats file
    try:
        with open(persistent_file) as f:
            olddata = cPickle.load(f)
        starttime = olddata['last_run_time'] + datetime.timedelta(minutes=5)
        starttime = round_time(starttime)
        lastdata = olddata['results']
        print "Start from last run: %s" % starttime
    except (OSError, IOError, EOFError) as ex:
        print 'Unable to read last run file: %s' % (ex)
        lastdata = {}

    if starttime.hour==0 and starttime.minute==0:
        lastdata = {}

    currenttime = starttime

    lasttime = None
    while currenttime <= endtime:
        print currenttime
        currentdata = {}
        stats = []
        for experiment, dbconnect in databases.iteritems():
            print experiment
            try:
                with psycopg2.connect(dbconnect + " " + passwd) as conn:
                    file_data = get_file_data(experiment, conn, currenttime, lastdata=lastdata)
                    stats.extend(file_data)
                    currentdata.update({ k:v for k,v in file_data})
                    stats.extend(get_project_data(experiment, conn, currenttime))
                    stats.extend(get_database_stats(experiment, conn))
            except psycopg2.Error as ex:
                print 'Database error for %s: %s' % (experiment, ex)

        lasttime = currenttime
        currenttime += datetime.timedelta(minutes=5)
        lastdata = currentdata

        #print stats

        send_to_graphite(stats)

        # write out most recent values
        try:
            with open(persistent_file, 'wb') as f:
                data = { 'last_run_time' : lasttime, 'results' : lastdata }
                cPickle.dump(data, f, cPickle.HIGHEST_PROTOCOL)
        except (OSError, IOError) as ex:
            print 'Error writing persistent file: %s' % ex

        # update now in case we've been running a long time
        if endtime == now:
            now = datetime.datetime.now(psycopg2.tz.LocalTimezone())
            endtime = now

