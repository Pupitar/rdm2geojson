import os
import json
import argparse
import timeit
from typing import Dict, List, Union, Callable, Type, Any, Optional

import yaml
import MySQLdb as msd
import logging

config = yaml.safe_load(open("config.yml"))

logging.basicConfig(level=config["app"]["log_level"])
log = logging.getLogger(__name__)


def get_db_con() -> msd.connect:
    con = msd.connect(
        host=config["database"]["host"],
        user=config["database"]["user"],
        passwd=config["database"]["password"],
        db=config["database"]["name"],
        connect_timeout=config["database"]["connect_timeout"],
    )

    return con


def get_customs() -> List[Optional[Dict]]:
    customs = []

    for filename in os.scandir(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "customs")
    ):
        if not filename.is_file() or filename.path.endswith(".gitkeep"):
            continue

        with open(filename.path) as f:
            data = json.load(f)

        customs.extend(data["features"])

    return customs


def get_data(args: argparse.Namespace) -> Dict:
    execution_start = timeit.default_timer()

    output = {
        "type": "FeatureCollection",
        "features": get_customs() if args.customs else [],
    }

    con = get_db_con()
    cur = con.cursor()

    def _get_points(list_of_points: list) -> List:
        return [
            [
                round(r["lon"], config["app"]["precision"]),
                round(r["lat"], config["app"]["precision"]),
            ]
            for r in list_of_points
        ]

    def _replace_name(instance_type, instance_name):
        for rule in config["filters"][instance_type]["replace"]:
            instance_name = instance_name.replace(rule[0], rule[1])

        return instance_name

    if args.quest:
        cur.execute(
            """
            SELECT
                name,
                JSON_EXTRACT(data, '$.area')
            FROM
                instance
            WHERE
                `type` = 'auto_quest' AND `name` LIKE %s
            """,
            (config["filters"]["quest"]["enabled"],),
        )

        for row in cur.fetchall():
            row_data = {
                "type": "Feature",
                "properties": {
                    "name": _replace_name("quest", row[0]),
                    "type": "quest",
                    "original_name": row[0],
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [_get_points(json.loads(row[1])[0])],
                },
            }
            output["features"].append(row_data)

    if args.raid:
        cur.execute(
            """
            SELECT
                name,
                JSON_EXTRACT(data, '$.area')
            FROM
                instance
            WHERE
                `type` in ('circle_smart_raid', 'circle_raid') AND `name` LIKE %s
            """,
            (config["filters"]["raid"]["enabled"],),
        )

        for row in cur.fetchall():
            row_data = {
                "type": "Feature",
                "properties": {
                    "name": _replace_name("raid", row[0]),
                    "type": "raid",
                    "original_name": row[0],
                },
                "geometry": {
                    "type": "MultiPoint",
                    "coordinates": _get_points(json.loads(row[1])),
                },
            }
            output["features"].append(row_data)

    if args.iv:
        cur.execute(
            """
            SELECT
                name,
                JSON_EXTRACT(data, '$.area')
            FROM
                instance
            WHERE
                `type` = 'circle_pokemon' AND `name` LIKE %s
            """,
            (config["filters"]["iv"]["enabled"],),
        )

        for row in cur.fetchall():
            row_data = {
                "type": "Feature",
                "properties": {
                    "name": _replace_name("iv", row[0]),
                    "type": "iv",
                    "original_name": row[0],
                },
                "geometry": {
                    "type": "MultiPoint",
                    "coordinates": _get_points(json.loads(row[1])),
                },
            }
            output["features"].append(row_data)

    con.close()

    execution_end = timeit.default_timer()
    log.debug(f"execution of save_sql_data took {execution_end - execution_start} sec")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-q", "--quest", help="Process Quest instances", action="store_true"
    )
    parser.add_argument(
        "-r", "--raid", help="Process Raid instances", action="store_true"
    )
    parser.add_argument("-i", "--iv", help="Process IV instances", action="store_true")
    parser.add_argument("-c", "--customs", help="Include customs", action="store_true")
    parser.add_argument("-o", "--output", help="Output filepath", required=True)
    args = parser.parse_args()

    log.info("rdm2geojson started")

    log.info(f"Processing... Q {args.quest} R {args.raid} I {args.iv} C {args.customs}")

    output_data = get_data(args)
    log.info("Fetched SQL data")

    with open(args.output, "w") as f:
        json.dump(output_data, f)

    log.info(f"Saved output to {args.output}")
