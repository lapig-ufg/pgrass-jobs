from datetime import datetime, timedelta
from multiprocessing import Pool

import rasterio
from pyproj import Transformer
from pystac_client import Client
from rasterio._err import CPLE_HttpResponseError

from app.config import logger, settings
from app.db import db_timeseires, schedule_next_update
from app.fuctions import is_tif
from app.model.functions import get_id_by_lon_lat
from app.model.models import TimeSerie
from functools import lru_cache


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
                            asset,
                            item.datetime,
                            assets[asset].href,
                            lon,
                            lat,
                            epsg,
                        )
                    )
                    logger.debug(
                        f'cooder:{(lon,lat,epsg)} url:{assets[asset].href}'
                    )
                except CPLE_HttpResponseError:
                    logger.error(
                        f'url:{assets[asset].href} lon:{lon} lat:{lat} '
                    )
                except Exception as e:
                    logger.exception(f'Error in get data in pixel {e}')
        except Exception as e:
            logger.exception('Error is tif {e}')
    logger.debug(f'Gerado To_dict')
    return timeserires


async def get_sentinel2(collection ,lon, lat, epsg, date=settings.DATE_START_QUERY):

    point_id = get_id_by_lon_lat(lon, lat, epsg)
    catalog_url = 'https://earth-search.aws.element84.com/v0'
    root = {
        'point_id': point_id,
        'collection': collection,
    }
    logger.debug(f'{root}')

    start = await db_timeseires.find_one(root, sort=[('datetime', -1)])

    if start is not None:
        date_start = start['datetime'] + timedelta(days=1)
        if date_start - timedelta(days=15) < datetime.now():
            logger.debug(
                f'This date has already been loaded to the _id:{point_id}'
            )
            await schedule_next_update(**root,next_update=date_start)
            return False
        date = date_start.strftime('%Y-%m-%d')

    logger.debug(f'data inicial {date}')
    now = datetime.now()

    catalog = Client.open(catalog_url)

    # Image retrieval parameters
    intersects_dict = dict(type='Point', coordinates=(lon, lat))
    dates = f'{date}/{now.strftime("%Y-%m-%d")}'

    search = catalog.search(
        collections=[collection],
        intersects=intersects_dict,
        datetime=dates,
    )
    logger.info(f'Chamando to_dict')
    with Pool(settings.CORE_TO_DOWNLOAD) as works:
        list_timeseries = works.map(
            to_dict, [(item, lon, lat, epsg) for item in search.get_items()]
        )

    try:
        resutl = [
            TimeSerie(**root, **timeserie).mongo()
            for timeseries in list_timeseries
            for timeserie in timeseries
        ]
        logger.debug(
            f'Save TimeSerie len {len(resutl)} point_id:{resutl[0]["point_id"]}'
        )
        await db_timeseires.insert_many(resutl)
        await schedule_next_update(**root)
    except Exception as e:
        logger.exception(f'Errro!!! {e}')
    return True
