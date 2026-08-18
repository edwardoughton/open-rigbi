"""Collect recalculated flood areas and regenerate the Figure 8 output."""

import argparse
import ctypes
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import validation
from misc import get_countries
from run_flood_area_recalculation import get_country_scenarios


ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RUN_LOGS = (
    PROCESSED / "flood_area_recalculation.stdout.log",
    PROCESSED / "flood_area_recalculation_restored.stdout.log",
)
R_SCRIPT = ROOT / "vis" / "scenario_statistics_totals.r"
R_EXECUTABLE = Path(r"C:\Program Files\R\R-4.4.2\bin\Rscript.exe")


def require_successful_runs():
    for log_path in RUN_LOGS:
        contents = log_path.read_text(encoding="utf-8", errors="replace")
        if "Flood-area recalculation completed" not in contents:
            raise RuntimeError(f"Calculation did not complete successfully: {log_path}")


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
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.wait_pids:
        wait_for_processes(args.wait_pids)

    require_successful_runs()
    countries = get_countries()

    country_scenarios = [
        (country, get_country_scenarios(country)) for country in countries
    ]
    country_scenarios = [item for item in country_scenarios if item[1]]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(validation.collect, [country], scenarios): country["iso3"]
            for country, scenarios in country_scenarios
        }
        for future in as_completed(futures):
            iso3 = futures[future]
            future.result()
            print(f"Collected {iso3}")

    validation.collect_all(countries)

    collected = PROCESSED / "results" / "validation" / "scenario_stats.csv"
    figure_input = (
        PROCESSED / "results_new" / "validation" / "scenario_stats.csv"
    )
    figure_input.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(collected, figure_input)

    subprocess.run([R_EXECUTABLE, R_SCRIPT], cwd=ROOT, check=True)
    print("Validation collection and Figure 8 regeneration completed")
