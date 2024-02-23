
from time_functions import epoch, utctimezone

# Format the number a timedelta as mins, secs
def formatMinSec(dt):
    if dt is None: return '-'
    mins, secs = divmod(dt.seconds, 60)
    mins = mins + dt.days*24*60 
    if mins > 0:
        return '%smin %ss' % (mins, secs)
    else:
        return '%ss' % secs

# Display a timedelta object as the number of minutes only
def formatMins(dt):
    if dt is None: return '-'
    mins = dt.days*24*60 + dt.seconds//60
    if mins < 1: return '<1 minute'
    elif mins < 2: return '<2 minutes'
    else: return '%d minutes' % mins

def formatHours(dt):
    if dt is None: return '-'
    hours = dt.days*24 + dt.seconds//3600
    if hours == 1: return '1 hour'
    else: return '%d hours' % hours

def formatTime(t):
    if t is None: return '-'
    else: return '<span data-timestamp="%d">%s</span>' % ( 1000*(t - epoch).total_seconds(), t.astimezone(utctimezone).strftime('%Y-%m-%d %H:%M:%S UTC'))
