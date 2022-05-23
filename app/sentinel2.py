from pyproj import Transformer
import rasterio
from app.config import logger
from datetime import datetime
from pystac_client import Client
from multiprocessing import Pool, cpu_count
from app.model.point import TimeSerie, Point
from app.db import db_points, db_timeseires
from pydantic import schema_json_of
from pymongo.errors import DuplicateKeyError

def read_pixel(asset, _datetime, url, lon, lat, epsg='32721'):
    transformer = Transformer.from_crs("epsg:4326", f"epsg:{epsg}", always_xy=True)
    lon_t, lat_t = transformer.transform(lon, lat)
    with rasterio.open(url) as ds:
        pixel_val = next(ds.sample([(lon_t, lat_t)]))
        return (asset, (_datetime, pixel_val[0], url))

def to_dict(args):
    item,lon,lat = args
    assets = item.get_assets()
    timeserires = []

    for asset in assets:
        if assets[asset].roles[0] == 'data':
            timeserires.append(
                read_pixel(asset, item.datetime, assets[asset].href,lon,lat)
            )
            logger.debug(f'cooder:{(lon,lat)} asset:{asset} url:{assets[asset].href}')
    
    logger.info(f'Time {timeserires}')
    return timeserires


async def get_sentinel2(lon,lat,date='2022-05-01'):
    now = datetime.now()
    catalog_url = "https://earth-search.aws.element84.com/v0"
    catalog = Client.open(catalog_url)

    # Image retrieval parameters
    intersects_dict = dict(type="Point", coordinates=(lon,lat))
    dates =  f'{date}/{now.strftime("%Y-%m-%d")}'

    search = catalog.search(
        collections=["sentinel-s2-l2a-cogs"],
        intersects=intersects_dict,
        datetime=dates
        )
    logger.info(f'Chamando to_dict')
    with Pool(cpu_count()) as works:
        list_timeseries = works.map(to_dict, [(item,lon,lat) for item in search.get_items()])

    point = Point(
        lat = float(lat),
        lon = float (lon),

    )
    json_timeseries = {}

    for timeserie in list_timeseries:
        for band, informations in timeserie:
            try:
                json_timeseries[band].append(informations)
            except:
                json_timeseries[band] = []
                
    for band in json_timeseries.copy():
        json_timeseries[band] = sorted(json_timeseries[band], key=lambda tup: tup[0] )
    logger.debug(json_timeseries)
    timesereis_final = []
    
    for band in json_timeseries:
         
        try:
            tmp = TimeSerie(
                ts_source_id = 1,
                point_id = point.id,
                sattelite = 'sentinel-s2-l2a-cogs',
                sensor = '',
                band_index = band,
                datetimes = [information[0] for  information in  json_timeseries[band]],
                values = [information[1] for  information in  json_timeseries[band]],
                cogs = [information[2] for  information in  json_timeseries[band]]
                )      
            timesereis_final.append(tmp.mongo())
        except:
            logger.warning([information[1] for  information in  json_timeseries[band]])
            logger.exception('Time series not created')      
    logger.debug(f'{json_timeseries}')
    try:
        result = await db_points.insert_one(point.mongo())
        #t = await teste.insert_one({'teste':'io'})
        #logger.debug(f'insert {t.inserted_id}')
    except DuplicateKeyError as e:
        logger.warning('point Duplicado {e}')
    except Exception as e:
        logger.exception('fall inset in mongodb')
    
    try:
        result2 = await db_timeseires.insert_many(timesereis_final)
    except Exception as e:
        logger.exception('fall inset in mongodb')
    