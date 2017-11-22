"""
mapping
~~~~~~~

Performs projection functions.  Map tiles are projected using the
https://en.wikipedia.org/wiki/Web_Mercator projection, which does not preserve
area or length, but is convenient.  We follow these conventions:

- Coordinates are always in the order longitude, latitude.
- Longitude varies between -180 and 180 degrees.  This is the east/west
  location from the Prime Meridian, in Greenwich, UK.  Positive is to the east.
- Latitude varies between -85 and 85 degress (approximately.  More extreme
  values cannot be represented in Web Mercator).  This is the north/south
  location from the equator.  Positive is to the north.

Once projected, the x coordinate varies between 0 and 1, from -180 degrees west
to 180 degrees east.  The y coordinate varies between 0 and 1, from (about) 85
degrees north to -85 degrees south.  Hence the natural ordering from latitude
to y coordinate is reversed.

Web Mercator agrees with the projections EPSG:3857 and EPSG:3785 up to
rescaling and reflecting in the y coordinate.

For more information, see for example
http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

Typical workflow is to use one of the `extent` methods to construct an
:class:`Extent` object.  This stores details of a rectangle of web mercator
space.  Then construct a :class:`Plotter` object to actually draw the tiles.
This object can then be used to plot the basemap to a `matplotlib` axes object.
"""

import math as _math

_EPSG_RESCALE = 20037508.342789244

def _to_3857(x, y):
    return ((x - 0.5) * 2 * _EPSG_RESCALE,
        (0.5 - y) * 2 * _EPSG_RESCALE)

def _from_3857(x, y):
    xx = 0.5 + (x / _EPSG_RESCALE) * 0.5
    yy = 0.5 - (y / _EPSG_RESCALE) * 0.5
    return xx, yy

def to_web_mercator(longitude, latitude):
    """Project the longitude / latitude coords to the unit square.

    :param longitude: In degrees, between -180 and 180
    :param latitude: In degrees, between -85 and 85

    :return: Coordinates `(x,y)` in the "Web Mercator" projection, normalised
      to be in the range [0,1].
    """
    xtile = (longitude + 180.0) / 360.0
    lat_rad = _math.radians(latitude)
    ytile = (1.0 - _math.log(_math.tan(lat_rad) + (1 / _math.cos(lat_rad))) / _math.pi) / 2.0
    return (xtile, ytile)

def to_lonlat(x, y):
    """Inverse project from "web mercator" coords back to longitude, latitude.

    :param x: The x coordinate, between 0 and 1.
    :param y: The y coordinate, between 0 and 1.

    :return: A pair `(longitude, latitude)` in degrees.
    """
    longitude = x * 360 - 180
    latitude = _math.atan(_math.sinh(_math.pi * (1 - y * 2))) * 180 / _math.pi
    return (longitude, latitude)

