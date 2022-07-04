

import geopandas as gpd
from geopandas.tools import sjoin

from app.config import logger, settings
from app.db import PyObjectId, db_features, db_dataset
from app.model.functions import get_id_by_lon_lat
from multiprocessing import Pool, cpu_count
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

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

def create_feture(args):
    row, epsg = args
    lon, lat = row['geometry']['coordinates']
    properties = row['properties']
    _id = PyObjectId(properties.pop('__pgrass_gid'))
    root = {
        'biome': properties['regions_BIOMA'],
        'municipally': properties['regions_MUNICIPIO'],
        'state': properties['regions_ESTADO'],
        'lat': lat,
        'lon': lon,
        'point_id':get_id_by_lon_lat(lat,lon, epsg)
    }
    logger.debug(f'update in db {_id}')
    return UpdateOne({'_id':_id}, {'$set':root})

def __add_infos_to_doc__(dataset_id,docs,columns,epsg ):
    regions_espg = regions.to_crs(epsg)
    logger.info(f'Add information in the document _id:{dataset_id}')

    gdf = gpd.GeoDataFrame.from_features(docs).set_geometry('geometry')
    gdf = gdf.set_crs(epsg)

    df_join = sjoin(gdf, regions_espg)
    with Pool(cpu_count()* 2) as work:   
        result = work.map(create_feture, [(row,epsg ) for row in df_join.iterfeatures()])
    
    return  result
    


def save_in_db(save):
    logger.debug(f"save in db {save}")
    client = MongoClient(settings.MONGODB_URL,maxPoolSize=10000)
    db = client.pgrss
    db.features.update_one(*save)

    
def list_to_matrix(informations):
  matrix = []
  row = []
  for i, information in enumerate(informations):
    if i == 0 or i % 10000:
      row.append(information)
    else:
      row.append(information)
      matrix.append(row)
      row = []
  if len(row) > 0:
    matrix.append(row)
    row = []

  return matrix

async def get_in_quee():
    dataset_ids = await db_features.distinct(
            'dataset_id', {'municipally': {'$exists': False}}
        )
    if len(dataset_ids) > 0:
        for dataset_id in dataset_ids:
            try:
                dataset = await db_dataset.find_one({'_id':dataset_id},{ 'epsg': 1, 'columns': 1 ,'_id':0})
                document = {dataset_id:{
                    'docs':[],
                    **dataset}}
                async for doc in db_features.find({'dataset_id':dataset_id,'municipally': {'$exists': False}}):
                    document[dataset_id]['docs'].append(doc)
                feature_update =__add_infos_to_doc__(dataset_id,**document[dataset_id])
                client = MongoClient(settings.MONGODB_URL,maxPoolSize=10000)
                db = client.pgrss
                try:
                    result =  db.features.bulk_write(feature_update)
                    logger.info(f'Save bulk in db {result.bulk_api_result}')
                except BulkWriteError as bwe:
                    logger.exception(bwe.details)
                
                
                
            except Exception as e:
                logger.exception(f'Error in loadfile {e}')
                
        
    else:
        logger.info(f'Todos os dados foram processado')
