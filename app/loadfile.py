from multiprocessing import Pool, cpu_count

import geopandas as gpd
from geopandas.tools import sjoin
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from app.config import logger, settings
from app.db import ObjectId, db_dataset, db_features
from app.model.functions import get_id_by_lon_lat

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
    _id = {'_id': ObjectId(properties.pop('__pgrass_gid'))}
    root = {
        'biome': properties['regions_BIOMA'],
        'municipally': properties['regions_MUNICIPIO'],
        'state': properties['regions_ESTADO'],
        'lat': lat,
        'lon': lon,
        'point_id': get_id_by_lon_lat(lat, lon, epsg),
    }

    logger.debug(f'update in db {_id}')
    return (_id, {'$set': root})


def __add_infos_to_doc__(dataset_id, docs, columns, epsg):
    regions_espg = regions.to_crs(epsg)
    logger.info(f'Add information in the document _id:{dataset_id}')

    gdf = gpd.GeoDataFrame.from_features(docs).set_geometry('geometry')
    gdf = gdf.set_crs(epsg)
    logger.info(f'Doing the sjoin in the document _id:{dataset_id}')
    df_join = sjoin(gdf, regions_espg)
    logger.info(f'FINISHED the sjoin in the document _id:{dataset_id}')
    
    with Pool(cpu_count() - 2) as work:
        result = work.map(
            create_feture, [(row, epsg) for row in df_join.iterfeatures()]
        )

    return result


async def get_in_quee():
    dataset_ids = await db_features.distinct(
        'dataset_id', {'municipally': {'$exists': False}}
    )
    if len(dataset_ids) > 0:
        for dataset_id in dataset_ids:
            try:
                dataset = await db_dataset.find_one(
                    {'_id': dataset_id}, {'epsg': 1, 'columns': 1, '_id': 0}
                )
                document = {dataset_id: {'docs': [], **dataset}}
                async for doc in db_features.find(
                    {
                        'dataset_id': dataset_id,
                        'municipally': {'$exists': False},
                    }
                ):
                    document[dataset_id]['docs'].append(doc)

                feature_update = __add_infos_to_doc__(
                    dataset_id, **document[dataset_id]
                )

                for _id, values in feature_update:
                    logger.debug(f'save in db {_id}')
                    await db_features.update_one(_id, values)

            except Exception as e:
                logger.exception(f'Error in loadfile {e}')

    else:
        logger.info(f'Todos os dados foram processado')
