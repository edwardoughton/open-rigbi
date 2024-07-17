#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# run.py file for OpenRigbi, designed to visualize risk to telecom
# infrastructure due to natural disasters
#
# SPDX-FileCopyrightText: 2024 Aryaman Rajaputra <arajaput@gmu.edu>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by Aryaman Rajaputra

from preprocess import FloodRisk, convert_to_stations, all_new_lengths
from constants import DATA_RAW, EXPORTS_FOLDER

import pandas as pd

if __name__ == "__main__":
    country_code = input("Enter the ISO 3166-1 alpha-2 country code: ").upper().strip()
    country_code_3 = input("Enter the ISO 3166-1 alpha-3 country code: ").upper().strip()
    flood_scenario = input("Enter the *name* of the scenario you wish to run (not the full path): ")
    print("Country code entered:", country_code)
    g = FloodRisk(country_code, country_code_3, flood_scenario)
    ocid = g.preprocess()

    mobile_codes = pd.read_csv(f"{DATA_RAW}/mobile_codes.csv")
    mcc = mobile_codes['mcc'].drop_duplicates().to_list()
    fr = FloodRisk('NA')
    data_dict = fr.preprocess(*mcc)
    print(data_dict.keys())
    convert_to_stations(data_dict)
    pd.DataFrame.from_dict(all_new_lengths).to_csv(f"{EXPORTS_FOLDER}/data_lengths.csv", index=False)
    
    """
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