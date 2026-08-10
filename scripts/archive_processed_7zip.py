"""
Archive data/processed with 7-Zip, one top-level folder per archive.

This is intended for very large processed datasets where resumability matters.
Each immediate child folder of data/processed is written to its own .7z file,
tested, then renamed from a temporary .partial.7z path to the final archive.

Examples:
    python scripts/archive_processed_7zip.py --dry-run
    python scripts/archive_processed_7zip.py
    python scripts/archive_processed_7zip.py --level 1 --no-test
    python scripts/archive_processed_7zip.py --volume-size 100g
    python scripts/archive_processed_7zip.py --only USA CAN MEX
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:  # optional convenience dependency
    tqdm = None


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "script_config.ini"


def load_default_source() -> Path:
    """Load data/processed from the repository's script configuration."""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    base_path = Path(config["file_locations"]["base_path"])
    if not base_path.is_absolute():
        base_path = SCRIPT_DIR.parent / base_path

    return base_path / "processed"


def find_7zip(explicit_path: str | None = None) -> str:
    """Return a usable 7-Zip executable path."""
    candidates: list[str | Path] = []

    if explicit_path:
        candidates.append(explicit_path)

    candidates.extend(["7z", "7za", "7zr"])

    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles")
        program_files_x86 = os.environ.get("ProgramFiles(x86)")

        if program_files:
            candidates.append(Path(program_files) / "7-Zip" / "7z.exe")
        if program_files_x86:
            candidates.append(Path(program_files_x86) / "7-Zip" / "7z.exe")

    for candidate in candidates:
        candidate_text = str(candidate)
        resolved = shutil.which(candidate_text)

        if resolved:
            return resolved

        candidate_path = Path(candidate_text)
        if candidate_path.exists():
            return str(candidate_path)

    raise FileNotFoundError(
        "Could not find 7-Zip. Install 7-Zip and make sure 7z is on PATH, "
        "or pass --seven-zip C:\\Path\\To\\7z.exe."
    )


def human_readable_size(num_bytes: int) -> str:
    """Convert a byte count into a readable value."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:,.2f} {unit}"
        size /= 1024

    return f"{num_bytes:,} B"


def calculate_sha256(file_path: Path, chunk_size: int = 1024 * 1024 * 16) -> str:
    """Calculate SHA-256 checksum without loading the archive into memory."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file_handle:
        while chunk := file_handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def archive_has_volume_parts(archive_path: Path) -> bool:
    """Return whether a split 7z archive has one or more .001 volume files."""
    return archive_path.with_suffix(archive_path.suffix + ".001").exists()


def final_archive_paths(archive_path: Path) -> list[Path]:
    """Return the final archive path or all final split-volume paths."""
    first_volume = archive_path.with_suffix(archive_path.suffix + ".001")

    if not first_volume.exists():
        return [archive_path]

    return sorted(archive_path.parent.glob(f"{archive_path.name}.[0-9][0-9][0-9]*"))


def remove_partial_outputs(partial_archive: Path) -> None:
    """Remove leftover partial archive files from an interrupted run."""
    partial_paths = [partial_archive]
    partial_paths.extend(sorted(partial_archive.parent.glob(f"{partial_archive.name}.[0-9][0-9][0-9]*")))

    for path in partial_paths:
        if path.exists():
            logging.warning("Removing incomplete archive piece: %s", path)
            path.unlink()


def promote_partial_outputs(partial_archive: Path, final_archive: Path) -> None:
    """Rename completed partial archives to their final archive names."""
    partial_volumes = sorted(partial_archive.parent.glob(f"{partial_archive.name}.[0-9][0-9][0-9]*"))

    if partial_volumes:
        for partial_volume in partial_volumes:
            final_volume_name = partial_volume.name.replace(partial_archive.name, final_archive.name, 1)
            os.replace(partial_volume, final_archive.parent / final_volume_name)
        return

    os.replace(partial_archive, final_archive)


def is_7zip_file_event(line: str) -> bool:
    """Return whether a 7-Zip log line represents one archived file."""
    stripped = line.strip()
    return (
        stripped.startswith("Compressing  ")
        or stripped.startswith("Compressing ")
        or stripped.startswith("+ ")
    )


def is_7zip_progress_noise(line: str) -> bool:
    """Return whether a 7-Zip line is noisy progress text handled by tqdm."""
    stripped = line.strip()
    if not stripped:
        return True
    if is_7zip_file_event(stripped):
        return True
    return "%" in stripped and any(character.isdigit() for character in stripped)


