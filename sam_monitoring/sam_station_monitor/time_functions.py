
from datetime import datetime
from psycopg2.tz import LocalTimezone, FixedOffsetTimezone

localtimezone=LocalTimezone()
utctimezone=FixedOffsetTimezone()

epoch = datetime(1970,1,1,tzinfo=utctimezone)
