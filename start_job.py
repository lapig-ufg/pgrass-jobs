from app.loadpoint import get_point
from app.db import client
from app.loadfile import get_in_quee
import asyncio
from app.db import teste




if '__main__' == __name__:
    
    
    loop = client.get_io_loop()
    loop.run_until_complete(get_in_quee())