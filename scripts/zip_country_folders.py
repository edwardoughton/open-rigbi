"""
Create one ZIP archive per country directory.

Example source structure:
    ~open-rigbi/data/processed/
        Afghanistan/
        Albania/
        Algeria/
        ...

Example output:
    ~open-rigbi/data/zenodo_upload/
        Afghanistan.zip
        Albania.zip
        Algeria.zip
        checksums_sha256.txt
        zip_country_folders.log

Run:
    python zip_country_folders.py
"""
from __future__ import annotations

import hashlib
import logging
import os
import configparser
import shutil
import sys
import zipfile
from pathlib import Path

CONFIG = configparser.ConfigParser()
filename = 'script_config.ini'
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', filename))
BASE_PATH = CONFIG['file_locations']['base_path']
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')

# ---------------------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------------------

SOURCE_DIR = Path(DATA_PROCESSED)
OUTPUT_DIR = Path(BASE_PATH, 'zenodo_upload')

# ZIP_DEFLATED compresses files and is generally appropriate for CSV,
# JSON, shapefiles, text files, and uncompressed rasters.
#
# For datasets dominated by formats that are already compressed, such as
# compressed GeoTIFF, NetCDF with internal compression, Parquet, JPEG,
# PNG, ZIP, or GZIP, consider changing this to zipfile.ZIP_STORED.
COMPRESSION_METHOD = zipfile.ZIP_DEFLATED

# ZIP compression level:
#   1 = fastest, with modest compression
#   6 = good general-purpose default
#   9 = slowest, often with only a small additional size reduction
#
# Set to None when using ZIP_STORED.
COMPRESSION_LEVEL = 6

# Set True to test every completed ZIP archive before marking it complete.
# This adds time but is recommended for a large research dataset.
TEST_ARCHIVES = True

# Set True to overwrite an existing final ZIP archive.
# Leave False for a resumable workflow.
OVERWRITE_EXISTING = False


# ---------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = OUTPUT_DIR / "zip_country_folders.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------

def human_readable_size(num_bytes: int) -> str:
    """Convert a byte count into a readable value."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:,.2f} {unit}"
        size /= 1024

    return f"{num_bytes:,} B"


def get_directory_size(directory: Path) -> int:
    """Calculate the total size of files within a directory."""
    total_size = 0

    for path in directory.rglob("*"):
        if path.is_file():
            try:
                total_size += path.stat().st_size
            except OSError as exc:
                logger.warning("Could not read size for %s: %s", path, exc)

    return total_size


def calculate_sha256(file_path: Path, chunk_size: int = 1024 * 1024 * 8) -> str:
    """Calculate SHA-256 checksum without loading the entire file into memory."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file_handle:
        while chunk := file_handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def test_zip_archive(zip_path: Path) -> None:
    """
    Test whether a ZIP archive can be read successfully.

    Raises an exception if a corrupted file is detected.
    """
    with zipfile.ZipFile(zip_path, "r", allowZip64=True) as archive:
        corrupted_file = archive.testzip()

        if corrupted_file is not None:
            raise RuntimeError(
                f"ZIP integrity test failed. First corrupted file: {corrupted_file}"
            )


