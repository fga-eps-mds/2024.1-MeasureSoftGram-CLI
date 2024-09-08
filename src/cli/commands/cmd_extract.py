from datetime import datetime
import json
import logging
import os
import re
import sys
from time import perf_counter

from rich import print
from rich.console import Console
from genericparser import GenericParser

from src.cli.jsonReader import folder_reader
from src.cli.utils import (
    make_progress_bar,
    print_info,
    print_panel,
    print_rule,
    print_warn,
    is_valid_date_range,
)

logger = logging.getLogger("msgram")


def get_infos_from_name(filename: str) -> str:
    """
    filename: str = fga-eps-mds-2022-1-MeasureSoftGram-Service-09-11-2022-16-11-42-develop.json
    """
    file_date = re.search(r"\d{1,2}-\d{1,2}-\d{4}-\d{1,2}-\d{1,2}", filename)

    if not file_date:
        message = (
            "Could not extract creation date from file. Was the file name "
            "to contain a date in the format dd-mm-yyyy-hh-mm"
        )
        print_warn(message)
        print_warn(f"filename: {filename}")
        sys.exit(1)

    file_name = filename.split(".")[0]

    return f"{file_name}-extracted.msgram"


def check_error_accompany_github(param, value, output_origin):
    if value is not None and output_origin == "sonarqube":
        logger.error(
            f'Error: The parameter "-{param}" must accompany a github repository output'
        )
        print_warn(
            f'Error: The parameter "-{param}" must accompany a github repository output'
        )
        sys.exit(1)


def command_extract(args):
    time_init = perf_counter()
    try:
        output_origin = args["output_origin"]
        extracted_path = args["extracted_path"]
        sonar_path = args.get("sonar_path", None)
        gh_repository = args.get("gh_repository", None)
        gh_label = args.get("gh_label", None)
        gh_workflows = args.get("gh_workflows", None)
        gh_date_range = args.get("gh_date_range", None)

    except Exception as e:
        logger.error(f"KeyError: args[{e}] - non-existent parameters")
        print_warn(f"KeyError: args[{e}] - non-existent parameters")
        exit(1)

    check_error_accompany_github("lb", gh_label, output_origin)
    check_error_accompany_github("wf", gh_workflows, output_origin)
    check_error_accompany_github("fd", gh_date_range, output_origin)

    if gh_date_range is not None and not is_valid_date_range(gh_date_range):
        logger.error(
            "Error: Range of dates for filter must be in format 'dd/mm/yyyy-dd/mm/yyyy'"
        )
        print_warn(
            "Error: Range of dates for filter must be in format 'dd/mm/yyyy-dd/mm/yyyy'"
        )
        sys.exit(1)

    if sonar_path is None and gh_repository is None:
        logger.error(
            "It is necessary to pass the data_path or repository_path parameters"
        )
        print_warn(
            "It is necessary to pass the data_path or repository_path parameters"
        )
        sys.exit(1)

    console = Console()
    console.clear()
    print_rule("Extract metrics")
    parser = GenericParser()

    if gh_repository and output_origin == "github":
        filters = {
            "labels": gh_label if gh_label else "US,User Story,User Stories",
            "workflows": gh_workflows.split(",") if gh_workflows else "build",
            "dates": gh_date_range if gh_date_range else None,
        }
        result = parser.parse(
            input_value=gh_repository, type_input=output_origin, filters=filters
        )
        repository_name = gh_repository.replace("/", "-")
        save_file_with_results(
            ".msgram",
            gh_repository,
            name=f"github_{repository_name}-{datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}-extracted.msgram",
            result=result,
        )
        return

    if not os.path.isdir(extracted_path):
        logger.error(
            f'FileNotFoundError: extract directory "{extracted_path}" does not exists'
        )
        print_warn(
            f"FileNotFoundError: extract directory[blue]'{extracted_path}'[/]does not exists"
        )
        sys.exit(1)

    logger.debug(f"output_origin: {output_origin}")
    logger.debug(f"data_path: {sonar_path}")
    logger.debug(f"extracted_path: {extracted_path}")

    files = list(sonar_path.glob("*.json"))

    if not files:
        print_warn(f"No JSON files found in the specified data_path: {sonar_path}\n")
        sys.exit(1)

    valid_files = len(files)

    print_info(f"\n> Extract and save metrics [[blue ]{output_origin}[/]]:")
    with make_progress_bar() as progress_bar:
        task_request = progress_bar.add_task(
            "[#A9A9A9]Extracting files: ", total=len(files)
        )
        progress_bar.advance(task_request)

        for component, filename, files_error in folder_reader(sonar_path, "json"):
            if files_error:
                progress_bar.update(task_request, advance=files_error)
                valid_files = valid_files - files_error

            name = get_infos_from_name(filename)
            result = parser.parse(input_value=component, type_input=output_origin)

            save_file_with_results(extracted_path, filename, name, result)

            progress_bar.advance(task_request)

        time_extract = perf_counter() - time_init
        print_info(
            f"\n\nMetrics successfully extracted [[blue bold]{valid_files}/{len(files)} "
            f"files - {time_extract:0.2f} seconds[/]]!"
        )
    print_panel(
        "> Run [#008080]msgram calculate all -ep 'extracted_path' -cp 'extracted_path' -o 'output_origin'"
    )


def save_file_with_results(extracted_path, filename, name, result):
    print(f"[dark_green]Reading:[/] [black]{filename}[/]")
    print(f"[dark_green]Save   :[/] [black]{name}[/]\n")

    with open(f"{extracted_path}/{name}", "w") as f:
        f.write(json.dumps(result, indent=4))
