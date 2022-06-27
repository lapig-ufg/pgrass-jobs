from loguru import logger
from app.db import db_features
from app.sentinel2 import get_sentinel2

async def get_point():
    runs = []
    async for feature  in db_features.find():
        if not str(feature['point_id']) in runs:
            logger.debug(f"run point_id {feature['point_id']}")
            coordinate = await get_sentinel2(feature['lon'],feature['lat'])
            runs.append(str(feature['point_id']))
            
        else:
            logger.debug(f"ignoaradp point_id {feature['point_id']}")