def zip_country_directory(country_dir: Path, output_zip: Path) -> None:
    """
    Zip a country directory to a temporary file and atomically rename it
    after the archive passes its integrity test.
    """
    partial_zip = output_zip.with_suffix(output_zip.suffix + ".partial")

    if partial_zip.exists():
        logger.warning("Removing incomplete archive: %s", partial_zip)
        partial_zip.unlink()

    source_size = get_directory_size(country_dir)
    logger.info(
        "Starting %s | Source size: %s",
        country_dir.name,
        human_readable_size(source_size),
    )

    zip_kwargs = {
        "file": partial_zip,
        "mode": "w",
        "compression": COMPRESSION_METHOD,
        "allowZip64": True,
    }

    if COMPRESSION_METHOD != zipfile.ZIP_STORED:
        zip_kwargs["compresslevel"] = COMPRESSION_LEVEL

    with zipfile.ZipFile(**zip_kwargs) as archive:
        for source_path in sorted(country_dir.rglob("*")):
            if not source_path.is_file():
                continue

            # Preserve the country folder as the archive's root directory.
            # Example:
            #   Albania/outputs/results.csv
            archive_path = source_path.relative_to(country_dir.parent)

            logger.info("Adding: %s", archive_path)
            archive.write(source_path, arcname=archive_path)

    if TEST_ARCHIVES:
        logger.info("Testing archive: %s", partial_zip.name)
        test_zip_archive(partial_zip)

    # os.replace is atomic when the temporary and final files are on the
    # same filesystem. A completed archive will not be confused with a
    # partially written archive.
    os.replace(partial_zip, output_zip)

    output_size = output_zip.stat().st_size

    if source_size > 0:
        compression_ratio = output_size / source_size
        logger.info(
            "Completed %s | ZIP size: %s | Final size: %.1f%% of original",
            output_zip.name,
            human_readable_size(output_size),
            compression_ratio * 100,
        )
    else:
        logger.info(
            "Completed %s | ZIP size: %s",
            output_zip.name,
            human_readable_size(output_size),
        )


def write_checksum_manifest(zip_files: list[Path]) -> None:
    """Generate a standard SHA-256 checksum manifest."""
    manifest_path = OUTPUT_DIR / "checksums_sha256.txt"
    temporary_manifest = manifest_path.with_suffix(".txt.partial")

    logger.info("Generating SHA-256 checksums")

    with temporary_manifest.open("w", encoding="utf-8", newline="\n") as file_handle:
        for zip_path in sorted(zip_files):
            logger.info("Calculating SHA-256: %s", zip_path.name)
            checksum = calculate_sha256(zip_path)
            file_handle.write(f"{checksum}  {zip_path.name}\n")

    os.replace(temporary_manifest, manifest_path)
    logger.info("Checksum manifest written: %s", manifest_path)


# ---------------------------------------------------------------------
# MAIN WORKFLOW
# ---------------------------------------------------------------------

def main() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Source directory does not exist: {SOURCE_DIR}")

    if not SOURCE_DIR.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {SOURCE_DIR}")

    country_dirs = sorted(
        path for path in SOURCE_DIR.iterdir()
        if path.is_dir()
    )

    if not country_dirs:
        raise RuntimeError(f"No country directories found in: {SOURCE_DIR}")

    logger.info("Found %d country directories", len(country_dirs))
    logger.info("Source directory: %s", SOURCE_DIR)
    logger.info("Output directory: %s", OUTPUT_DIR)

    completed_archives: list[Path] = []
    failed_countries: list[str] = []

    for index, country_dir in enumerate(country_dirs, start=1):
        iso3 = country_dir.name
        results_dir = country_dir / "results_new"
        output_zip = OUTPUT_DIR / f"{iso3}.zip"

        logger.info(
            "Processing %d of %d: %s",
            index,
            len(country_dirs),
            iso3,
        )

        # Skip countries that do not contain a results_new directory.
        if not results_dir.exists() or not results_dir.is_dir():
            logger.warning(
                "Skipping %s: results_new directory not found at %s",
                iso3,
                results_dir,
            )
            continue

        if output_zip.exists() and not OVERWRITE_EXISTING:
            logger.info("Skipping existing archive: %s", output_zip.name)
            completed_archives.append(output_zip)
            continue

        try:
            zip_country_directory(results_dir, output_zip)
            completed_archives.append(output_zip)

        except Exception:
            logger.exception("FAILED: %s", iso3)
            failed_countries.append(iso3)

    if completed_archives:
        write_checksum_manifest(completed_archives)

    logger.info("Batch complete")
    logger.info("Successful or previously completed archives: %d", len(completed_archives))
    logger.info("Failed country directories: %d", len(failed_countries))

    if failed_countries:
        logger.error("Countries requiring another attempt:")
        for country_name in failed_countries:
            logger.error("  - %s", country_name)

        sys.exit(1)


if __name__ == "__main__":
    main()