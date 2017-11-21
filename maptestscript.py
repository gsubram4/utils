# -*- coding: utf-8 -*-

from utils.mapping import plotMap, Extent

tile_source = "http://localhost:5050/mapbox-light/mapbox-light-{z}-{x}-{y}.png"

extent = Extent.from_center_lonlat(36.836135, -1.292976, xsize=.0003)

zz = plotMap(extent, tile_source)

