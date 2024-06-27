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

MCC_TO_COUNTRY = {
    276: 'ALB',
    505: 'AUS',
    302: 'CAN',
    712: 'CRI',
    234: 'GBR',
    607: 'GMB',
    639: 'KEN',
    204: 'NLD',
    530: 'NZL',
    608: 'SEN'
}

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

            for chunk in pd.read_csv(f"{DATA_RAW}/cell_towers_2022-12-24.csv", chunksize=1000):
                #  Filter rows by the current MCC code and LTE radio type
                filtered_chunk = chunk[chunk['mcc'] == code]
                new_filtered_chunk = filtered_chunk[filtered_chunk['radio'] == 'LTE']
                if not new_filtered_chunk.empty:
                    new_filtered_chunk['geometry'] = [Point(row.lon, row.lat) for row in new_filtered_chunk.itertuples()]
                    gdf_chunk = gpd.GeoDataFrame(new_filtered_chunk, geometry='geometry')
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
    countries = [x['Country'] for x in lengths]
    unique_stations = [x['Unique 4G Stations'] for x in lengths]
    unique_bs_id_int = [x['Unique BS ID Int'] for x in lengths]
    unique_sector_id_int = [x['Unique Sector ID Int'] for x in lengths]

    bar_width = 0.25
    r1 = np.arange(len(countries))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]
    r4 = [x + bar_width for x in r3]

    country_names = [MCC_TO_COUNTRY[mcc] for mcc in countries]

    # Adjusted plotting values
    plt.bar(r1, [y / 10 for y in unique_stations], color='blue', width=bar_width, label='Unique 4G Stations')
    plt.bar(r2, [y / 10 for y in unique_bs_id_int], color='green', width=bar_width, label='Unique BS ID Int')
    plt.bar(r3, [y / 10 for y in unique_sector_id_int], color='red', width=bar_width, label='Unique Sector ID Int')
    plt.bar(r4, radio_len, color='yellow', width=bar_width, label='Radio Data Length')

    plt.xlabel('Country')
    plt.ylabel('Count')
    plt.title('Comparison of Data Lengths by Country')
    plt.xticks([r + bar_width for r in range(len(country_names))], country_names, rotation=45)
    plt.legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    fr = FloodRisk('NA')
    data_dict = fr.preprocess(276, 505, 302, 712, 234, 607, 639, 204, 530, 608)
    print(data_dict.keys())
    convert_to_stations(data_dict)
    
    alb_radio = pd.read_csv(f"../data/raw/countries_data/ALB/lte_cells.csv", encoding='latin-1') # This is already LTE
    aus_radio = gpd.read_file(f"../data/raw/countries_data/AUS/spectra_rrl/site.csv") # Australian data has no distinction between different -G's
    can_radio = gpd.read_file(f"../data/raw/countries_data/CAN/sites/sites_all.shp")
    cri_radio = pd.read_excel(f"../data/raw/countries_data/CRI/RadioBases móviles I Semestre 2020.xlsx")  
    cri_radio = cri_radio.dropna(subset=['Unnamed: 7'])
    cri_radio = cri_radio[cri_radio['Unnamed: 7'].str.contains('4G')]
    gbr_radio = gpd.read_file(f"../data/raw/countries_data/GBR/sites.shp") # This data also doesn't have a distinction between different -G's
    gmb_radio = pd.read_excel(f"../data/raw/countries_data/GMB/Gambia Network_Africell.xlsx", sheet_name='4G Cells') # This can be directly compared with OCID because it's cells
    ken_radio = pd.read_csv(f"../data/raw/countries_data/KEN/all_sites.csv") # Kenyan data has no distinction between different -G's
    ken_radio = ken_radio.drop_duplicates(subset=['cellName'])
    nld_radio = pd.read_csv(f"../data/raw/countries_data/NLD/Antennetotalen+jaaroverzicht+2023.csv", skiprows=1)
    nld_radio = nld_radio[nld_radio['Toepassing'] == 'LTE']
    nzl_radio = gpd.read_file(f"../data/raw/countries_data/NZL/cell_extract.shp") # New Zealand data has no distinction between different -G's
    sen_radio = pd.read_csv(f"../data/raw/countries_data/SEN/Bilan_Couverture_Orange_Dec2017.csv", encoding="latin1") # Senegalese data has no distinction between different -G's
    sen_radio = sen_radio.drop_duplicates(subset=["Cell_ID"])
    
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

    for i in all_new_lengths:
        print(i)
    print(radio)
    
    plot(all_new_lengths, radio)

    """
    MCC: OCID - Radio
    -----------------
    276: 657 - 4875
    505: 51753 - 103969
    302: 46902 - 565472
    712: 2391 - 3836 Close-ish?
    234: 57611 - 144311
    607: 5 - 176 I have no idea what happened here
    639: 1383 - 126220
    204: 20385 - 16388 this is okay
    530: 4450 - 4433 this is okay
    608:  604 - 3708 OCID is missing values here 
    """