import os
import sys

from dynaconf import Dynaconf
from loguru import logger


def start_logger():
    type_logger = 'development'
    if os.environ.get('LAPIG_ENV') == 'production':
        type_logger = 'production'
    logger.info(f'The system is operating in mode {type_logger}')


confi_format = '[ {time} | process: {process.id} | {level: <8}] {module}.{function}:{line} {message}'
rotation = '500 MB'


if os.environ.get('LAPIG_ENV') == 'production':
    logger.remove()
    logger.add(sys.stderr, level='INFO', format=confi_format)


logger.add('/data/logs/jobs/jobs.log')
logger.add('/data/logs/jobs/jobs_WARNING.log', level='WARNING')

settings = Dynaconf(
    envvar_prefix='PGRASS',
    settings_files=['settings.toml', '.secrets.toml', '/data/settings.toml'],
    environments=True,
    load_dotenv=True,
)
