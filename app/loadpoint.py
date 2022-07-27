from loguru import logger

from app.db import PyObjectId, db_features, db_point_status, get_datetime_to_mongo
from app.sattelite.sentinel2 import get_sentinel2



async def remove_points_already_loaded(points,collection):
    point_status = await db_point_status.find({collection:{'$gt':get_datetime_to_mongo()}}).distinct('_id')
    
    if len(point_status) > 0:
        return set(points) - set(point_status)
    return points

async def get_point():
    logger.debug('start point check')

    points = await db_features.distinct('point_id')

    point_collection = await remove_points_already_loaded(points,'sentinel-s2-l2a-cogs')
    for point in point_collection:
        feature = await db_features.find_one({'point_id': PyObjectId(point)})

        logger.debug(f"run point_id {feature['point_id']}")
        await get_sentinel2('sentinel-s2-l2a-cogs', feature['lon'], feature['lat'], feature['epsg'])
