from datetime import datetime

date_format = "%Y-%m-%d"
time_format = "%H:%M:%S"
datetime_format = date_format + " " + time_format
epoch = datetime(1000, 1, 1)
epoch_seconds = epoch.timestamp()
