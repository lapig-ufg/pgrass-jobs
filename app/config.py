from dynaconf import Dynaconf
from loguru import logger

logger.add('/data/logs/jobs/jobs.log')
logger.add('/data/logs/jobs/jobs_WARNING.log', level="WARNING")

settings = Dynaconf(
    envvar_prefix="PGRASS",
    settings_files=["settings.toml", ".secrets.toml","/data/settings.toml"],
    environments=True,
    load_dotenv=True
)