class _BaseExtent(object):
    """A simple "rectangular region" class."""
    def __init__(self, xmin, xmax, ymin, ymax):
        self._xmin, self._xmax = xmin, xmax
        self._ymin, self._ymax = ymin, ymax
        if not (xmin < xmax):
            raise ValueError("xmin < xmax.")
        if not (ymin < ymax):
            raise ValueError("ymin < ymax.")

    @property
    def xmin(self):
        """Minimum x value of the region."""
        return self.project(self._xmin, self._ymin)[0]

    @property
    def xmax(self):
        """Maximum x value of the region."""
        return self.project(self._xmax, self._ymax)[0]

    @property
    def width(self):
        """The width of the region."""
        return self.xmax - self.xmin

    @property
    def xrange(self):
        """A pair of (xmin, xmax)."""
        return (self.xmin, self.xmax)

    @property
    def ymin(self):
        """Minimum y value of the region."""
        return self.project(self._xmin, self._ymin)[1]

    @property
    def ymax(self):
        """Maximum y value of the region."""
        return self.project(self._xmax, self._ymax)[1]

    @property
    def height(self):
        """The height of the region."""
        return self.ymax - self.ymin

    @property
    def yrange(self):
        """A pair of (ymax, ymin).  Inverted so as to work well with
        `matplotib`.
        """
        return (self.ymax, self.ymin)
    
    @staticmethod
    def from_center(x, y, xsize=None, ysize=None, aspect=1.0):
        """Helper method to aid in constructing a new instance centered on the
        given location, with a given width and/or height.  If only one of the
        width or height is specified, the aspect ratio is used.

        :return: `(xmin, xmax, ymin, ymax)`
        """
        if xsize is None and ysize is None:
            raise ValueError("Must specify at least one of width and height")
        x, y, aspect = float(x), float(y), float(aspect)
        if xsize is not None:
            xsize = float(xsize)
        if ysize is not None:
            ysize = float(ysize)
        if xsize is None:
            xsize = ysize * aspect
        if ysize is None:
            ysize = xsize / aspect
        xmin, xmax = x - xsize / 2, x + xsize / 2
        ymin, ymax = y - ysize / 2, y + ysize / 2
        return (xmin, xmax, ymin, ymax)

    def _to_aspect(self, aspect):
        """Internal helper method.  Return a new bounding box.
        Shrinks the rectangle as necessary."""
        width = self._xmax - self._xmin
        height = self._ymax - self._ymin
        new_xrange = height * aspect
        new_yrange = height
        if new_xrange > self.width:
            new_xrange = width
            new_yrange = width / aspect
        midx = (self._xmin + self._xmax) / 2
        midy = (self._ymin + self._ymax) / 2
        return (midx - new_xrange / 2, midx + new_xrange / 2,
                      midy - new_yrange / 2, midy + new_yrange / 2)

    def _with_scaling(self, scale):
        """Return a new instance with the same midpoint, but with the width/
        height divided by `scale`.  So `scale=2` will zoom in."""
        midx = (self._xmin + self._xmax) / 2
        midy = (self._ymin + self._ymax) / 2
        xs = (self._xmax - self._xmin) / scale / 2
        ys = (self._ymax - self._ymin) / scale / 2
        return (midx - xs, midx + xs, midy - ys, midy + ys)
    
