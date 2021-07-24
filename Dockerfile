FROM ubuntu

RUN apt-get update
RUN apt-get install --yes python3-pip
RUN python3 -m pip install lnetatmo graphyte requests unidecode

COPY netatmo2graphyte /usr/bin/
CMD ["netatmo2graphyte"]

ENV \
  LOGLEVEL=INFO \
  GRAPHYTE_HOST=127.0.0.1 \
  NETATMO_CLIENT_PASSWORD=REQUIRED \
  NETATMO_CLIENT_USERNAME=REQUIRED \
  NETATMO_CLIENT_SECRET=REQUIRED \
  NETATMO_CLIENT_ID=REQUIRED \
  DAEMON_DELAY_SECONDS=60
