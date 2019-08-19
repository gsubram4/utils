# -*- coding: utf-8 -*-
"""
geoplot
~~~~~~~

Wrapper functions around matplotlib to support geoplotting on web-mercator
map tiles. 

"""
from __future__ import print_function, absolute_import
import requests as _requests
import io as _io
import PIL.Image as _Image
import matplotlib.pyplot as plt
from .mapping import Extent, to_web_mercator
from collections import Iterable, defaultdict
import numpy as np
from functools import partial

MAPBOX_SATELLITE = "https://api.mapbox.com/v4/mapbox.streets-satellite/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZ3VpbHR5c3BhcmsiLCJhIjoiM2NPR0l4dyJ9.H3VmL6yY8xt7ZpyqeavnSw"
MAPBOX_STREETS = "https://api.mapbox.com/v4/mapbox.streets/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZ3VpbHR5c3BhcmsiLCJhIjoiM2NPR0l4dyJ9.H3VmL6yY8xt7ZpyqeavnSw"
STAMEN = "http://b.tile.stamen.com/terrain/{z}/{x}/{y}.jpg"

tile_cache = defaultdict(defaultdict)

def get_tile(tile_source, x, y, zoom):
    """Attempt to fetch the tile at the specified coords and zoom level.

    :param x: X coord of the tile; must be between 0 (inclusive) and
      `2**zoom` (exclusive).
    :param y: Y coord of the tile.
    :param zoom: Integer, greater than or equal to 0.  19 is the commonly
      supported maximum zoom.

    :return: `None` for (cache related) failure, or a :package:`Pillow`
      image object of the tile.
    """
    url = tile_source.format(x=x, y=y, z=zoom)
    response = _requests.get(url)
    if not response.ok:
        raise IOError("Failed to download {}.  Got {}".format(url, response))
        return None
    try:
        fp = _io.BytesIO(response.content)
        return _Image.open(fp)
    except:
        raise RuntimeError("Failed to decode data for {} - {}x{} @ {} zoom".format(tile_source, x, y, zoom))
        return None


def as_one_image(tile_source, xtilemax, xtilemin, ytilemax, ytilemin, zoom):
    size = 256
    xs = size * (xtilemax + 1 - xtilemin)
    ys = size * (ytilemax + 1 - ytilemin)
    out = _Image.new("RGB", (xs, ys))
    #print(range(xtilemin, xtilemax + 1))
    #print(range(ytilemin, ytilemax + 1))
    if (xtilemax+1-xtilemin)*(ytilemax+1-ytilemin) > 200:
        raise RuntimeError("Too many tiles")
    for x in range(xtilemin, xtilemax + 1):
        for y in range(ytilemin, ytilemax + 1):
            #check cache:
            if (x,y,zoom) in tile_cache[tile_source]:
                tile =  tile_cache[tile_source][(x,y,zoom)]
            else:
                tile = get_tile(tile_source, x, y, zoom)
                tile_cache[tile_source][(x,y,zoom)] = tile
            xo = (x - xtilemin) * size
            yo = (y - ytilemin) * size
            out.paste(tile, (xo, yo))
    return out

def getTile(extent, tile_source, zoom=12):
    """ 
    Constructs the best available image covering the extent 
    at the specified zoom level. 
    
    The tile may be larger than the extent requested, but is 
    guaranteed to cover the entire extent.
    """   
    
    ## Handle Extent
    #print(type(extent))
    if type(extent) is list:
        min_lon = extent[0]
        max_lon = extent[1]
        min_lat = extent[2]
        max_lat = extent[3]
        extent = Extent.from_lonlat(min_lon, max_lon, min_lat, max_lat)
    elif isinstance(extent, Extent):
        extent = extent.to_project_web_mercator()
    else:
        print("Unrecognized Extent Type")
        return None
    
    xtilemax = int(2 ** zoom * extent.xmax)
    xtilemin = int(2 ** zoom * extent.xmin)
    ytilemin = int(2 ** zoom * extent.ymin)
    ytilemax = int(2 ** zoom * extent.ymax)
    
    tile = as_one_image(tile_source, xtilemax, xtilemin, ytilemax, ytilemin, zoom)
    return tile   
    
