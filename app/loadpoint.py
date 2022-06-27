from loguru import logger
from app.db import db_features
from app.sentinel2 import get_sentinel2
from app.db import get_datetime_to_mongo
import pytz
from datetime import datetime, timedelta

async def get_point():
    runs = []
    logger.debug('start point check')
    
    async for feature  in db_features.find({
        "next_update" : {"$lte": datetime.now().astimezone(pytz.utc) }
    }):
        import web_pdb; web_pdb.set_trace()
        if not str(feature['point_id']) in runs:
            logger.debug(f"run point_id {feature['point_id']}")
            coordinate = await get_sentinel2(feature['lon'],feature['lat'])
            runs.append(str(feature['point_id']))
            next_update =  (datetime.now() + timedelta(days=15)).astimezone(pytz.utc).isoformat()
            await db_features.update_one(
                    {'_id': feature['_id']}, 
                    {'$set': {'next_update': next_update}}
                )
            logger.debug(f"{feature['_id']} next_update {next_update}")
        else:
            logger.debug(f"ignoaradp point_id {feature['point_id']}")
