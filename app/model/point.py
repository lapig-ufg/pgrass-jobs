
from pydantic import Field, HttpUrl
from enum import Enum
from app.db import PyObjectId, MongoModel
from datetime import datetime
from typing import Dict, List, Union
from bson import ObjectId

from app.model.functions import get_id




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
class Point(MongoModel):
    biome: str
    municipally:str
    state: str
    point_id: PyObjectId = Field(default_factory=PyObjectId)
    lat: float
    lon: float
    geometry: str = ''
    epsg: int
    dfields: Dict
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        from hashlib import shake_256
        self.point_id = get_id(f"{self.lon:.5f}{self.lat:.5f}")
        self.geometry = f'POINT ({self.lon:.5f} {self.lat:.5f},)'

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
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ts_source_id: int
    point_id: PyObjectId = Field(default_factory=PyObjectId)
    sattelite: SatelliteEnum
    sensor: str = ''
    band_index: str
    datetimes: List[datetime]
    values: List[Union[int,float]]
    cogs:List[HttpUrl]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.id = get_id(f"{self.ts_source_id}{self.point_id}{self.sattelite}{self.band_index}{self.sensor}")
    
        
