from io import StringIO
from pathlib import Path
import shutil
import sys
import tempfile

import pytest
from src.cli.commands.cmd_norm_diff import command_norm_diff


def test_norm_diff():
    config_dirpath = tempfile.mkdtemp()

    captured_output = StringIO()
    sys.stdout = captured_output

    shutil.copy("tests/unit/data/planned.json", f"{config_dirpath}/planned.json")
    shutil.copy("tests/unit/data/calculated.json", f"{config_dirpath}/calculated.json")

    command_norm_diff(
        {
            "planned_path": Path(config_dirpath) / "planned.json",
            "calculated_path": Path(config_dirpath) / "calculated.json",
        }
    )

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()

    assert "Norm diff calculation performed successfully!" in output
    assert "For more detailed informations use 'diff' command." in output

    norm_diff_value = float(output.split("Norm Diff:")[1].split("\n")[0].strip())
    assert norm_diff_value == 0.24323122001478284


def test_missing_args():
    config_dirpath = tempfile.mkdtemp()

    captured_output = StringIO()
    sys.stdout = captured_output

    shutil.copy("tests/unit/data/planned.json", f"{config_dirpath}/planned.json")
    shutil.copy("tests/unit/data/calculated.json", f"{config_dirpath}/calculated.json")

    with pytest.raises(SystemExit) as excinfo:
        command_norm_diff({"planned_path": Path(config_dirpath) / "planned.json"})

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()

    assert excinfo.value.code == 1
    assert "non-existent parameters" in output


def test_invalid_calculated_file():
    config_dirpath = tempfile.mkdtemp()

    captured_output = StringIO()
    sys.stdout = captured_output

    shutil.copy("tests/unit/data/planned.json", f"{config_dirpath}/planned.json")
    shutil.copy("tests/unit/data/calculated.json", f"{config_dirpath}/calculated.json")

    with pytest.raises(SystemExit) as excinfo:
        command_norm_diff(
            {
                "planned_path": Path(config_dirpath) / "planned.json",
                "calculated_path": Path(config_dirpath) / "invalid.json",
            }
        )

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()

    assert excinfo.value.code == 1
    assert "Error reading calculate" in output


def test_invalid_planned_file():
    config_dirpath = tempfile.mkdtemp()

    captured_output = StringIO()
    sys.stdout = captured_output

    shutil.copy("tests/unit/data/planned.json", f"{config_dirpath}/planned.json")
    shutil.copy("tests/unit/data/calculated.json", f"{config_dirpath}/calculated.json")

    with pytest.raises(SystemExit) as excinfo:
        command_norm_diff(
            {
                "planned_path": Path(config_dirpath) / "invalid.json",
                "calculated_path": Path(config_dirpath) / "calculated.json",
            }
        )

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()

    assert excinfo.value.code == 1
    assert "Error reading planned" in output


def test_missmatch_values():
    config_dirpath = tempfile.mkdtemp()

    captured_output = StringIO()
    sys.stdout = captured_output

    shutil.copy(
        "tests/unit/data/missmatch-planned.json",
        f"{config_dirpath}/missmatch-planned.json",
    )
    shutil.copy("tests/unit/data/calculated.json", f"{config_dirpath}/calculated.json")

    with pytest.raises(SystemExit) as excinfo:
        command_norm_diff(
            {
                "planned_path": Path(config_dirpath) / "missmatch-planned.json",
                "calculated_path": Path(config_dirpath) / "calculated.json",
            }
        )

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()

    assert excinfo.value.code == 1
    assert "Error extracting values" in output