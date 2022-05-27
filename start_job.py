from app.loadpoint import get_point
from app.db import client
from app.loadfile import join_to_json
import asyncio
from app.db import teste




if '__main__' == __name__:
    
    
    loop = client.get_io_loop()
    #loop.run_until_complete(join_to_json('/data/update/teste.zip'))
    loop.run_until_complete(get_point())