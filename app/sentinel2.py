from datetime import datetime
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
from app.model.models import Feature, TimeSerie


def read_pixel(asset, _datetime, url, lon, lat, epsg):
    transformer = Transformer.from_crs(
        'epsg:{epsg}', f'epsg:32721', always_xy=True
    )
    lon_t, lat_t = transformer.transform(lon, lat)
    with rasterio.open(url) as ds:
        pixel_val = next(ds.sample([(lon_t, lat_t)]))
        return (asset, (_datetime, pixel_val[0], url))


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
                except:
                    logger.exception('Error in get data in pixel')
        except:
            logger.exception('Error is tif')
    logger.info(f'Time {timeserires}')
    return timeserires


async def get_sentinel2(lon, lat, epsg, date='2013-05-01'):
    now = datetime.now()
    catalog_url = 'https://earth-search.aws.element84.com/v0'
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
    with Pool(cpu_count()) as works:
        list_timeseries = works.map(
            to_dict, [(item, lon, lat, epsg) for item in search.get_items()]
        )

    point_id = get_id_by_lon_lat(float(lon), float(lat))
    json_timeseries = {}

    for timeserie in list_timeseries:
        for band, informations in timeserie:
            try:
                json_timeseries[band].append(informations)
            except:
                json_timeseries[band] = []

    for band in json_timeseries.copy():
        json_timeseries[band] = sorted(
            json_timeseries[band], key=lambda tup: tup[0]
        )
    logger.debug(json_timeseries)
    timesereis_final = []

    for band in json_timeseries:

        try:
            tmp = TimeSerie(
                point_id=point_id,
                sattelite='sentinel-s2-l2a-cogs',
                sensor='',
                band_index=band,
                datetimes=[
                    information[0] for information in json_timeseries[band]
                ],
                values=[
                    information[1] for information in json_timeseries[band]
                ],
                cogs=[information[2] for information in json_timeseries[band]],
            )
            try:
                result2 = await db_timeseires.insert_one(tmp.mongo())
                logger.debug(f"save in mongo {tmp['_id']}")
            except DuplicateKeyError:
                result2 = await db_timeseires.update_one(
                    {'_id': tmp.id}, {'$set': tmp.mongo()}
                )
                logger.warning('TimeSerie exeiste')
            except:
                logger.exception('fall inset in mongodb')
        except:
            logger.warning(
                [information[1] for information in json_timeseries[band]]
            )
            logger.exception('Time series not created')
