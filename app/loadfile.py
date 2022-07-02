
from datetime import datetime, timedelta
from multiprocessing import Pool
from os import cpu_count
from pymongo import MongoClient
import geopandas as gpd
from geopandas.tools import sjoin

from app.config import logger, settings
from app.db import db_features
from app.model.models import Feature

regions_tmp = gpd.read_file('zip:///data/base/regions.zip').add_prefix(
    'regions_'
)
regions = regions_tmp[
    [
        'regions_MUNICIPIO',
        'regions_ESTADO',
        'regions_UF',
        'regions_BIOMA',
        'regions_geometry',
    ]
]
regions = regions.set_geometry('regions_geometry')


def __add_infos_to_doc__(args):
    doc, regions_espg = args
    logger.info(f'Add information in the document _id:{doc["_id"]}')

    gdf = gpd.GeoDataFrame.from_features([doc]).set_geometry('geometry')
    gdf = gdf.set_crs(doc['epsg'])

    df_join = sjoin(gdf, regions_espg)
    _id = doc['_id']
    epsg = df_join.crs.to_epsg()
    lon = doc['geometry']['coordinates'][0]
    lat = doc['geometry']['coordinates'][1]
    root = {
        **doc,
        'biome': df_join['regions_BIOMA'].iloc[0],
        'lat': lat,
        'lon': lon,
        'epsg': epsg,
        'municipally': df_join['regions_MUNICIPIO'].iloc[0],
        'state': df_join['regions_ESTADO'].iloc[0],
        'next_update': datetime.now() - timedelta(days=30),
    }
    
    return ( _id, {'$set':Feature(**root).mongo()})
    

async def save_buckt(buckets):
    for _id, new_doc in buckets:
        logger.debug(f'Update _id:{_id}')
        await db_features.update_one({'_id':_id},new_doc)

async def get_in_quee():
    docs = [
        doc
        async for doc in db_features.find({'municipally': {'$exists': False}})
    ]
    if len(docs) > 0:
        regions_new_crs = {}
        epsgs = await db_features.distinct(
            'epsg', {'municipally': {'$exists': False}}
        )
        for epsg in epsgs:
            logger.debug(f'{epsg}')
            regions_new_crs[epsg] = regions.to_crs(epsg)

        bucket = []
        for index, doc in enumerate(docs):
            if index > 0 and index % 500 != 0:
                bucket.append((doc, regions_new_crs[doc['epsg']]))
            else:
                with Pool(cpu_count() * 2 ) as works:
                    bucket_result = works.map( __add_infos_to_doc__, bucket)
                await save_buckt(bucket_result)
                bucket = []
                
        if len(bucket) > 0:
            with Pool(cpu_count() * 2) as works:
                bucket_result = works.map( __add_infos_to_doc__, bucket)
            await save_buckt(bucket_result)
        del docs, bucket 
    else:
        logger.info(f'Todos os dados foram processado')
