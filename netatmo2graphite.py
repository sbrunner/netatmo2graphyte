#!/usr/bin/env python3

"""Get the data on Netatmo website and set the the Graphyte."""

import datetime
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

import graphyte
import lnetatmo
import unidecode

LOG = logging.getLogger("netatmo2graphite")


class TooManyError(Exception):
    """Too many requests."""


def normalize(name: str) -> str:
    """Normalize a name for Graphyte."""
    name = name.replace(" ", "_")
    name = name.replace("(", "_")
    name = name.replace(")", "_")
    name = name.replace("__", "_")
    name = name.strip("_")
    return unidecode.unidecode(name).lower()


def process(state: dict[str, int], authorization: lnetatmo.ClientAuth) -> None:
    """Get the new data on Netatmo website and set the the Graphyte."""
    delta = int(os.environ.get("DAEMON_PROCESS_END_SECONDS", "86400"))
    graphyte.send("run", 1)

    try:
        weather_data = lnetatmo.WeatherStationData(authorization)
    except TypeError as error:
        raise TooManyError from error

    for station in weather_data.stations.values():
        station_name = station["home_name"]
        LOG.info("Station '%s'", station_name)

        modules = [station] + station["modules"]

        for module in modules:
            for data_type in [
                "wifi_status",
                "battery_percent",
                "rf_status",
                "battery_vp",
            ]:
                if data_type in module:
                    key = (
                        f"status.{normalize(station_name)}.{normalize(module['module_name'])}."
                        f"{normalize(data_type)}"
                    )
                    LOG.debug("Key: %s = %s", key, module[data_type])
                    graphyte.send(key, module[data_type])
            for data_type in [
                "last_setup",
                "last_status_store",
                "last_upgrade",
                "last_message",
                "last_seen",
                "date_setup",
            ]:
                if data_type in module:
                    key = (
                        f"dates.{normalize(station_name)}.{normalize(module['module_name'])}."
                        f"{normalize(data_type)}"
                    )
                    LOG.debug("Key: %s = %s", key, module[data_type])
                    graphyte.send(key, module[data_type])
            for data_type in [
                "firmware",
            ]:
                if data_type in module:
                    key = (
                        f"other.{normalize(station_name)}.{normalize(module['module_name'])}."
                        f"{normalize(data_type)}"
                    )
                    LOG.debug("Key: %s = %s", key, module[data_type])
                    graphyte.send(key, module[data_type])

            if "place" in module:
                key = (
                    f"other.{normalize(station_name)}.{normalize(module['module_name'])}."
                    f"{normalize('altitude')}"
                )
                LOG.debug("Key: %s = %s", key, module["place"]["altitude"])
                graphyte.send(key, module["place"]["altitude"])

            for data_type in module["data_type"]:
                key = (
                    f"data.{normalize(station_name)}.{normalize(module['module_name'])}."
                    f"{normalize(data_type)}"
                )
                LOG.info("Key %s", key)

                while True:
                    LOG.debug(
                        "Get measure for %s, from %r",
                        key,
                        datetime.datetime.fromtimestamp(
                            state.get(
                                key,
                                float(os.environ.get("DAEMON_DEFAULT_TIMESTAMP", "0")),
                            ),
                            tz=datetime.timezone.utc,
                        ),
                    )
                    measures = weather_data.getMeasure(
                        device_id=station["_id"],
                        scale="max",  # max
                        mtype=data_type,
                        module_id=module["_id"],
                        date_begin=state.get(key, float(os.environ.get("DAEMON_DEFAULT_TIMESTAMP", "0"))),
                    )
                    if measures is None:
                        # Netatmo error
                        LOG.error("Exit on Netatmo error 1")
                        sys.exit(1)
                    if not measures["body"]:
                        # No more data
                        break
                    if isinstance(measures["body"], list):
                        LOG.error("Error: %r", measures["body"][0])
                        sys.exit(1)
                    break_ = False
                    for time_str, values in measures["body"].items():
                        time_int = int(time_str)
                        if key in state and state[key] < time_int - int(
                            os.environ.get("DAEMON_PROCESS_MAX_MISSING_SECONDS", str(86400 * 7)),
                        ):
                            LOG.info(
                                "Ignore from date: %r, current: %r, diff: %f",
                                datetime.datetime.fromtimestamp(time_int, tz=datetime.timezone.utc),
                                datetime.datetime.fromtimestamp(state[key], tz=datetime.timezone.utc),
                                time_int - state[key],
                            )
                            state[key] += int(os.environ.get("DAEMON_PROCESS_ADD_ON_IGNORE_SECONDS", "3600"))
                            break_ = True
                            break
                        for value in values:
                            if value is not None:
                                graphyte.send(
                                    key,
                                    value,
                                    timestamp=time_int,
                                )
                        state[key] = time_int

                    LOG.debug(
                        "Save state %s: %r",
                        key,
                        datetime.datetime.fromtimestamp(time_int, tz=datetime.timezone.utc),
                    )

                    state_path = Path("/etc/netatmo2graphite/state.json")
                    state_back_path = Path("/etc/netatmo2graphite/state.json.bak")
                    state_tmp_path = Path("/etc/netatmo2graphite/state.json_")
                    with state_tmp_path.open("w", encoding="utf-8") as config_file:
                        config_file.write(json.dumps(state))
                    shutil.move(str(state_path), str(state_back_path))
                    shutil.move(str(state_tmp_path), str(state_path))
                    if break_ or state.get(key, 0) > time.time() - delta:
                        break


def main() -> None:
    """Run the daemon."""
    logging.basicConfig(level=os.environ.get("LOGLEVEL", logging.INFO))

    graphyte.init(os.environ["GRAPHITE_HOST"], prefix="netatmo", interval=10)

    graphyte.send("start", 1)

    authorization = lnetatmo.ClientAuth()

    if authorization is None:
        LOG.error("Netatmo login error")
        sys.exit(1)

    state = {}
    state_path = Path("/etc/netatmo2graphite/state.json")
    if state_path.exists():
        with state_path.open(encoding="utf-8") as config_file:
            data = config_file.read()
            try:
                state = json.loads(data)
            except json.decoder.JSONDecodeError:
                LOG.exception("Wrong state: %s", data)

    delay = int(os.environ.get("DAEMON_DELAY_SECONDS", "300"))
    if delay > 0:
        while True:
            time.sleep(delay)
            try:
                process(state, authorization)
            except TooManyError:
                LOG.error("Too many requests, will continue...")  # noqa: TRY400
    else:
        try:
            process(state, authorization)
        except TooManyError:
            LOG.error("Too many requests")  # noqa: TRY400


if __name__ == "__main__":
    main()
