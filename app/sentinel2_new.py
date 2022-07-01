from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count

import rasterio
from pymongo.errors import DuplicateKeyError
from pyproj import Transformer
from pystac_client import Client
from rasterio._err import CPLE_HttpResponseError

from app.config import logger
from app.db import db_points, db_timeseires
from app.fuctions import is_tif
from app.model.functions import get_id_by_lon_lat
from app.model.models import Feature, TimeSerie, TimeSerieNew


def read_pixel(asset, _datetime, url, lon, lat, epsg):
    transformer = Transformer.from_crs(
        f'epsg:{epsg}', f'epsg:32721', always_xy=True
    )
    lon_t, lat_t = transformer.transform(lon, lat)
    with rasterio.open(url) as ds:
        pixel_val = next(ds.sample([(lon_t, lat_t)]))
        return {
            'asset':asset, 
            'datetime':_datetime, 
            'value':pixel_val[0], 
            'cog':url}


def to_dict(args):
    item, lon, lat, epsg = args
    assets = item.get_assets()
    timeserires = []

    for asset in assets:
        try:
            if is_tif(assets[asset].href):
                try:
                    timeserires.append(
                        read_pixel(
                            asset, item.datetime, assets[asset].href, lon, lat, epsg
                        )
                    )
                    logger.debug(
                        f'cooder:{(lon,lat,epsg)} url:{assets[asset].href}'
                    )
                except CPLE_HttpResponseError:
                    logger.error(
                        f'url:{assets[asset].href} lon:{lon} lat:{lat} '
                    )
                except:
                    logger.exception('Error in get data in pixel')
        except:
            logger.exception('Error is tif')
    logger.debug(f'Time {timeserires}')
    return timeserires


async def get_sentinel2(lon, lat, epsg, date='2000-06-15'):
    
    point_id = get_id_by_lon_lat(float(lon), float(lat), epsg)
    catalog_url = 'https://earth-search.aws.element84.com/v0'
    root = {
        'point_id':point_id,
        'sattelite':'sentinel-s2-l2a-cogs',
        'sensor':'',
        'catalog_url':catalog_url
    }
    logger.debug(f'{root}')
    
    start = await db_timeseires.find_one(root, sort=[('datetime',-1)])
    
    if start is not None:
        date_start = start['datetime'] + timedelta(days=1)
        if(date_start - timedelta(days=15) < datetime.now() ):
            logger.debug(f'This date has already been loaded to the _id:{point_id}')
            return False
        date = date_start.strftime("%Y-%m-%d")
    
    
    logger.debug(f'data inicial {date}')
    now = datetime.now()
    
    catalog = Client.open(catalog_url)

    # Image retrieval parameters
    intersects_dict = dict(type='Point', coordinates=(lon, lat))
    dates = f'{date}/{now.strftime("%Y-%m-%d")}'

    search = catalog.search(
        collections=['sentinel-s2-l2a-cogs'],
        intersects=intersects_dict,
        datetime=dates,
    )
    logger.info(f'Chamando to_dict')
    with Pool(cpu_count()-2) as works:
        list_timeseries = works.map(
            to_dict, [(item, lon, lat,epsg) for item in search.get_items()]
        )

    resutl = [TimeSerieNew(**root,**timeserie).mongo()  for timeseries in list_timeseries for timeserie in timeseries ]
    
    result2 = await db_timeseires.insert_many(resutl)
    return True

    
    
