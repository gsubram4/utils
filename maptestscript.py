# -*- coding: utf-8 -*-

from utils.mapping import Extent
from utils.geoplot import plotMap
from utils.common import fig
import matplotlib.pyplot as plt


tile_source = "http://localhost:5050/stamen-terrain/stamen-terrain-{z}-{x}-{y}.png"

extent = Extent.from_center_lonlat(36.836135, -1.292976, xsize=.0003)
fig()
zz = plotMap(extent, tile_source, zoom=13)

