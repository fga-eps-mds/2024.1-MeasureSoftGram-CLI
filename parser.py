import json
import requests
import sys
import argparse as ap
import argcomplete
from datetime import datetime

TODAY = datetime.now()

METRICS_SONAR = [
    "files",
    "functions",
    "complexity",
    "comment_lines_density",
    "duplicated_lines_density",
    "coverage",
    "ncloc",
    "tests",
    "test_errors",
    "test_failures",
    "test_execution_time",
    "security_rating",
]

BASE_URL = "https://sonarcloud.io/api/measures/component_tree?component=fga-eps-mds_"

def main(**args):
  pass

if __name__ == "__main__":

    parser = ap.ArgumentParser()
    parser.add_argument('measuresoftgram', choices=['import', 'get'])
    parser.add_argument('measuresoftgram get', choices=['metrics', 'measures', 'subcharacteristics', 'characteristics'])
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    main(**vars(args))

    REPO = sys.argv[1]
    RELEASE_VERSION = sys.argv[2]

    response = requests.get(
        f'{BASE_URL}{REPO}&metricKeys={",".join(METRICS_SONAR)}&ps=500'
    )
    j = json.loads(response.text)

    file_path = f'./analytics-raw-data/fga-eps-mds-{REPO}-{TODAY.strftime("%m-%d-%Y-%H-%M-%S")}-{RELEASE_VERSION}.json'

    with open(file_path, "w") as fp:
        fp.write(json.dumps(j))
        fp.close()