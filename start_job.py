import asyncio

from app.db import client, teste
from app.loadfile import get_in_quee
from app.loadpoint import get_point

if '__main__' == __name__:

    loop = client.get_io_loop()
    loop.run_until_complete(get_in_quee())
    loop.run_until_complete(get_point())
