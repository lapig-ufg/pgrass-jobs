###############################################
# Base Image
###############################################
FROM python:3.10-slim as python-base

ENV LAPIG_ENV='dev' \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.0.5 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
###############################################
# Builder Image
###############################################
FROM python-base as builder-base
RUN apt-get update && apt-get install --no-install-recommends -y curl build-essential libspatialindex-dev

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN pip3 install poetry 

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --no-interaction --no-ansi

###############################################
# Production Image
###############################################
FROM python-base as production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

WORKDIR /APP

# Clone app and npm install on server
ENV URL_TO_APPLICATION_GITHUB="https://github.com/lapig-ufg/pgrass-jobs.git"
ENV BRANCH="main"

RUN apt-get update && apt-get install -y git make && mkdir -p /APP && cd /APP && git clone -b ${BRANCH} ${URL_TO_APPLICATION_GITHUB} && \
    rm -rf /var/lib/apt/lists/*


CMD sh -c "cd /APP/pgrass-jobs && python start_sched.py"