def run_7zip(
    command: list[str],
    dry_run: bool,
    cwd: Path | None = None,
    file_progress=None,
) -> None:
    """Run 7-Zip, updating tqdm from file events without printing filenames."""
    logging.info("Command: %s", subprocess.list2cmdline(command))

    if dry_run:
        return

    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    output_tail: list[str] = []

    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.strip()

        if is_7zip_file_event(line):
            if file_progress is not None:
                file_progress.update(1)
            continue

        if is_7zip_progress_noise(line):
            continue

        output_tail.append(line)
        output_tail = output_tail[-20:]
        logging.info(line)

    return_code = process.wait()

    if return_code != 0:
        details = "\n".join(output_tail)
        raise RuntimeError(f"7-Zip failed with exit code {return_code}\n{details}")


def count_files(directory: Path) -> int:
    """Count files under a directory for tqdm progress reporting."""
    file_count = 0
    for path in directory.rglob("*"):
        if path.is_file():
            file_count += 1
    return file_count


def archive_directory(
    seven_zip: str,
    source_dir: Path,
    output_dir: Path,
    *,
    level: int,
    threads: str,
    solid: str,
    volume_size: str | None,
    test_archive: bool,
    dry_run: bool,
    overwrite: bool,
    file_progress=None,
) -> list[Path]:
    """Archive one source directory and return the final output path or parts."""
    final_archive = output_dir / f"{source_dir.name}.7z"
    partial_archive = output_dir / f"{source_dir.name}.partial.7z"

    if final_archive.exists() or archive_has_volume_parts(final_archive):
        if not overwrite:
            logging.info("Skipping existing archive: %s", final_archive.name)
            return final_archive_paths(final_archive)

        if not dry_run:
            for path in final_archive_paths(final_archive):
                logging.warning("Removing existing archive: %s", path)
                path.unlink()

    if not dry_run:
        remove_partial_outputs(partial_archive)

    add_command = [
        seven_zip,
        "a",
        "-t7z",
        str(partial_archive),
        source_dir.name,
        f"-mx={level}",
        "-m0=lzma2",
        f"-mmt={threads}",
        f"-ms={solid}",
        "-bb1",
    ]

    if volume_size:
        add_command.append(f"-v{volume_size}")

    logging.info("Archiving: %s", source_dir)
    run_7zip(add_command, dry_run=dry_run, cwd=source_dir.parent, file_progress=file_progress)

    if test_archive:
        test_target = partial_archive
        if volume_size:
            test_target = partial_archive.with_suffix(partial_archive.suffix + ".001")

        test_command = [seven_zip, "t", str(test_target)]
        logging.info("Testing archive: %s", test_target)
        run_7zip(test_command, dry_run=dry_run)

    if not dry_run:
        promote_partial_outputs(partial_archive, final_archive)

    final_paths = final_archive_paths(final_archive)
    final_size = sum(path.stat().st_size for path in final_paths if path.exists())

    if final_size:
        logging.info(
            "Completed %s | Archive size: %s",
            final_archive.name,
            human_readable_size(final_size),
        )
    else:
        logging.info("Completed %s", final_archive.name)

    return final_paths


def write_checksum_manifest(output_dir: Path, archive_paths: list[Path], dry_run: bool) -> None:
    """Write checksums for all completed archive files."""
    manifest_path = output_dir / "checksums_sha256.txt"
    partial_manifest = output_dir / "checksums_sha256.txt.partial"

    logging.info("Writing SHA-256 manifest: %s", manifest_path)

    if dry_run:
        return

    with partial_manifest.open("w", encoding="utf-8", newline="\n") as file_handle:
        for archive_path in sorted(set(archive_paths)):
            if not archive_path.exists():
                continue

            logging.info("Checksumming: %s", archive_path.name)
            checksum = calculate_sha256(archive_path)
            file_handle.write(f"{checksum}  {archive_path.name}\n")

    os.replace(partial_manifest, manifest_path)


