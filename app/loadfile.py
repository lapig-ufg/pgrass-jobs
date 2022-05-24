from unittest.main import main
import geopandas as gpd
from geopandas.tools import sjoin
from app.db import db_features
from app.config import logger
from app.model.models import Feature

regions_tmp = gpd.read_file('zip:///data/base/regions.zip').add_prefix('regions_')
regions = regions_tmp[['regions_MUNICIPIO','regions_ESTADO',
                       'regions_UF','regions_BIOMA','regions_geometry']]
regions = regions.set_geometry('regions_geometry')


async def join_to_json(file_name):
    features = gpd.read_file(file_name)
    df_join = sjoin(features,regions.to_crs(features.crs.to_epsg()))
    epsg = df_join.crs.to_epsg()
    dict_features = []
    for row in df_join.iterfeatures():
        lon, lat = row['geometry']['coordinates']
        properties = row['properties']
        root = {
            'file_name': file_name,
            'gid':row['id'],
            'biome': properties['regions_BIOMA'],
            'lat': lat,
            'lon': lon,
            'epsg': epsg,
            'municipally': properties['regions_MUNICIPIO'],
            'file_name': 'fieldwork_grid_points_goias_2022_v4_mod_only_Pasture 2',
            'state': properties['regions_ESTADO']
        }
        dfields = {}
        for column in features.columns[:-1]:
            dfields[column] = properties[column]
        root['dfields'] = dfields
        f = Feature(**root)
        logger.debug(f)
        dict_features.append(f.mongo())
    
    try:
        result = await db_features.insert_many(dict_features)
    except:
        logger.error(dict_features)
        logger.exception('fala no load file')
    
if __name__ == '__main__':
    join_to_json('/data/update/teste.zip')