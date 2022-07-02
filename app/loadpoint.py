from loguru import logger

from app.db import PyObjectId, db_features
from app.sattelite.sentinel2 import get_sentinel2


async def get_point():
    logger.debug('start point check')

    points = await db_features.distinct('point_id')

    for point in points:
        feature = await db_features.find_one({'point_id': PyObjectId(point)})

        logger.debug(f"run point_id {feature['point_id']}")
        await get_sentinel2(
            feature['lon'], feature['lat'], feature['epsg']
        )
