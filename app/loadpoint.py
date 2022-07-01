from datetime import datetime, timedelta

import py
import pytz
from loguru import logger

from app.db import PyObjectId, db_features, get_datetime_to_mongo
from app.sentinel2 import get_sentinel2


async def get_point():
    runs = []
    logger.debug('start point check')

    points = await db_features.distinct('point_id')

    for point in points:
        feature = await db_features.find_one({'point_id': PyObjectId(point)})

        logger.debug(f"run point_id {feature['point_id']}")
        coordinate = await get_sentinel2(
            feature['lon'], feature['lat'], feature['epsg']
        )
