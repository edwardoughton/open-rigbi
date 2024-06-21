import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point

import math
import os
from pathlib import Path

BASE_PATH: str = './data'
DATA_FOLDER: Path = Path('./data')
DATA_RAW: str = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE: str = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED: str = os.path.join(BASE_PATH, 'processed')
EXPORTS_FOLDER: Path = DATA_FOLDER / 'exports'
EXPORTS_FOLDER.mkdir(parents=True, exist_ok=True)

class FloodRisk:
    def __init__(self, iso3):
        self.iso3 = iso3

    def preprocess(self, *codes):
        if not os.path.exists(f"{DATA_PROCESSED}/{self.iso3.upper()}") and not os.path.isdir(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions"):
            os.makedirs(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions")
            print(f"Created directory {DATA_PROCESSED}/{self.iso3.upper()}")
        else:
            print(f"Directory {DATA_PROCESSED}/{self.iso3.upper()} already exists")

        path = f"{DATA_PROCESSED}/{self.iso3.upper()}/regions"
        mcc_data = {}  # Dictionary to store GeoDataFrames for each MCC code
        total_rows = sum(1 for _ in open(f"{DATA_RAW}/cell_towers_2022-12-24.csv")) - 1  # Subtract 1 for the header row
        chunksize = 1000

        for code in codes:  # Loop over each MCC code
            features = []
            chunk_count = 0
            total_chunks = math.ceil(total_rows / chunksize)

            for chunk in pd.read_csv(f"{DATA_RAW}/cell_towers_2022-12-24.csv", chunksize=chunksize):
                # Filter rows by the current MCC code
                filtered_chunk = chunk[chunk["mcc"] == code]
                if not filtered_chunk.empty:
                    filtered_chunk['geometry'] = [Point(row.lon, row.lat) for row in filtered_chunk.itertuples()]
                    gdf_chunk = gpd.GeoDataFrame(filtered_chunk, geometry='geometry')
                    features.append(gdf_chunk)
                    chunk_count += 1
                    print(f"Processed chunk {chunk_count}/{total_chunks} for MCC {code}")

            if features:  # If there are features for the current MCC code
                all_features = pd.concat(features, ignore_index=True)
                output_path = f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}.shp"
                all_features.to_file(output_path)
                print(f"Saved {code} data to {output_path}")
                mcc_data[code] = all_features  # Store the GeoDataFrame in the dictionary

        return mcc_data

all_new_lengths = []
def convert_to_stations(data_dict):
    for country_code, data in data_dict.items():
        print(f"Processing {country_code}")
        print(data.head(10))

        data['bs_id_float'] = data['cell'] / 256
        data['bs_id_int'] = np.round(data['bs_id_float'], 0)
        data['sector_id'] = data['bs_id_float'] - data['bs_id_int']
        data['sector_id'] = np.round(data['sector_id'].abs() * 256)

        unique_bs_id_int = data['bs_id_int'].drop_duplicates()
        unique_sector_id_int = data['sector_id'].drop_duplicates()

        new_lengths = {
            'Country': country_code,
            'Unique 4G Stations': len(data),
            'Unique BS ID Int': len(unique_bs_id_int),
            'Unique Sector ID Int': len(unique_sector_id_int)
        }
        all_new_lengths.append(new_lengths)

    return all_new_lengths

    # Plotting
def plot(lengths, radio_len):
    fig, ax = plt.subplots(figsize=(10, 6))
    countries = [x['Country'] for x in all_new_lengths]
    unique_stations = [x['Unique 4G Stations'] for x in all_new_lengths]
    unique_bs_id_int = [x['Unique BS ID Int'] for x in all_new_lengths]
    unique_sector_id_int = [x['Unique Sector ID Int'] for x in all_new_lengths]

    bar_width = 0.25
    r1 = np.arange(len(countries))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]
    r4 = [x + bar_width for x in r3]

    plt.bar(r1, unique_stations, color='blue', width=bar_width, label='Unique 4G Stations')
    plt.bar(r2, unique_bs_id_int, color='green', width=bar_width, label='Unique BS ID Int')
    plt.bar(r3, unique_sector_id_int, color='red', width=bar_width, label='Unique Sector ID Int')
    plt.bar(r4, radio_len, color='yellow', width=bar_width, label='Radio Data Length')

    plt.xlabel('Country')
    plt.ylabel('Count')
    plt.title('Comparison of Data Lengths by Country')
    plt.xticks([r + bar_width for r in range(len(countries))], countries, rotation=45)
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    fr = FloodRisk('NA')
    data_dict = fr.preprocess(276, 505, 302, 712, 234, 639, 204, 530, 608)
    print(data_dict.keys())
    convert_to_stations(data_dict)
    alb_radio = pd.DataFrame({'Country': 'ALB', 'Stations': 0}, index=[0])
    
    alb_radio = pd.read_csv(f"../data/raw/countries_data/ALB/lte_cells.csv", encoding="latin1")
    aus_radio = pd.read_csv(f"../data/raw/countries_data/AUS/spectra_rrl/site.csv")
    can_radio = pd.read_csv(f"../data/raw/countries_data/CAN/Site_Data_Extract.csv")
    cri_radio = pd.read_csv(f"../data/raw/countries_data/CRI/Mobile Network Coverage and antenna characteristics_Costa Rica.csv")
    gbr_radio = pd.read_csv(f"../data/raw/countries_data/GBR/results.csv")
    gmb_radio = pd.read_excel(f"../data/raw/countries_data/GMB/Gambia Network_Africell.xlsx")
    ken_radio = pd.read_csv(f"../data/raw/countries_data/KEN/all_sites.csv")
    nld_radio = pd.read_csv(f"../data/raw/countries_data/NLD/Antennetotalen+jaaroverzicht+2023.csv")
    nzl_radio = gpd.read_file(f"../data/raw/countries_data/NZL/cell_extract.shp")
    sen_radio = pd.read_csv(f"../data/raw/countries_data/SEN/results.csv")

    radio = [len(alb_radio), 
             len(aus_radio), 
             len(can_radio),
             len(cri_radio), 
             len(gbr_radio), 
             len(gmb_radio), 
             len(ken_radio), 
             len(nld_radio), 
             len(nzl_radio), 
             len(sen_radio)]
    
    plot(all_new_lengths, radio)

    