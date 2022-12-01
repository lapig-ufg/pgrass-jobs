from datetime import datetime, timedelta
from app.config import logger, settings
import motor.motor_asyncio
import pytz
from bson import ObjectId
from pydantic import BaseConfig, BaseModel
import pymongo
from requests import get

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)

db = client.pgrass

db_points = db.points
db_timeseires = db.timeseires
db_features = db.features
db_dataset = db.dataset
db_point_status = db.point_status
db_collections = db.collections

async def add_metadata_collections(url):
    try:
        collection = get(url).json()
        if '_id' not in collection and 'id' in collection:
            collection['_id'] = collection.pop('id')
        await db.collections.insert_one(collection)
        logger.debug(f'Collection add {url}')
    except pymongo.errors.DuplicateKeyError:
        ...
    

async def schedule_next_update(point_id,collection,next_update=datetime.now()):
    next_update = (next_update.replace(
        hour=23,
        minute=59,
        second=59, 
        microsecond=0
        ) + timedelta(days=15)).astimezone(pytz.utc).isoformat()
    try:
        await db_point_status.insert_one({'_id':point_id,collection:next_update})
        logger.debug(f'_id:{point_id} collection:{next_update}')
    except pymongo.errors.DuplicateKeyError:
        logger.debug(f'update _id:{point_id} collection:{next_update}')
        await db_point_status.update_one( {'_id':point_id},{'$set':{collection:next_update}})
        
    
    




def get_datetime_to_mongo():
    return datetime.now().astimezone(pytz.utc).isoformat()


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class MongoModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.astimezone(pytz.utc).isoformat(),
            ObjectId: lambda oid: str(oid),
        }

    @classmethod
    def from_mongo(cls, data: dict):
        """We must convert _id into "id"."""
        if not data:
            return data
        _id = data.pop('_id', None)
        return cls(**dict(data, id=_id))

    def mongo(self, **kwargs):
        exclude_unset = kwargs.pop('exclude_unset', True)
        by_alias = kwargs.pop('by_alias', True)

        parsed = self.dict(
            exclude_unset=exclude_unset,
            by_alias=by_alias,
            **kwargs,
        )

        # Mongo uses `_id` as default key. We should stick to that as well.
        if '_id' not in parsed and 'id' in parsed:
            parsed['_id'] = parsed.pop('id')

        return parsed
