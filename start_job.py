import asyncio
import os
import time
from pyinstrument import Profiler
from pathlib import Path

from app.db import add_metadata_collections, client
from app.config import settings
from app.loadfile import get_in_quee
from app.loadpoint import get_point

PROFILE_ROOT = Path('/data/.profiles')



def start():
    if not os.environ.get('LAPIG_ENV') == 'production':
        profiler = Profiler()
        profiler.start()
    loop = client.get_io_loop()
    for link in settings.COLLECTIONS:
        loop.run_until_complete(add_metadata_collections(link))
    
    loop.run_until_complete(get_in_quee())
    loop.run_until_complete(get_point())
    if not os.environ.get('LAPIG_ENV') == 'production':
        profiler.stop()
        PROFILE_ROOT.mkdir(exist_ok=True)
        results_file = PROFILE_ROOT / f'{time.strftime("%Y%m%d-%H%M%S")}.html'
        with open(results_file, "w", encoding="utf-8") as f_html:
            f_html.write(profiler.output_html())




if '__main__' == __name__:
    start()

    
