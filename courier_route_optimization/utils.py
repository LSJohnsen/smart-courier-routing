
from functools import wraps
from datetime import datetime
import csv
import time
import itertools
import numpy as np
import math
import matplotlib.pyplot as plt
from courier_route_optimization.constants import EARTH_RADIUS_KM

'''
decorators or util functuions 
'''
def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        duration = end - start

        print(f"{func.__name__} took {duration:.5f} seconds")

        # log timer to csv 
        log_file = "execution_timer_log.csv"
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            

            if file.tell() == 0:
                writer.writerow(["timestamp", "function", "duration_seconds"])
            writer.writerow([datetime.now().isoformat(), func.__name__, f"{duration:.5f}"])

        return result
    return wrapper

def normalize(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

# calculates distances from lat/lon, based on https://github.com/mapado/haversine/blob/main/haversine/haversine.py
def haversine(lat1, lon1, lat2, lon2, R=EARTH_RADIUS_KM):

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
