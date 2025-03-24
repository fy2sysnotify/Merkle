import datetime

ts = (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds()
print(int(ts))