def parse_args() -> argparse.Namespace:
    default_source = load_default_source()
    default_output = default_source.parent / "processed_archives_7z"

    parser = argparse.ArgumentParser(
        description="Archive data/processed with 7-Zip, one top-level folder per .7z archive."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=default_source,
        help=f"Folder to archive. Default: {default_source}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Archive output folder. Default: {default_output}",
    )
    parser.add_argument(
        "--seven-zip",
        help="Path to 7z.exe if it is not on PATH.",
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=range(0, 10),
        metavar="0-9",
        default=3,
        help="7-Zip compression level. Default: 3 for a speed-biased archive.",
    )
    parser.add_argument(
        "--threads",
        default="on",
        help="7-Zip thread setting, such as on, off, 8, or 16. Default: on.",
    )
    parser.add_argument(
        "--solid",
        choices=["on", "off"],
        default="off",
        help="Solid archive mode. Default: off for better corruption isolation.",
    )
    parser.add_argument(
        "--volume-size",
        help="Split archives into volumes, for example 25g, 50g, or 100g.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only archive these top-level folder names.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing completed archives.",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip 7-Zip archive integrity tests after creation.",
    )
    parser.add_argument(
        "--no-checksums",
        action="store_true",
        help="Skip writing checksums_sha256.txt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run without creating archives.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable the optional tqdm file progress bar.",
    )

    return parser.parse_args()


def configure_logging(output_dir: Path, dry_run: bool) -> None:
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if not dry_run:
        handlers.append(logging.FileHandler(output_dir / "archive_processed_7zip.log", encoding="utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=handlers,
    )


def main() -> None:
    args = parse_args()
    source_dir = args.source.resolve()
    output_dir = args.output.resolve()

    configure_logging(output_dir, dry_run=args.dry_run)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_dir}")

    if output_dir == source_dir or source_dir in output_dir.parents:
        raise ValueError("Output directory must not be inside the source directory.")

    try:
        seven_zip = find_7zip(args.seven_zip)
    except FileNotFoundError:
        if not args.dry_run:
            raise
        seven_zip = args.seven_zip or "7z"
        logging.warning("7-Zip was not found; dry-run commands will use placeholder: %s", seven_zip)

    logging.info("Using 7-Zip: %s", seven_zip)
    logging.info("Source: %s", source_dir)
    logging.info("Output: %s", output_dir)
    logging.info(
        "Settings: level=%s, threads=%s, solid=%s, test=%s, checksums=%s",
        args.level,
        args.threads,
        args.solid,
        not args.no_test,
        not args.no_checksums,
    )

    top_level_dirs = sorted(path for path in source_dir.iterdir() if path.is_dir())

    if args.only:
        requested = set(args.only)
        top_level_dirs = [path for path in top_level_dirs if path.name in requested]
        missing = sorted(requested - {path.name for path in top_level_dirs})

        if missing:
            raise FileNotFoundError(f"Requested folders not found in {source_dir}: {', '.join(missing)}")

    if not top_level_dirs:
        raise RuntimeError(f"No top-level folders found in: {source_dir}")

    logging.info("Found %d top-level folders to archive", len(top_level_dirs))

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    archive_paths: list[Path] = []
    failed_dirs: list[str] = []

    file_progress = None
    if tqdm is None and not args.no_progress:
        logging.warning("tqdm is not installed; file-level progress bar is disabled")
    elif tqdm is not None and not args.no_progress and not args.dry_run:
        logging.info("Counting files for progress bar")
        total_files = 0
        for directory in top_level_dirs:
            final_archive = output_dir / f"{directory.name}.7z"
            if (final_archive.exists() or archive_has_volume_parts(final_archive)) and not args.overwrite:
                continue
            total_files += count_files(directory)

        file_progress = tqdm(
            total=total_files,
            unit="file",
            desc="Files zipped",
            dynamic_ncols=True,
        )

    try:
        for index, directory in enumerate(top_level_dirs, start=1):
            if file_progress is not None:
                file_progress.set_postfix_str(directory.name)

            logging.info("Processing %d of %d: %s", index, len(top_level_dirs), directory.name)

            try:
                archive_paths.extend(
                    archive_directory(
                        seven_zip,
                        directory,
                        output_dir,
                        level=args.level,
                        threads=args.threads,
                        solid=args.solid,
                        volume_size=args.volume_size,
                        test_archive=not args.no_test,
                        dry_run=args.dry_run,
                        overwrite=args.overwrite,
                        file_progress=file_progress,
                    )
                )
            except Exception:
                logging.exception("FAILED: %s", directory.name)
                failed_dirs.append(directory.name)
    finally:
        if file_progress is not None:
            file_progress.close()

    if archive_paths and not args.no_checksums:
        write_checksum_manifest(output_dir, archive_paths, dry_run=args.dry_run)

    logging.info("Batch complete")
    logging.info("Successful or previously completed folders: %d", len(top_level_dirs) - len(failed_dirs))
    logging.info("Failed folders: %d", len(failed_dirs))

    if failed_dirs:
        logging.error("Folders requiring another attempt: %s", ", ".join(failed_dirs))
        sys.exit(1)


if __name__ == "__main__":
    main()
