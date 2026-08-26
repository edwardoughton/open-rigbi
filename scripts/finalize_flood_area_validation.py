"""Collect recalculated flood areas and regenerate the Figure 8 output."""

import argparse
import ctypes
import os
import subprocess
from pathlib import Path

import pandas as pd

from collect_flood_area_validation import collect
from misc import get_countries
from run_flood_area_recalculation import (
    get_national_scenarios,
)


ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
DEFAULT_CLEAN_DIR = (
    PROCESSED / "results_new" / "validation_clean" / "country_data"
)
DEFAULT_OUTPUT = (
    PROCESSED / "results_new" / "validation" / "scenario_stats.csv"
)
R_SCRIPTS = (
    ROOT / "vis" / "scenario_statistics_totals.r",
    ROOT / "vis" / "scenario_statistics_totals_si.r",
)
R_EXECUTABLE = Path(r"C:\Program Files\R\R-4.4.2\bin\Rscript.exe")


def get_available_scenarios(country):
    """Return only the national rasters used by the clean calculation."""
    return get_national_scenarios(country)


def validate_country_coverage(collected, country_scenarios):
    """Require every country with flood inputs to have every plotted scenario."""
    data = pd.read_csv(collected)
    duplicated = data.duplicated(
        [
            "iso3",
            "hazard",
            "climate_scenario",
            "model",
            "year",
            "return_period",
            "percentile",
        ]
    )
    if duplicated.any():
        raise RuntimeError(f"Found {int(duplicated.sum())} duplicate scenario rows")

    actual_counts = data.groupby("iso3").size().to_dict()
    problems = []
    for country, scenarios in country_scenarios:
        expected = sum("_perc_" not in str(scenario) for scenario in scenarios)
        actual = actual_counts.get(country["iso3"], 0)
        if actual != expected:
            problems.append(f"{country['iso3']}: expected {expected}, found {actual}")
    if problems:
        raise RuntimeError(
            "Incomplete country/scenario coverage: " + "; ".join(problems)
        )


def require_successful_run(country_data_dir):
    log_path = country_data_dir.parent / "recalculation.stdout.log"
    contents = log_path.read_text(encoding="utf-8", errors="replace")
    if "Flood-area recalculation completed" not in contents:
        raise RuntimeError(f"Calculation did not complete successfully: {log_path}")


def write_atomic(data, output):
    """Atomically promote the validated clean dataset."""
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    partial.unlink(missing_ok=True)
    try:
        data.to_csv(partial, index=False)
        os.replace(partial, output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def wait_for_processes(process_ids):
    """Wait for Windows process IDs and require successful exit codes."""
    synchronize = 0x00100000
    infinite = 0xFFFFFFFF
    kernel32 = ctypes.windll.kernel32

    for process_id in process_ids:
        handle = kernel32.OpenProcess(synchronize, False, process_id)
        if not handle:
            raise RuntimeError(f"Could not open calculation process {process_id}")
        try:
            kernel32.WaitForSingleObject(handle, infinite)
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                raise RuntimeError(f"Could not read exit code for process {process_id}")
            if exit_code.value != 0:
                raise RuntimeError(
                    f"Calculation process {process_id} exited with {exit_code.value}"
                )
        finally:
            kernel32.CloseHandle(handle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-pids", nargs="+", type=int, default=[])
    parser.add_argument(
        "--country-data-dir", type=Path, default=DEFAULT_CLEAN_DIR
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.wait_pids:
        wait_for_processes(args.wait_pids)

    country_data_dir = args.country_data_dir.resolve()
    output = args.output.resolve()
    require_successful_run(country_data_dir)
    countries = get_countries()

    country_scenarios = [
        (country, get_available_scenarios(country)) for country in countries
    ]
    country_scenarios = [item for item in country_scenarios if item[1]]
    combined = collect(country_data_dir)
    write_atomic(combined, output)
    validate_country_coverage(output, country_scenarios)

    environment = os.environ.copy()
    environment["OPEN_RIGBI_VALIDATION_DIR"] = str(output.parent)
    for r_script in R_SCRIPTS:
        subprocess.run(
            [R_EXECUTABLE, r_script], cwd=ROOT, env=environment, check=True
        )
    print("Clean validation promotion and figure regeneration completed")
