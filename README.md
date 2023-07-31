# Netatmo 2 Graphite

Tool used to export your [Netatmo](https://www.netatmo.com) data to [Graphite](https://graphiteapp.org/).

Contrary to [netatmo-exporter](https://github.com/xperimental/netatmo-exporter) all the history is imported.

To run use:

```
docker run --detatch --volume=state:/etc/netatmo2graphite \
 --env=GRAPHITE_HOST=<host> \
 --env=CLIENT_SECRET=<client secret> \
 --env=CLIENT_ID=<client id> \
 --env=REFRESH_TOKEN=<refresh token> \
 sbrunner/netatmo2graphite
```

Get Netatmo client credentials: This application tries to get data from the Netatmo API. For that to work you will need to create an application in the [Netatmo developer console](https://dev.netatmo.com/apps/), so that you can get the `client id` and `client secret`.

In 'Token generator' create a `read_station` token, the you will obtain the `refresh token`.

Careful: The first import can takes many times

Board: https://grafana.com/grafana/dashboards/14771

Recommended Graphite configuration, in `storage-schemas.conf` add:

```
[netatmo_data]
pattern = ^netatmo\.data\.
retentions = 1m:15d,1h:100y

[netatmo_status]
pattern = ^netatmo\.status\.
retentions = 10m:2d,1d:10y

[netatmo_dates]
pattern = ^netatmo\.dates\.
retentions = 10m:2d,1d:10y

[netatmo_other]
pattern = ^netatmo\.other\.
retentions = 10m:2d,1d:10y
```

in `storage-schemas.conf` add:

```
[netatmo]
pattern = netatmo\..*
xFilesFactor = 0
aggregationMethod = average
```

## Contributing

Install the pre-commit hooks:

```bash
pip install pre-commit
pre-commit install --allow-missing-config
```
