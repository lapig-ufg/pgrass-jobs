import asyncio

from app.db import add_metadata_collections, client
from app.config import settings
from app.loadfile import get_in_quee
from app.loadpoint import get_point


def start():
    loop = client.get_io_loop()
    for link in settings.COLLECTIONS:
        loop.run_until_complete(add_metadata_collections(link))
    
    loop.run_until_complete(get_in_quee())
    loop.run_until_complete(get_point())




if '__main__' == __name__:
    start()

    
