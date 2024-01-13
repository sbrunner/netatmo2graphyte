FROM ubuntu:22.04 AS base
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get upgrade --yes \
    && apt-get install --yes --no-install-recommends python3-pip binutils

WORKDIR /app

COPY requirements.txt /tmp/
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=/tmp/requirements.txt

# Used to convert the locked packages by poetry to pip requirements format
FROM base as poetry

# Install Poetry
WORKDIR /tmp
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=requirements.txt

# Do the conversion
COPY poetry.lock pyproject.toml ./
RUN poetry export --output=requirements.txt \
    && poetry export --with=dev --output=requirements-dev.txt

FROM base AS checker

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    python3 -m pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements-dev.txt

FROM base AS run

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    python3 -m pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements.txt \
    && python3 -m pip freeze > /requirements.txt

RUN python3 -m compileall -q /usr/local/lib/python3.* && pip freeze --all > /requirements.txt

COPY netatmo2graphite /usr/bin/
CMD ["netatmo2graphite"]

RUN echo '{}' > ~/.netatmo.credentials

ENV \
    LOGLEVEL=INFO \
    GRAPHITE_HOST=127.0.0.1 \
    NETATMO_CLIENT_PASSWORD=REQUIRED \
    NETATMO_CLIENT_USERNAME=REQUIRED \
    NETATMO_CLIENT_SECRET=REQUIRED \
    NETATMO_CLIENT_ID=REQUIRED \
    DAEMON_DELAY_SECONDS=60
