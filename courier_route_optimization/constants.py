

from enum import Enum

# https://www.youtube.com/watch?v=TAMbq0iRUsA
# https://docs.python.org/3/library/enum.html

'''
Contains constants for the delivery methods, urgency, and earth radius
'''

class StrEnum(str, Enum):
    #Python 3.11 StrEnum for Python 3.10 (gpt)
    pass

class Mode(StrEnum):
    CAR = "car"
    BICYCLE = "bicycle"
    WALK = "walk"

MODE_PARAMS = {
    Mode.CAR: {"speed": 50, "cost": 4, "co2": 120},    #km/h, NOK/km, g/km
    Mode.BICYCLE: {"speed": 15, "cost": 0, "co2": 0},
    Mode.WALK: {"speed": 5, "cost": 0, "co2": 0},
}

URGENCY_MULT = {
    "high": 0.6,
    "medium": 1.0,   #Change?
    "low": 1.2
}

EARTH_RADIUS_KM = 6371.0

#ex use:
#print(Mode.CAR)                 # Mode.CAR
#print(Mode.CAR == "car")        # True
#print(MODE_PARAMS[Mode("car")]) # {'speed': 50, 'cost': 4, 'co2': 120}
#speed = MODE_PARAMS[Mode.CAR]["speed"] # 50


