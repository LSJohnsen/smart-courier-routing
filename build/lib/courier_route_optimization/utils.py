
from functools import wraps
from datetime import datetime
import csv
import time
import itertools
import numpy as np
import matplotlib.pyplot as plt

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

# normalize 
def normalize(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)
    