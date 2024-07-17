from pathlib import Path
import os

BASE_PATH: str = './data'
DATA_FOLDER: Path = Path('./data')
DATA_RAW: str = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE: str = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED: str = os.path.join(BASE_PATH, 'processed')
EXPORTS_FOLDER: Path = DATA_FOLDER / 'exports'
EXPORTS_FOLDER.mkdir(parents=True, exist_ok=True)