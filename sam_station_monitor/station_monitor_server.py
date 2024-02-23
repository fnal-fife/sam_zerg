#! /usr/bin/env python

import os,sys,logging,logging.handlers
import cherrypy

from SAMStationMonitor import SAMStationMonitor

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))


    if len(sys.argv) > 1:
        configfile = sys.argv[1]
    else:
        configfile = 'default.cfg'
    cherrypy.config.update(configfile)

    # set up logging to roll over daily
    cherrypy.log.error_file = ""
    cherrypy.log.access_file = ""
    logdir = getattr(cherrypy.log, "log_dir", None)
    if logdir:
        backupCount = getattr(cherrypy.log, "keep_days",30)
        h = logging.handlers.TimedRotatingFileHandler(os.path.join(logdir,"error_log"),when="midnight",interval=1,backupCount=backupCount)
        h.setLevel(logging.DEBUG)
        h.setFormatter(cherrypy._cplogging.logfmt)
        cherrypy.log.error_log.addHandler(h)
        h = logging.handlers.TimedRotatingFileHandler(os.path.join(logdir,"access_log"),when="midnight",interval=1,backupCount=backupCount)
        h.setLevel(logging.DEBUG)
        h.setFormatter(cherrypy._cplogging.logfmt)
        cherrypy.log.access_log.addHandler(h)

    # Top level app

    conf = {'/robots.txt' :
            {'tools.staticfile.on' : True,
             'tools.staticfile.filename': os.path.join(current_dir,"static","robots.txt")
             },
            }
    cherrypy.tree.mount(None,"/", conf)

    conf = {'/' : 
            {'tools.staticdir.root' : current_dir,
             'tools.encode.on' : True,
             'tools.gzip.mime_types': ['text/html', 'text/plain', 'text/javascript', 'text/css', 'application/json'],
             'tools.gzip.on' : True
             },
            '/sammonitor.css' : 
            {'tools.staticfile.on' : True,
             'tools.staticfile.filename' : os.path.join(current_dir,"static","sammonitor.css")
             },
            '/static' : 
            {'tools.staticdir.on' : True,
             'tools.staticdir.dir' :'static',
             },
            }

    monitor = SAMStationMonitor()
    mountpoint = cherrypy.config.get('mountpoint', "/station_monitor")
    app = cherrypy.tree.mount(monitor, mountpoint, configfile)
    app.merge(conf)
    monitor.start(app)

    cherrypy.engine.start()
    cherrypy.engine.block()
