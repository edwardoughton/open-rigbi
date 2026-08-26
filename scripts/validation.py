"""
Validate flood area statistics.

The workflow uses national Aqueduct rasters so regional fragments cannot be
double counted. Alternate coastal percentile rasters are excluded because
Figure 8 and Figure S1 use the default (95th-percentile) coastal layer.

"""
import argparse
import os
import shutil
import subprocess
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from tqdm import tqdm

import process
from misc import get_countries


ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
DEFAULT_COUNTRY_DATA = (
    PROCESSED / "results_new" / "validation_clean" / "country_data"
)
DEFAULT_OUTPUT = PROCESSED / "results_new" / "validation" / "scenario_stats.csv"
R_SCRIPTS = (
    ROOT / "vis" / "scenario_statistics_totals.r",
    ROOT / "vis" / "scenario_statistics_totals_si.r",
)
MIN_FLOOD_DEPTH_M = 0.000001
OUTPUT_COLUMNS = [
    "iso3",
    "hazard",
    "climate_scenario",
    "model",
    "year",
    "return_period",
    "percentile",
    "flooded_area_km2",
]
KEY_COLUMNS = OUTPUT_COLUMNS[:7]

warnings.filterwarnings(
    "ignore",
    message="Setting the shape on a NumPy array has been deprecated.*",
    category=DeprecationWarning,
)


def get_national_scenarios(country):
    """
    Return the national rasters used by the published validation analysis.
    
    """
    folder = PROCESSED / country["iso3"] / "hazards" / "flooding"
    if not folder.is_dir():
        return []
    return [
        path
        for path in sorted(folder.glob("*.tif"))
        if "_perc_" not in path.name
    ]


def parse_scenario(scenario):
    """
    Parse an Aqueduct filename stem into released scenario fields.
    
    """
    parts = scenario.split("_")
    if scenario.startswith("inunriver_"):
        hazard, climate_scenario, model, year, return_period = parts[:5]
        percentile = "-"
    elif scenario.startswith("inuncoast_"):
        hazard, climate_scenario, model, year, return_period = parts[:5]
        percentile = 0 if len(parts) <= 6 else parts[-1]
    else:
        raise ValueError(f"Unrecognized flood scenario: {scenario}")
    return {
        "hazard": hazard,
        "climate_scenario": climate_scenario,
        "model": model,
        "year": year,
        "return_period": return_period,
        "percentile": percentile,
    }


def calculate_scenario(country, scenario_path, output_dir, overwrite=False):
    """
    Calculate flooded area for one country/scenario national raster.
    
    """
    scenario_path = Path(scenario_path)
    scenario = scenario_path.stem
    output_folder = output_dir / country["iso3"] / "regional" / scenario
    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / f"{country['iso3']}_{scenario}.csv"
    if output_path.exists() and not overwrite:
        return

    partial = output_path.with_suffix(".csv.partial")
    partial.unlink(missing_ok=True)
    flooded_area_km2 = 0.0
    has_flooded_cells = False
    with rasterio.open(scenario_path) as raster:
        for _, window in raster.block_windows(1):
            data = raster.read(1, window=window)
            flooded_mask = (
                np.isfinite(data)
                & (data >= MIN_FLOOD_DEPTH_M)
                & (data < 150)
            )
            if not flooded_mask.any():
                continue
            has_flooded_cells = True
            flooded_area_km2 += process.calculate_flooded_area_km2(
                flooded_mask, raster.window_transform(window), raster.crs
            )

    row = parse_scenario(scenario)
    row["flooded_area_km2"] = flooded_area_km2 if has_flooded_cells else "-"
    try:
        pd.DataFrame([row]).to_csv(partial, index=False)
        os.replace(partial, output_path)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def calculate_country(country, workers, output_dir, overwrite=False):
    """
    Calculate every plotted flood scenario for one country.
    
    """
    scenarios = get_national_scenarios(country)
    if not scenarios:
        return 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                calculate_scenario, country, scenario, output_dir, overwrite
            )
            for scenario in scenarios
        ]
        for future in as_completed(futures):
            future.result()
    return len(scenarios)


