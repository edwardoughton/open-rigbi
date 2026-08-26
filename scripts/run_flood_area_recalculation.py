"""Recalculate flooded area for every country with regional flood rasters."""

import argparse
import os
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
DEFAULT_OUTPUT_DIR = (
    ROOT / "data" / "processed" / "results_new" / "validation" / "country_data"
)
MIN_FLOOD_DEPTH_M = 0.000001

# Rasterio currently triggers this NumPy deprecation warning once per block.
warnings.filterwarnings(
    "ignore",
    message="Setting the shape on a NumPy array has been deprecated.*",
    category=DeprecationWarning,
)


def get_country_scenarios(country):
    """Return scenario identifiers found in a country's regional rasters."""
    folder = os.path.join(
        process.DATA_PROCESSED,
        country["iso3"],
        "hazards",
        "flooding",
        "regional",
    )
    if not os.path.isdir(folder):
        return []

    scenarios = set()
    for filename in os.listdir(folder):
        if not filename.endswith(".tif"):
            continue
        marker = filename.find("_inun")
        if marker == -1:
            continue
        scenarios.add(filename[marker + 1 : -4])

    return sorted(scenarios)


def get_national_scenarios(country):
    """Return the national rasters used by the published validation analysis."""
    folder = Path(process.DATA_PROCESSED) / country["iso3"] / "hazards" / "flooding"
    if not folder.is_dir():
        return []
    # validation.collect() historically excludes the alternate coastal
    # percentile rasters (filenames containing ``_perc_``). Figure 8 and
    # Figure S1 use the default coastal percentile only.
    return [
        str(path)
        for path in sorted(folder.glob("*.tif"))
        if "_perc_" not in path.name
    ]


def process_national_scenario(country, scenario_path, output_dir, overwrite=False):
    """Calculate one country's flood statistics directly from a national raster."""
    scenario_path = Path(scenario_path)
    scenario = scenario_path.stem
    output_folder = output_dir / country["iso3"] / "regional" / scenario
    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / f"{country['iso3']}_{scenario}.csv"
    if output_path.exists() and not overwrite:
        return

    partial_output = output_path.with_suffix(".csv.partial")
    partial_output.unlink(missing_ok=True)

    parts = scenario.split("_")
    if scenario.startswith("inunriver_"):
        hazard, climate_scenario, model, year, return_period = parts[:5]
        percentile = "-"
    elif scenario.startswith("inuncoast_"):
        hazard, climate_scenario, model, year, return_period = parts[:5]
        percentile = 0 if len(parts) <= 6 else parts[-1]
    else:
        raise ValueError(f"Unrecognized flood scenario: {scenario}")

    with rasterio.open(scenario_path) as raster:
        has_flooded_cells = False
        flooded_area_km2 = 0.0
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

    metrics = pd.DataFrame([{
        "hazard": hazard,
        "climate_scenario": climate_scenario,
        "model": model,
        "year": year,
        "return_period": return_period,
        "percentile": percentile,
        "flooded_area_km2": flooded_area_km2 if has_flooded_cells else "-",
    }])
    try:
        metrics.to_csv(partial_output, index=False)
        os.replace(partial_output, output_path)
    except BaseException:
        partial_output.unlink(missing_ok=True)
        raise


def run_national_processing(country, workers, output_dir, overwrite=False):
    """Process all available national flood rasters for one country."""
    scenarios = get_national_scenarios(country)
    if not scenarios:
        return 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                process_national_scenario,
                country,
                scenario,
                output_dir,
                overwrite,
            )
            for scenario in scenarios
        ]
        for future in as_completed(futures):
            future.result()
    return len(scenarios)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only recalculate the listed ISO3 country codes.",
    )
    parser.add_argument(
        "--national",
        action="store_true",
        help="Calculate from national rasters instead of regional fragments.",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Country-data output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recalculate and atomically replace existing scenario CSVs.",
    )
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Validation output directory: {output_dir}")

    started = time.time()
    countries = get_countries()
    if args.only:
        requested = set(args.only)
        countries = [country for country in countries if country["iso3"] in requested]

    for country in tqdm(countries):
        # if not country['iso3'] == "GBR":
        #     continue
        if args.national:
            scenario_count = run_national_processing(
                country,
                args.workers,
                output_dir,
                overwrite=args.overwrite,
            )
            if scenario_count:
                print(
                    f"--Processed {country['country']} from "
                    f"{scenario_count} national rasters"
                )
            else:
                print(f"--Skipping {country['country']}: no national flood rasters")
            continue

        scenarios = get_country_scenarios(country)
        if not scenarios:
            print(f"--Skipping {country['country']}: no regional flood rasters")
            continue

        print(
            f"--Working on {country['country']} "
            f"({len(scenarios)} scenarios)"
        )
        process.get_scenarios = lambda scenarios=scenarios: scenarios
        process.run_site_processing(country)

    elapsed = time.time() - started
    print(f"Flood-area recalculation completed in {elapsed:.2f} seconds")
