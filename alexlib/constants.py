from datetime import datetime

date_format = "%Y-%m-%d"
time_format = "%H:%M:%S"
datetime_format = date_format + " " + time_format
epoch = datetime(
    year=2,
    month=1,
    day=1,
    hour=0,
    minute=0,
    second=0,
    microsecond=0,
)
epoch_s = epoch.timestamp()
