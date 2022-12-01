from datetime import datetime, timedelta
from multiprocessing import Pool

from pystac_client import Client
from rasterio._err import CPLE_HttpResponseError

from app.config import logger, settings
from app.db import db_timeseires, schedule_next_update
from app.fuctions import is_tif
from app.model.functions import get_id_by_lon_lat
from app.model.models import TimeSerie



def responce(x):
    assets = x.get_assets()
    _datetime = x.datetime
    del x
    arr = []
    for asset in assets:
        url = assets[asset].href
        if is_tif(url):
            arr.append( {
                'asset': asset,
                'datetime': _datetime,
                'cog':url
             })
    return arr
    

async def get_sentinel2(collection ,lon, lat, epsg, date=settings.DATE_START_QUERY):

    point_id = get_id_by_lon_lat(lon, lat, epsg)
    catalog_url = 'https://earth-search.aws.element84.com/v0'
    root = {
        'point_id': point_id,
        'collection': collection,
        'lon':lon,
        'lat':lat,
        'epsg':epsg
    }
    logger.debug(f'{root}')

    start = await db_timeseires.find_one(root, sort=[('datetime', -1)])

    if start is not None:
        date_start = start['datetime'] + timedelta(days=1)
        
        if (date_start - datetime.now()).days > -30:
            logger.debug(
                f'This date has already been loaded to the _id:{point_id}'
            )
            await schedule_next_update(point_id,collection,next_update=date_start)
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
    with Pool(settings.CORE_TO_STAC) as works:
        list_timeseries = works.map(
            responce, [item for item in search.get_items()]
        )
    del search
    
    def get_TimeSerie(list_timeseries):
        for timeseries in list_timeseries:
            for timeserie in timeseries:
                yield TimeSerie(**root, **timeserie).mongo()

    try:
        resutl = [i for i in get_TimeSerie(list_timeseries)]
        logger.debug(
            f'Save TimeSerie len {len(resutl)} point_id:{resutl[0]["point_id"]}'
        )
        await db_timeseires.insert_many(resutl)
        await schedule_next_update(point_id,collection)
    except Exception as e:
        logger.exception(f'Errro!!! {e}')
        return False
        
    return True
