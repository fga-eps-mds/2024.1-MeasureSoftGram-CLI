import os
from genericparser.plugins.domain.generic_class import GenericStaticABC
import requests
from datetime import datetime


class ParserGithub(GenericStaticABC):
    token = None

    def __init__(self, token=None):
        self.token = token

    def _make_request(self, url, token=None):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            print("error making request to github api in url: ", url, e)
        return response.json() if response.status_code == 200 else {}

    def _should_compute_workflow_run(self, run, filters):
        if filters is None:
            return True
        if run["name"] not in filters["workflows"]:
            return False
        if filters["dates"] is not None:
            dates = filters["dates"].split("-")
            run_date = datetime.strptime(run["run_started_at"], "%Y-%m-%dT%H:%M:%SZ")
            start = datetime.strptime(dates[0], "%d/%m/%Y")
            end = datetime.strptime(dates[1], "%d/%m/%Y")
            if run_date < start or run_date > end:
                return False
        return True

    def _get_ci_feedback_times(self, base_url, token=None, filters=None):
        ci_feedback_times = []
        url = f"{base_url}/actions/runs"
        response = self._make_request(url, token)

        if response is not None:
            workflow_runs = response.get("workflow_runs", [])

            for run in workflow_runs:
                if not self._should_compute_workflow_run(run, filters):
                    continue

                started_at = datetime.fromisoformat(
                    run["run_started_at"].replace("Z", "+00:00")
                )
                completed_at = datetime.fromisoformat(
                    run["updated_at"].replace("Z", "+00:00")
                )
                feedback_time = completed_at - started_at
                ci_feedback_times.append(int(feedback_time.total_seconds()))

            result = {
                "metrics": ["sum_ci_feedback_times", "total_builds"],
                "values": [sum(ci_feedback_times), len(ci_feedback_times)],
            }

            return result
        else:
            return False

    def _check_requests(self, base_url, params, values, token=None):
        results = []
        for value in values:
            url_value = value.replace(" ", "%20")
            url = f"{base_url}/{params}{url_value}"
            response = self._make_request(url, token)
            if response and isinstance(response, list):
                for result in response:
                    if result not in results:
                        results.append(result)
        return results

    def _is_valid_time(self, value, dates):
        date_since, date_until = dates

        created_at = datetime.strptime(value["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        closed_at = datetime.strptime(value["closed_at"], "%Y-%m-%dT%H:%M:%SZ") if value["closed_at"] else None
        since = datetime.strptime(date_since, "%d/%m/%Y")
        until = datetime.strptime(date_until, "%d/%m/%Y")

        return ((created_at <= until)
                and (closed_at is None
                or (closed_at is not None and closed_at >= since)))

    def _get_throughput(self, base_url, token=None, filters=None):
        values = []
        issues = []
        label_list = filters["labels"].split(",") if filters and filters["labels"] else []
        dates = filters["dates"].split("-") if filters and filters["dates"] else None
        response = self._check_requests(
            base_url,
            "issues?state=all&labels=",
            label_list,
            token,
        )

        for issue in response:
            if dates is None or self._is_valid_time(issue, dates):
                issues.append(issue)

        total_issues = len(issues)
        resolved_issues = sum(1 for issue in issues if issue["state"] == "closed")

        values.extend(
            [
                total_issues,
                resolved_issues,
                resolved_issues / total_issues if total_issues > 0 else 0,
            ]
        )

        return {
            "metrics": ["total_issues", "resolved_issues", "resolved_ratio"],
            "values": values,
        }

    def extract(self, **kwargs):
        input_file = kwargs.get("input_file")
        filters = kwargs.get("filters")
        token_from_github = (
            input_file.get("token", None)
            if type(input_file) is dict
            else None or os.environ.get("GITHUB_TOKEN", None) or self.token
        )
        repository = (
            input_file.get("repository", None)
            if (type(input_file) is dict)
            else input_file
        )
        metrics = []
        keys = repository
        values = []
        owner, repository_name = repository.split("/")
        url = f"https://api.github.com/repos/{owner}/{repository_name}"

        return_of_get_throughput = self._get_throughput(
            url, token_from_github, filters
        )
        metrics.extend(return_of_get_throughput["metrics"])
        values.extend(return_of_get_throughput["values"])

        return_of_get_ci_feedback_times = self._get_ci_feedback_times(
            url, token_from_github, filters
        )

        if return_of_get_ci_feedback_times:
            metrics.extend(return_of_get_ci_feedback_times["metrics"])
            values.extend(return_of_get_ci_feedback_times["values"])

        return {"metrics": metrics, "values": values, "file_paths": keys}


def main():
    return ParserGithub()
