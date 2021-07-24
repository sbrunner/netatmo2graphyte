Run:

```
docker run --detatch --volume=state:/etc/netatmo2graphyte \
 --env=GRAPHYTE_HOST=<host> \
 --env=NETATMO_CLIENT_PASSWORD=<password> \
 --env=NETATMO_CLIENT_USERNAME=<username> \
 --env=NETATMO_CLIENT_SECRET=<client secret> \
 --env=NETATMO_CLIENT_ID=<client id> \
 --env=DAEMON_DELAY_SECONDS=300 \
 sbrunner/netatmo2graphyte
```
