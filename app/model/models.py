from datetime import datetime
from enum import Enum
from typing import Dict, List, Union

from pydantic import Field, HttpUrl

from app.db import MongoModel, PyObjectId
from app.model.functions import get_id, get_id_by_lon_lat


class JobStatusEnum(str, Enum):
    in_queue = 'IN_QUEUE'
    running = 'RUNNING'
    complete = 'COMPLETE'
    canceled = 'CANCELLED'
    error = 'ERROR'


class SatelliteEnum(str, Enum):
    sentinel_s2_l2a_cogs = 'sentinel-s2-l2a-cogs'


"""
{
		"_id": "pontos_go_1",
		"dataset_id": 1,
		"biome": "cerrado",
		"municipally": "Goiânia",
		"state": "Goiás",
		"lon": -14.5,
		"lat": -45.4,
		"point_id": "XXXXXXXXXXXXXXX",
		"dfields": {
			"degradation_stage": "degraded",
		}
	},
"""


class Feature(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    dataset_id: PyObjectId
    biome: str
    municipally: str
    state: str
    point_id: PyObjectId = Field(default_factory=PyObjectId)
    lat: float
    lon: float
    geometry: dict
    epsg: int
    properties: Dict

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.point_id = get_id_by_lon_lat(self.lon, self.lat, self.epsg)


"""
	{
		"point_id": "XXXXXXXXXXXXXXX",
		"ts_source_id": "1",
		"sattelite": "landsat",
		"sensor": "oli",
		"band_index": "ndvi",
		"datetimes": [
			"2000-01-01",
			"2000-01-16",
			"..."
		],
		"values": [
			0.2,
			0.6,
			"..."
		],
		"cogs": [
			"*.tif",
			"*.tif"
			"..."
		]
	}
"""




class TimeSerie(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')
    ts_source_id: int
    point_id: PyObjectId = Field(default_factory=PyObjectId)
    sattelite: SatelliteEnum
    sensor: str = ''
    band_index: str
    datetimes: List[datetime]
    values: List[Union[int, float]]
    cogs: List[HttpUrl]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.id = get_id(
            f'{self.ts_source_id}{self.point_id}{self.sattelite}{self.band_index}{self.sensor}'
        )


class TimeSerieNew(MongoModel):
    id: PyObjectId = Field(default_factory=PyObjectId)
    point_id: PyObjectId = Field(default_factory=PyObjectId)
    sattelite: SatelliteEnum
    sensor: str
    catalog_url: HttpUrl
    asset: str
    datetime: datetime
    value: Union[List[Union[int,float]],int, float]
    cog: HttpUrl

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.id = get_id(
            f'{self.point_id}{self.sattelite}{self.sensor}{self.asset}{self.cog}'
        )
