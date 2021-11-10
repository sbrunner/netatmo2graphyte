FROM ubuntu:20.04 AS base

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install --yes --no-install-recommends python3-pip binutils && \
    apt-get clean && \
    rm -r /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt && \
    rm --recursive --force /tmp/*

COPY Pipfile Pipfile.lock ./
RUN pipenv sync --system --clear && \
    rm --recursive --force /usr/local/lib/python3.*/dist-packages/tests/ /tmp/* /root/.cache/* && \
    (strip /usr/local/lib/python3.*/dist-packages/*/*.so || true)


FROM base AS checker

RUN \
    pipenv sync --system --clear --dev && \
    rm --recursive --force /tmp/* /root/.cache/*

FROM base AS run

RUN python3 -m compileall -q /usr/local/lib/python3.* -x '/pipenv/'

COPY netatmo2graphite /usr/bin/
CMD ["netatmo2graphite"]

ENV \
  LOGLEVEL=INFO \
  GRAPHITE_HOST=127.0.0.1 \
  NETATMO_CLIENT_PASSWORD=REQUIRED \
  NETATMO_CLIENT_USERNAME=REQUIRED \
  NETATMO_CLIENT_SECRET=REQUIRED \
  NETATMO_CLIENT_ID=REQUIRED \
  DAEMON_DELAY_SECONDS=60
