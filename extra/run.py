
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
from constants import *
from preprocess import FloodRisk
from process import GID
from pathlib import Path
from joblib import Parallel, delayed
import pandas as pd
from tqdm import tqdm

if __name__ == "__main__":
    # Load data
    mobile_codes = pd.read_csv(f"../{BASE_PATH}/mobile_codes.csv", encoding='latin1')
    mobile_codes = mobile_codes.drop_duplicates(subset=['mcc'])
    df = pd.read_csv(f"../{BASE_PATH}/countries.csv", encoding='latin-1')
    df = df[df['Exclude'] != 1]

    def process_country(country_code):
        try:
            country_code_2 = df[df['iso3'] == country_code]['iso2'].values[0]
            mcc = mobile_codes[mobile_codes['iso3'] == country_code]['mcc'].values[0]
            print(f"Processing Country code: {country_code}")

            fr = FloodRisk(country_code_2, country_code)
            main_feature = fr.preprocess(mcc)
            result_df = fr.process(main_feature, None, None, None)

            return country_code, result_df
        except Exception as e:
            print(f"Error processing country code {country_code}: {e}")
            return country_code, pd.DataFrame()

    results = Parallel(n_jobs=-1)(delayed(process_country)(country_code) for country_code in df['iso3'])

    combined_df = pd.concat([result_df for _, result_df in results], ignore_index=True)

    combined_df.to_csv(f"../{BASE_PATH}/combined_output.csv", index=False)

    print(f"Length of the combined DataFrame: {len(combined_df)}")
    
    """
    for feature in os.listdir(f"./{DATA_PROCESSED}/{country_code.upper()}/regions"):
        if feature.endswith(".shp"):
            feature_name = Path(feature).stem
            feature = gpd.read_file(f"./{DATA_PROCESSED}/{country_code.upper()}/regions/{feature}")
            features = fr.process(feature, Path(""), feature_name, "")
            features.to_csv(f"./{EXPORTS_FOLDER}/{country_code.upper()}/{feature_name}.csv", index=False)

            for scenario in os.listdir(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/flood_layer/{country_code.lower()}/wri_aqueduct.version_2"):
                scenario_path = f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/flood_layer/{country_code.lower()}/wri_aqueduct.version_2/{scenario}"
                scenario_name = Path(scenario).stem
                g.process(feature, scenario_path, feature_name, scenario_name)
    """