def plotMap(extent, tile_source, figure=None, zoom=None, auto_render=False, hide_axis=True):
    """ 
    extent is in lon_lat format
    """
    if figure is None:
        figure = plt.gcf()
    ax = figure.gca()

    if zoom is None:
        zoom = calculate_optimal_zoom(extent, figure)
        #print("Zoom is: ", zoom)

    xtilemax = int(2 ** zoom * extent.xmax)
    xtilemin = int(2 ** zoom * extent.xmin)
    ytilemin = int(2 ** zoom * extent.ymin)
    ytilemax = int(2 ** zoom * extent.ymax)
    
    tile = getTile(extent, tile_source, zoom)

    if tile is not None:
        scale = float(2 ** zoom)
    
        x0, y0 = extent.project(xtilemin / scale, ytilemin / scale)
        x1, y1 = extent.project((xtilemax+1) / scale, (ytilemax+1) / scale)
        ax.imshow(tile, interpolation="lanczos", extent=(x0,x1,y1,y0))
        ax.set(xlim=extent.xrange, ylim=extent.yrange)
        plt.autoscale(False)
        if hide_axis:
            plt.gca().axes.get_xaxis().set_ticks([])
            plt.gca().axes.get_yaxis().set_ticks([])
        #plt.show(block=False)  
        canvas = figure.canvas
        if auto_render:
            canvas.mpl_connect('button_release_event', partial(button_press_callback, ax=ax, figure=figure, tile_source=tile_source))
        else:
            canvas.mpl_connect('key_release_event', partial(key_press_callback, figure=figure, tile_source=tile_source))            

def key_press_callback(event, figure, tile_source):
    if event.key == 'd':
        ax = figure.gca()
        myExtent = extent(ax)
        plotMap(myExtent, tile_source)
        figure.canvas.draw()
    if event.key == 'c':
        ax = figure.gca()
        myExtent = extent(ax)
        figure.clf()
        plotMap(myExtent, tile_source)
        figure.canvas.draw()

def button_press_callback(event, figure, tile_source):
    myExtent = extent(ax)
    plotMap(myExtent, tile_source)
        
def plot(longitudes, latitudes, *args, **kwargs):
    if isinstance(longitudes, Iterable) and isinstance(latitudes, Iterable):
        xpts, ypts = zip(*map(to_web_mercator, longitudes, latitudes))
    else:
        xpts, ypts = to_web_mercator(longitudes, latitudes)
    plt.plot(xpts, ypts, *args, **kwargs)
    
def extent(ax=None):
    if ax is None:
        ax = plt.gca()
    
    axis = ax.axis()
    return Extent(axis[0],axis[1], axis[3], axis[2])

def calculate_optimal_zoom(myExtent, figure):
    lle = myExtent.get_lonlat_extent()
    
    ry1 = np.log( (np.sin(np.deg2rad(lle[2]))+1) / np.cos(np.deg2rad(lle[2])) )
    ry2 = np.log( (np.sin(np.deg2rad(lle[3]))+1) / np.cos(np.deg2rad(lle[3])) )
    ryc = (ry1+ry2) / 2
    centerY = np.rad2deg(np.arctan(np.sinh(ryc)))

    width, height = figure.get_size_inches() * figure.dpi
    resolutionHorizontal = (lle[1]-lle[0]) / width
    vy0 = np.log(np.tan(np.pi * (0.25 + centerY/360.)))
    vy1 = np.log(np.tan(np.pi * (0.25 + lle[3]/360.)))

    viewHeightHalf = height/2.0
    zoomFactorPowered = viewHeightHalf / (40.7436654315252*(vy1 - vy0))
    resolutionVertical = 360.0 / (zoomFactorPowered * 256)

    resolution = max(resolutionHorizontal, resolutionVertical)
    
    zoom = np.round(np.log2(360 / (resolution * 256)))
    return int(zoom)-1


