# -*- coding: utf-8 -*-
"""
geoplot
~~~~~~~

Wrapper functions around matplotlib to support geoplotting on web-mercator
map tiles. 

"""

import requests as _requests
import io as _io
import PIL.Image as _Image
import matplotlib.pyplot as plt
from mapping import Extent

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
    print range(xtilemin, xtilemax + 1)
    print range(ytilemin, ytilemax + 1)
    if (xtilemax+1-xtilemin)*(ytilemax+1-ytilemin) > 200:
        raise RuntimeError("Too many tiles")
    for x in range(xtilemin, xtilemax + 1):
        for y in range(ytilemin, ytilemax + 1):
            tile = get_tile(tile_source, x, y, zoom)
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
    if type(extent) is list:
        min_lon = extent[0]
        max_lon = extent[1]
        min_lat = extent[2]
        max_lat = extent[3]
        extent = Extent.from_lonlat(min_lon, max_lon, min_lat, max_lat)
    elif type(extent) is Extent:
        extent = extent.to_project_web_mercator()
    else:
        print "Unrecognized Extent Type"
        return None
    
    xtilemax = int(2 ** zoom * extent.xmax)
    xtilemin = int(2 ** zoom * extent.xmin)
    ytilemin = int(2 ** zoom * extent.ymin)
    ytilemax = int(2 ** zoom * extent.ymax)
    
    tile = as_one_image(tile_source, xtilemax, xtilemin, ytilemax, ytilemin, zoom)
    return tile   
    
def plotMap(extent, tile_source, ax=None, zoom=12):
    """ 
    extent is in lon_lat format
    """
    if ax is None:
        ax = plt.gca()
        
    xtilemax = int(2 ** zoom * extent.xmax)
    xtilemin = int(2 ** zoom * extent.xmin)
    ytilemin = int(2 ** zoom * extent.ymin)
    ytilemax = int(2 ** zoom * extent.ymax)
    
    tile = getTile(extent, tile_source, zoom)
    
    scale = float(2 ** zoom)

    x0, y0 = extent.project(xtilemin / scale, ytilemin / scale)
    x1, y1 = extent.project((xtilemax+1) / scale, (ytilemax+1) / scale)
    ax.imshow(tile, interpolation="lanczos", extent=(x0,x1,y1,y0))
    ax.set(xlim=extent.xrange, ylim=extent.yrange)
    
    
