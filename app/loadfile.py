from unittest.main import main
import geopandas as gpd
from geopandas.tools import sjoin
from app.db import db_features, db_jobs
from app.config import logger
from app.model.models import Feature

regions_tmp = gpd.read_file('zip:///data/base/regions.zip').add_prefix('regions_')
regions = regions_tmp[['regions_MUNICIPIO','regions_ESTADO',
                       'regions_UF','regions_BIOMA','regions_geometry']]
regions = regions.set_geometry('regions_geometry')


async def get_in_quee():
    async for doc in db_jobs.find({'job_status':'IN_QUEUE'}):
        root ={
        "file_name":doc['file_name'],
        "dataset_id":doc['_id'],
        "columns":doc['columns'],
        }
        gdf = gpd.GeoDataFrame.from_features(doc["features"]).set_geometry('geometry')
        gdf = gdf.set_crs(doc['epsg'])
        status = await join_to_json(gdf,root)
        if status == True:
            result = await db_jobs.update_one(
                    {'_id': doc['_id']}, 
                    {'$set': {'job_status': 'COMPLETE'}}
                )




async def join_to_json(features,root_doc):
    df_join = sjoin(features,regions.to_crs(features.crs.to_epsg()))
    epsg = df_join.crs.to_epsg()
    dict_features = []
    for row in df_join.iterfeatures():
        lon, lat = row['geometry']['coordinates']
        properties = row['properties']
        root = {**root_doc,
            'gid':row['id'],
            'biome': properties['regions_BIOMA'],
            'lat': lat,
            'lon': lon,
            'epsg':epsg,
            'municipally': properties['regions_MUNICIPIO'],
            'state': properties['regions_ESTADO']
        }
        dfields = {}
        for column in features.columns:
            if not column == 'geometry':
                dfields[column] = properties[column]
        root['dfields'] = dfields
        f = Feature(**root)
        logger.debug(f)
        dict_features.append(f.mongo())
    
    try:
        result = await db_features.insert_many(dict_features)
        return True
    except:
        logger.error(dict_features)
        logger.exception('fala no load file')
        return False
    
if __name__ == '__main__':
    join_to_json('/data/update/teste.zip')