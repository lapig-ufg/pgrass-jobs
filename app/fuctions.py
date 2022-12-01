from pathlib import Path
from functools import lru_cache

import rasterio
from pyproj import Transformer


from app.config import logger


def is_tif(file_name):
    return Path(file_name).suffix.capitalize() in ['.tif', '.tiff']



@lru_cache(maxsize=512)
def __transformer(lon,lat, point_epsg,raster_epsg):
    transformer = Transformer.from_crs(
        f'epsg:{point_epsg}', f'{raster_epsg}', always_xy=True
    )
    return transformer.transform(lon, lat)


def read_pixel(asset, _datetime, url, lon, lat, epsg): 
    with rasterio.open(url) as ds:
        lon_t, lat_t = __transformer(lon, lat, epsg, ds.crs['init'])
        pixel_val = (next(ds.sample([(lon_t, lat_t)]))).tolist()
        logger.debug(f"band:{asset}, cog:{url}, cood([{lon}, {lon_t} ], [{lat}, {lat_t} ], {epsg}), pixel:{pixel_val}")
        if len(pixel_val) == 1:
            pixel_val = pixel_val[0]
        
        return {
            'asset': asset,
            'datetime': _datetime,
            'value': pixel_val,
            'cog': url,
        }
