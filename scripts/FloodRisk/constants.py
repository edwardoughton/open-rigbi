from pathlib import Path

BASE_PATH: Path = Path('./data')
DATA_FOLDER: Path = Path('./data')
DATA_RAW: Path = Path(BASE_PATH / 'raw')
DATA_INTERMEDIATE: Path = Path(BASE_PATH / 'intermediate')
DATA_PROCESSED: Path = Path(BASE_PATH / 'processed')
EXPORTS_FOLDER: Path = Path(DATA_FOLDER / 'exports')
EXPORTS_FOLDER.mkdir(parents=True, exist_ok=True)