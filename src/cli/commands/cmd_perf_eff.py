from pathlib import Path
import json
import pandas as pd
import logging
from core.transformations import norm_diff
from src.cli.jsonReader import open_json_file
from src.cli.utils import (
    print_error,
    print_info,
    print_rule,
)
from src.cli.exceptions import exceptions
from resources import (
    calculate_measures,
    calculate_subcharacteristics,
    calculate_characteristics,
)


logger = logging.getLogger("msgram")


def command_perf_eff(args):
    try:
        first_release_path = args["first_release"]
        second_release_path = args["second_release"]
    except KeyError as e:
        logger.error(f"KeyError: args[{e}] - non-existent parameters")
        print_error(f"KeyError: args[{e}] - non-existent parameters")
        exit(1)

    measures_input = parse_performance_efficiency_data(
        first_release_path, second_release_path
    )

    calculated_measures = calculate_measures(measures_input)
    subcharacteristics_input = make_subcharacteristics_input(
        calculated_measures["measures"]
    )
    calculated_subcharacteristics = calculate_subcharacteristics(
        subcharacteristics_input
    )
    characteristics_input = make_characteristics_input(
        calculated_subcharacteristics["subcharacteristics"]
    )
    calculated_characteristics = calculate_characteristics(characteristics_input)

    print_characteristic(
        calculated_characteristics, calculated_subcharacteristics, calculated_measures
    )

    print_info(
        "\n[#A9A9A9]Performance efficiency calculation performed successfully![/]\n"
    )

    return


def get_value_by_key(data, key):
    for entity in data:
        if entity["key"] == key:
            return entity["value"]


def make_subcharacteristics_input(calculated_measures):
    return {
        "subcharacteristics": [
            {
                "key": "time_behaviour",
                "measures": [
                    {
                        "key": "response_time",
                        "value": get_value_by_key(calculated_measures, "response_time"),
                        "weight": 100,
                    },
                ],
            },
            {
                "key": "resource_utilization",
                "measures": [
                    {
                        "key": "cpu_utilization",
                        "value": get_value_by_key(
                            calculated_measures, "cpu_utilization"
                        ),
                        "weight": 50,
                    },
                    {
                        "key": "memory_utilization",
                        "value": get_value_by_key(
                            calculated_measures, "memory_utilization"
                        ),
                        "weight": 50,
                    },
                ],
            },
        ]
    }


def make_characteristics_input(calculated_subcharacteristics):
    return {
        "characteristics": [
            {
                "key": "performance_efficiency",
                "subcharacteristics": [
                    {
                        "key": "time_behaviour",
                        "value": float(
                            get_value_by_key(
                                calculated_subcharacteristics, "time_behaviour"
                            )
                        ),
                        "weight": 50,
                    },
                    {
                        "key": "resource_utilization",
                        "value": float(
                            get_value_by_key(
                                calculated_subcharacteristics, "resource_utilization"
                            )
                        ),
                        "weight": 50,
                    },
                ],
            },
        ]
    }


def print_characteristic(
    calculated_characteristics, calculated_subcharacteristics, calculated_measures
):
    obj = {
        "characteristics": [
            {
                "key": "performance_efficiency",
                "values": float(
                    get_value_by_key(
                        calculated_characteristics["characteristics"],
                        "performance_efficiency",
                    )
                ),
                "subcharacteristics": [
                    {
                        "key": "time_behaviour",
                        "value": float(
                            get_value_by_key(
                                calculated_subcharacteristics["subcharacteristics"],
                                "time_behaviour",
                            )
                        ),
                        "measures": [
                            {
                                "key": "response_time",
                                "value": get_value_by_key(
                                    calculated_measures["measures"], "response_time"
                                ),
                            },
                        ],
                    },
                    {
                        "key": "resource_utilization",
                        "value": float(
                            get_value_by_key(
                                calculated_subcharacteristics["subcharacteristics"],
                                "resource_utilization",
                            )
                        ),
                        "measures": [
                            {
                                "key": "cpu_utilization",
                                "value": get_value_by_key(
                                    calculated_measures["measures"], "cpu_utilization"
                                ),
                            },
                            {
                                "key": "memory_utilization",
                                "value": get_value_by_key(
                                    calculated_measures["measures"],
                                    "memory_utilization",
                                ),
                            },
                        ],
                    },
                ],
            },
        ]
    }

    print(json.dumps(obj, indent=4))


def parse_performance_efficiency_data(path1: Path, path2: Path):
    try:
        release1_df = pd.read_csv(path1)
        release2_df = pd.read_csv(path2)

        release1_endpoints = []
        release2_endpoints = []

        for column_name, _ in release1_df.items():
            if "ENDPOINT" in str(column_name):
                release1_endpoints.append(column_name)

        for column_name, _ in release2_df.items():
            if "ENDPOINT" in str(column_name):
                release2_endpoints.append(column_name)

        endpoint_calls_1 = release1_df[release1_endpoints].values.tolist()
        endpoint_calls_2 = release2_df[release2_endpoints].values.tolist()

        measures = {
            "measures": [
                {
                    "key": "cpu_utilization",
                    "releases": [
                        {
                            "metrics": release1_df["cpu_app"].values.tolist(),
                            "endpoint_calls": endpoint_calls_1,
                        },
                        {
                            "metrics": release2_df["cpu_app"].values.tolist(),
                            "endpoint_calls": endpoint_calls_2,
                        },
                    ],
                },
                {
                    "key": "memory_utilization",
                    "releases": [
                        {
                            "metrics": release1_df["memory_app"].values.tolist(),
                            "endpoint_calls": endpoint_calls_1,
                        },
                        {
                            "metrics": release2_df["memory_app"].values.tolist(),
                            "endpoint_calls": endpoint_calls_2,
                        },
                    ],
                },
                {
                    "key": "response_time",
                    "releases": [
                        {
                            "metrics": release1_df["response_time"].values.tolist(),
                            "endpoint_calls": endpoint_calls_1,
                        },
                        {
                            "metrics": release2_df["response_time"].values.tolist(),
                            "endpoint_calls": endpoint_calls_2,
                        },
                    ],
                },
            ]
        }
        return measures
    except exceptions.MeasureSoftGramCLIException as e:
        print_error(f"[red]Error parsing csv files: {e}\n")
        print_rule()
        exit(1)
