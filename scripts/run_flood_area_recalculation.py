"""Recalculate flooded area for every country with regional flood rasters."""

import argparse
import os
import time

from tqdm import tqdm

import process
from misc import get_countries


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only recalculate the listed ISO3 country codes.",
    )
    args = parser.parse_args()

    started = time.time()
    countries = get_countries()
    if args.only:
        requested = set(args.only)
        countries = [country for country in countries if country["iso3"] in requested]

    for country in tqdm(countries):
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
