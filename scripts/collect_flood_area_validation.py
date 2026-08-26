"""Collect an isolated national flood-area recalculation into one validated CSV."""

import argparse
import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_COUNTRY_DATA = (
    ROOT / "data" / "processed" / "results_new" / "validation_clean" / "country_data"
)
DEFAULT_OUTPUT = DEFAULT_COUNTRY_DATA.parent / "scenario_stats.csv"
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


def collect(country_data_dir):
    """Read one-row scenario files and fail on malformed or duplicate results."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--country-data-dir", type=Path, default=DEFAULT_COUNTRY_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--expected-rows",
        type=int,
        help="Fail unless the collected result has this many scenario rows.",
    )
    args = parser.parse_args()

    country_data_dir = args.country_data_dir.resolve()
    output = args.output.resolve()
    combined = collect(country_data_dir)
    if args.expected_rows is not None and len(combined) != args.expected_rows:
        raise ValueError(
            f"Expected {args.expected_rows} rows, collected {len(combined)}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    partial.unlink(missing_ok=True)
    try:
        combined.to_csv(partial, index=False)
        os.replace(partial, output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    missing_area = (combined["flooded_area_km2"] == "-").sum()
    print(f"Collected {len(combined):,} rows for {combined['iso3'].nunique()} countries")
    print(f"Rows without flooded cells: {missing_area:,}")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
