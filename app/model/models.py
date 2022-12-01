from datetime import datetime
from enum import Enum
from typing import Dict, List, Union, Optional

from pydantic import Field, HttpUrl
from pymongo import MongoClient
from app.config import settings, logger
from app.db import MongoModel, PyObjectId
from app.model.functions import get_id, get_id_by_lon_lat

class ListId(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')


class JobStatusEnum(str, Enum):
    in_queue = 'IN_QUEUE'
    running = 'RUNNING'
    complete = 'COMPLETE'
    canceled = 'CANCELLED'
    error = 'ERROR'


def create_enum_collections():
    collections = {}
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.pgrass
        for collection in db.collections.find({},{'title'}):
            collections[collection['_id']] = collection['_id']
    return collections

def make_enum(name, values):
    _k = _v = None
    class TheEnum(str, Enum):
        nonlocal _k, _v
        for _k, _v in values.items():
            try:
                locals()[_k] = _v
            except:
                logger.exception('Make enum')
    TheEnum.__name__ = name
    return TheEnum        


CollectionsEnum  = make_enum('CollectionsEnum', create_enum_collections())


class Feature(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    dataset_id: PyObjectId
    biome: str
    municipally: str
    state: str
    point_id: PyObjectId
    lat: float
    lon: float
    geometry: dict
    epsg: int
    properties: Dict

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.point_id = get_id_by_lon_lat(self.lon, self.lat, self.epsg)



class TimeSerie(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId)
    point_id: PyObjectId = Field(default_factory=PyObjectId)
    collection: str
    asset: str
    datetime: datetime
    lon: Optional[float]
    lat: Optional[float]
    epsg: Optional[int]
    value: Optional[Union[List[Union[int,float]],int, float]]
    cog: HttpUrl

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.id = get_id(
            f'{self.point_id}{self.asset}{self.cog}'
        )
