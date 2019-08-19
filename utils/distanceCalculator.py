# -*- coding: utf-8 -*-

import numpy as np
from math import radians, cos, sin, asin, sqrt, atan2

r_earth = 6371.

def translate_lonlat(longitude, latitude, x_km, y_km=None):
    if y_km is None:
        y_km = x_km
    new_latitude = latitude + ((y_km/r_earth) * (180./np.pi))
    new_longitude = longitude + ((x_km/r_earth) * (180./np.pi) / cos(latitude*np.pi/180.))
    return new_longitude, new_latitude


def haversine_np(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.    

    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km