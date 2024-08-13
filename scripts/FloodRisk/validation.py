import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import math
import os
from pathlib import Path

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

DATA_RAW = "../data/raw"
DATA_PROCESSED = "./data/exports"

def preprocess(iso3, *codes):
    iso3_upper = iso3.upper()
    output_dir = f"{DATA_PROCESSED}/{iso3_upper}/regions"
    
    if not os.path.exists(output_dir) and not os.path.isdir(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory {output_dir}")
    else:
        print(f"Directory {output_dir} already exists")

    mcc_data = {}  # Dictionary to store GeoDataFrames for each MCC code
    total_rows = sum(1 for _ in open(f"{DATA_RAW}/cell_towers_2022-12-24.csv")) - 1  # Subtract 1 for the header row
    chunksize = 1000

    for code in codes:
        features = []
        chunk_count = 0
        total_chunks = math.ceil(total_rows / chunksize)

        for chunk in pd.read_csv(f"{DATA_RAW}/cell_towers_2022-12-24.csv", chunksize=chunksize):
            # Filter rows by the current MCC code and LTE radio type
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
            output_path = f"{output_dir}/processed_cell_towers_{iso3_upper}_{code}.shp"
            all_features.to_file(output_path)
            print(f"Saved {code} data to {output_path}")
            mcc_data[code] = all_features  # Store the GeoDataFrame in the dictionary

    return mcc_data

def convert_to_stations(data_dict):
    all_new_lengths = []
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

def main():
    # Read radio data
    alb_radio = pd.read_csv(f"../data/raw/countries_data/ALB/lte_cells.csv", encoding='latin-1')
    aus_radio = pd.read_csv(f"../data/raw/countries_data/AUS/spectra_rrl/site.csv")  # Fixed to use pd.read_csv
    can_radio = gpd.read_file(f"../data/raw/countries_data/CAN/sites/sites_all.shp")
    cri_radio = pd.read_excel(f"../data/raw/countries_data/CRI/RadioBases móviles I Semestre 2020.xlsx")
    cri_radio = cri_radio.dropna(subset=['Unnamed: 7'])
    cri_radio = cri_radio[cri_radio['Unnamed: 7'].str.contains('4G')]
    gbr_radio = gpd.read_file(f"../data/raw/countries_data/GBR/sites.shp")
    gmb_radio = pd.read_excel(f"../data/raw/countries_data/GMB/Gambia Network_Africell.xlsx", sheet_name='4G Cells')
    ken_radio = pd.read_csv(f"../data/raw/countries_data/KEN/all_sites.csv")
    ken_radio = ken_radio.drop_duplicates(subset=['cellName'])
    nld_radio = pd.read_csv(f"../data/raw/countries_data/NLD/Antennetotalen+jaaroverzicht+2023.csv")
    nld_radio = nld_radio[nld_radio['Toepassing'] == 'LTE']
    nzl_radio = gpd.read_file(f"../data/raw/countries_data/NZL/cell_extract.shp")
    sen_radio = pd.read_csv(f"../data/raw/countries_data/SEN/Bilan_Couverture_Orange_Dec2017.csv", encoding="latin1")
    sen_radio = sen_radio.drop_duplicates(subset=["Cell_ID"])

    # Count of radio data
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

    # Read processed OCID data
    alb_ocid = pd.read_csv(f"./data/exports/ALB/towers_ALB.csv")
    aus_ocid = pd.read_csv(f"./data/exports/AUS/towers_AUS.csv")
    can_ocid = pd.read_csv(f"./data/exports/CAN/towers_CAN.csv")
    cri_ocid = pd.read_csv(f"./data/exports/CRI/towers_CRI.csv")
    gbr_ocid = pd.read_csv(f"./data/exports/GBR/towers_GBR.csv")
    gmb_ocid = pd.read_csv(f"./data/exports/GMB/towers_GMB.csv")
    ken_ocid = pd.read_csv(f"./data/exports/KEN/towers_KEN.csv")
    nld_ocid = pd.read_csv(f"./data/exports/NLD/towers_NLD.csv")
    nzl_ocid = pd.read_csv(f"./data/exports/NZL/towers_NZL.csv")
    sen_ocid = pd.read_csv(f"./data/exports/SEN/towers_SEN.csv")

    # Count of OCID data
    ocid = [len(alb_ocid),
            len(aus_ocid),
            len(can_ocid),
            len(cri_ocid),
            len(gbr_ocid),
            len(gmb_ocid),
            len(ken_ocid),
            len(nld_ocid),
            len(nzl_ocid),
            len(sen_ocid)]

    # Calculate difference
    difference = [(x - y) for x, y in zip(radio, ocid)]

    # Print the results
    for i, diff in enumerate(difference):
        country_code = list(MCC_TO_COUNTRY.values())[i]
        if diff < 0:
            print(f"OCID has more data than radio by {abs(diff)} for {country_code}")
        else:
            print(f"Radio has more data than OCID by {diff} for {country_code}")

if __name__ == "__main__":
    main()

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