def calculate(countries, output_dir, workers=4, overwrite=False):
    """
    Calculate clean national scenario files for selected countries.
    
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    for country in tqdm(countries):
        count = calculate_country(country, workers, output_dir, overwrite)
        if count:
            print(f"--Processed {country['country']} from {count} national rasters")
        else:
            print(f"--Skipping {country['country']}: no national flood rasters")
    print(f"Flood area recalculation completed in {time.time() - started:.2f} seconds")
 

def collect(country_data_dir):
    """
    Read scenario files and fail on malformed or duplicate results.
    
    """
    files = sorted(country_data_dir.glob("*/regional/*/*.csv"))
    if not files:
        raise FileNotFoundError(f"No scenario CSVs found below {country_data_dir}")

    frames = []
    for path in files:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        if len(frame) != 1:
            raise ValueError(f"Expected one row in {path}, found {len(frame)}")
        missing = set(OUTPUT_COLUMNS[1:]) - set(frame.columns)
        if missing:
            raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
        frame.insert(0, "iso3", path.parents[2].name)
        frames.append(frame[OUTPUT_COLUMNS])

    combined = pd.concat(frames, ignore_index=True)
    duplicates = combined.duplicated(KEY_COLUMNS, keep=False)
    if duplicates.any():
        sample = combined.loc[duplicates, KEY_COLUMNS].head().to_dict("records")
        raise ValueError(f"Duplicate scenario keys found; examples: {sample}")
    return combined.sort_values(KEY_COLUMNS).reset_index(drop=True)


def validate_coverage(data, countries):
    """
    Require every included country to have all available national scenarios.
    
    """
    actual_counts = data.groupby("iso3").size().to_dict()
    expected_countries = set()
    problems = []
    for country in countries:
        scenarios = get_national_scenarios(country)
        if not scenarios:
            continue
        iso3 = country["iso3"]
        expected_countries.add(iso3)
        actual = actual_counts.get(iso3, 0)
        if actual != len(scenarios):
            problems.append(f"{iso3}: expected {len(scenarios)}, found {actual}")

    unexpected = sorted(set(actual_counts) - expected_countries)
    if unexpected:
        problems.append(f"unexpected countries: {', '.join(unexpected)}")
    if problems:
        raise RuntimeError("Incomplete scenario coverage: " + "; ".join(problems))


def write_atomic(data, output):
    """
    Atomically promote a validated consolidated dataset.
    
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    partial.unlink(missing_ok=True)
    try:
        data.to_csv(partial, index=False)
        os.replace(partial, output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def find_rscript(explicit=None):
    """
    Locate Rscript from an explicit path or the active environment.
    
    """
    if explicit:
        executable = Path(explicit)
        if not executable.is_file():
            raise FileNotFoundError(f"Rscript not found: {executable}")
        return str(executable)
    executable = shutil.which("Rscript")
    if executable:
        return executable
    windows_default = Path(r"C:\Program Files\R\R-4.4.2\bin\Rscript.exe")
    if windows_default.is_file():
        return str(windows_default)
    raise FileNotFoundError("Rscript is not on PATH; pass --rscript")


def generate_figures(validation_dir, rscript=None):
    """
    Regenerate Figure 8 and Figure S1 from the promoted CSV.
    
    """
    environment = os.environ.copy()
    environment["OPEN_RIGBI_VALIDATION_DIR"] = str(validation_dir)
    executable = find_rscript(rscript)
    for script in R_SCRIPTS:
        subprocess.run([executable, script], cwd=ROOT, env=environment, check=True)


def promote(country_data_dir, output, countries, figures=True, rscript=None):
    """
    Validate and plot clean results.
    
    """
    data = collect(country_data_dir)
    validate_coverage(data, countries)
    write_atomic(data, output)
    missing_area = int((data["flooded_area_km2"] == "-").sum())
    print(f"Promoted {len(data):,} rows for {data['iso3'].nunique()} countries")
    print(f"Rows without flooded cells: {missing_area:,}")
    print(f"Wrote {output}")
    if figures:
        generate_figures(output.parent, rscript)
        print("Regenerated Figure 8 and Figure S1")


def add_common_paths(parser):
    parser.add_argument(
        "--country-data-dir", type=Path, default=DEFAULT_COUNTRY_DATA
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    calculate_parser = commands.add_parser("calculate")
    calculate_parser.add_argument("--only", nargs="+", metavar="ISO3")
    calculate_parser.add_argument("--workers", type=int, default=4)
    calculate_parser.add_argument("--overwrite", action="store_true")
    calculate_parser.add_argument(
        "--country-data-dir", type=Path, default=DEFAULT_COUNTRY_DATA
    )

    collect_parser = commands.add_parser("collect")
    add_common_paths(collect_parser)

    finalize_parser = commands.add_parser("finalize")
    add_common_paths(finalize_parser)
    finalize_parser.add_argument("--skip-figures", action="store_true")
    finalize_parser.add_argument("--rscript")

    all_parser = commands.add_parser("all")
    add_common_paths(all_parser)
    all_parser.add_argument("--only", nargs="+", metavar="ISO3")
    all_parser.add_argument("--workers", type=int, default=4)
    all_parser.add_argument("--overwrite", action="store_true")
    all_parser.add_argument("--skip-figures", action="store_true")
    all_parser.add_argument("--rscript")
    return parser.parse_args()


def selected_countries(only=None):
    countries = get_countries()
    if not only:
        return countries
    requested = set(only)
    selected = [country for country in countries if country["iso3"] in requested]
    missing = sorted(requested - {country["iso3"] for country in selected})
    if missing:
        raise ValueError(f"Unknown or excluded ISO3 codes: {', '.join(missing)}")
    return selected


def main():
    args = parse_args()
    country_data_dir = args.country_data_dir.resolve()
    selected = selected_countries(getattr(args, "only", None))

    if args.command in {"calculate", "all"}:
        calculate(
            selected,
            country_data_dir,
            workers=args.workers,
            overwrite=args.overwrite,
        )
    if args.command in {"collect", "finalize", "all"}:
        promote(
            country_data_dir,
            args.output.resolve(),
            get_countries(),
            figures=args.command != "collect" and not args.skip_figures,
            rscript=getattr(args, "rscript", None),
        )


if __name__ == "__main__":
    main()