class Extent(_BaseExtent):
    """Store details about an area of web mercator space.  Can be switched to
    be projected in EPSG:3857 / EPSG:3785.  We allow the x range outside of
    [0,1] to allow working across the "boundary" as 1 (i.e. we treat the
    coordinates as being topologically a cylinder and identify (0,y) and (1,y)
    for all y).

    :param xmin:
    :param xmax: The range of the x coordinates, between 0 and 1. (But see
      note above).
    :param ymin:
    :param ymax: The range of the y coordinates, between 0 and 1.
    :param projection_type: Internal use only, see :meth:`to_project_3857`
      and :meth:`to_project_web_mercator` instead.
    """
    def __init__(self, xmin, xmax, ymin, ymax, projection_type="normal"):
        super(Extent, self).__init__(xmin, xmax, ymin, ymax)
        if ymin < 0 or ymax > 1:
            raise ValueError("Need 0 < ymin < ymax < 1.")
        if projection_type == "normal":
            self.project = self._normal_project
        elif projection_type == "epsg:3857":
            self.project = self._3857_project
        else:
            raise ValueError()
        self._project_str = projection_type

    @staticmethod
    def from_center(x, y, xsize=None, ysize=None, aspect=1.0):
        """Construct a new instance centred on the given location in Web
        Mercator space, with a given width and/or height.  If only one of the
        width or height is specified, the aspect ratio is used.
        """
        xmin, xmax, ymin, ymax = _BaseExtent.from_center(x, y, xsize, ysize, aspect)
        xmin, xmax = max(0, xmin), min(1.0, xmax)
        ymin, ymax = max(0, ymin), min(1.0, ymax)
        return Extent(xmin, xmax, ymin, ymax)

    @staticmethod
    def from_center_lonlat(longitude, latitude, xsize=None, ysize=None, aspect=1.0):
        """Construct a new instance centred on the given location with a given
        width and/or height.  If only one of the width or height is specified,
        the aspect ratio is used.
        """
        x, y = to_web_mercator(longitude, latitude)
        return Extent.from_center(x, y, xsize, ysize, aspect)
        
    @staticmethod
    def from_center_3857(x, y, xsize=None, ysize=None, aspect=1.0):
        """Construct a new instance centred on the given location with a given
        width and/or height.  If only one of the width or height is specified,
        the aspect ratio is used.
        """
        x, y = _from_3857(x, y)
        ex = Extent.from_center(x, y, xsize, ysize, aspect)
        return ex.to_project_3857()

    @staticmethod
    def from_lonlat(longitude_min, longitude_max, latitude_min, latitude_max):
        """Construct a new instance from longitude/latitude space."""
        xmin, ymin = to_web_mercator(longitude_min, latitude_max)
        xmax, ymax = to_web_mercator(longitude_max, latitude_min)
        return Extent(xmin, xmax, ymin, ymax)

    @staticmethod
    def from_3857(xmin, xmax, ymin, ymax):
        """Construct a new instance from longitude/latitude space."""
        xmin, ymin = _from_3857(xmin, ymin)
        xmax, ymax = _from_3857(xmax, ymax)
        ex = Extent(xmin, xmax, ymin, ymax)
        return ex.to_project_3857()

    def get_lonlat_extent(self):
        min_lon, min_lat = to_lonlat(self._xmin, self._ymin)
        max_lon, max_lat = to_lonlat(self._xmax, self._ymax)
        return (min_lon, max_lon, min_lat, max_lat)

    def __repr__(self):
        return "Extent(({},{})->({},{}) projected as {})".format(self.xmin, self.ymin,
                      self.xmax, self.ymax, self._project_str)

    def clone(self, projection_type=None):
        """A copy."""
        if projection_type is None:
            projection_type = self._project_str
        return Extent(self._xmin, self._xmax, self._ymin, self._ymax, projection_type)

    def _normal_project(self, x, y):
        """Project from tile space to coords."""
        return x, y

    def _3857_project(self, x, y):
        return _to_3857(x, y)

    def to_project_3857(self):
        """Change the coordinate system to conform to EPSG:3857 / EPSG:3785
        which can be useful when working with e.g. geoPandas (or other data
        which is projected in this way).
        
        :return: A new instance of :class:`Extent`
        """
        return self.clone("epsg:3857")

    def to_project_web_mercator(self):
        """Change the coordinate system back to the default, the unit square.

        :return: A new instance of :class:`Extent`
        """
        return self.clone("normal")

    def with_center(self, xc, yc):
        """Create a new :class:`Extent` object with the centre moved to these
        coordinates and the same rectangle size.  Clips so y is in range [0,1].
        """
        oldxc = (self._xmin + self._xmax) / 2
        oldyc = (self._ymin + self._ymax) / 2
        ymin = self._ymin + yc - oldyc
        ymax = self._ymax + yc - oldyc
        if ymin < 0:
            ymax -= ymin
            ymin = 0
        if ymax > 1:
            ymin -= (ymax - 1)
            ymax = 1
        return Extent(self._xmin + xc - oldxc, self._xmax + xc - oldxc,
            ymin, ymax, self._project_str)

    def with_center_lonlat(self, longitude, latitude):
        """Create a new :class:`Extent` object with the centre the given
        longitude / latitude and the same rectangle size.
        """
        xc, yc = to_web_mercator(longitude, latitude)
        return self.with_centre(xc, yc)
    
    def to_aspect(self, aspect):
        """Return a new instance with the given aspect ratio.  Shrinks the
        rectangle as necessary."""
        output = self._to_aspect(aspect)
        return Extent(output[0],output[1],output[2],output[3], self._project_str)

    def with_absolute_translation(self, dx, dy):
        """Return a new instance translated by this amount.  Clips `y` to the
        allowed region of [0,1].
        
        :param dx: Amount to add to `x` value (on the 0 to 1 scale).
        :param dy: Amount to add to `y` value (on the 0 to 1 scale).
        """
        ymin, ymax = self._ymin + dy, self._ymax + dy
        if ymin < 0:
            ymax -= ymin
            ymin = 0
        if ymax > 1:
            ymin -= (ymax - 1)
            ymax = 1
        return Extent(self._xmin + dx, self._xmax + dx, ymin, ymax, self._project_str)
        
    def with_translation(self, dx, dy):
        """Return a new instance translated by this amount.  The values are
        relative to the current size, so `dx==1` means translate one whole
        rectangle size (to the right).
        
        :param dx: Amount to add to `x` value relative to current width.
        :param dy: Amount to add to `y` value relative to current height.
        """
        dx = dx * (self._xmax - self._xmin)
        dy = dy * (self._ymax - self._ymin)
        return self.with_absolute_translation(dx, dy)

    def with_scaling(self, scale):
        """Return a new instance with the same midpoint, but with the width/
        height divided by `scale`.  So `scale=2` will zoom in."""
        output = self._with_scaling(scale)
        return Extent(output[0],output[1],output[2],output[3], self._project_str)
    

