"""import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from misc import get_regions, get_scenarios
from joblib import Parallel, delayed

errors = []
successes = []

def get_scenarios():
    scenarios = []
    for root, dirs, files in os.walk("/home/cisc/projects/open-rigbi/data/raw/flood_hazard"):
        for file in files:
            if file.endswith(".shp"):
                scenarios.append(os.path.join(root, file))
    return scenarios

def validate_country(country, scenarios):
    country_dict = {}
    mobile_codes = pd.read_csv(f"../{BASE_PATH}/mobile_codes.csv", encoding='latin1')
    mobile_codes = mobile_codes.drop_duplicates(subset=['mcc'])
    df = pd.read_csv(f"../{BASE_PATH}/countries.csv", encoding='latin-1')
    df = df[df['Exclude'] != 1]
    print("Loaded data")
    level = df.loc[df['iso3'] == country_code, 'gid_region'].values[0]
    level = int(level)
    country_data_path = f"/home/cisc/projects/open-rigbi/data/processed/{country}"
    regions = get_regions(country, level)
    for region in regions:
        region = region['GID_{}'.format(level)]
        for scenario in scenarios:
            try:
                scenario_name = os.path.basename(scenario).split(".")[0]
                official_path = f"/home/cisc/projects/open-rigbi/data/processed/{country.upper()}/hazards/flooding/regional/{country.upper()}.{region}_{scenario_name}.tif"
                if not os.path.exists(official_path):
                    print(f"Missing {official_path}")
                    errors.append(official_path)
                else:
                    print(f"Found {official_path}")

            except Exception as e:
                print(f"Error processing {scenario}: {e}")
                errors.append(scenario)
"""
"""
Collect validation results.

"""
import sys
import os
import configparser
import pandas as pd

from misc import get_scenarios, get_regions, get_tropical_storm_scenarios

BASE_PATH = f"/home/cisc/projects/open-rigbi/data/"
DATA_RAW = f"/home/cisc/projects/open-rigbi/data/raw"
# DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
DATA_PROCESSED = f"/home/cisc/projects/open-rigbi/data/processed"

def get_countries():
    """
    Get all countries.

    """
    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]
    countries = countries.to_dict('records')
    #countries = countries.sort_values(by=['Population'], ascending=True)
    #countries = countries.sample(frac=1)
    return countries#[:10]

def collect(countries, scenarios):
    """
    Collect validation results.

    """
    # gid_level = 'GID_{}'.format(country['gid_region'])

    folder_in = os.path.join(DATA_PROCESSED, 'results', 'validation', 'country_data')
    #folder_out = os.path.join(DATA_PROCESSED, 'results', 'validation')

    for country in countries:
        
        #if not country['iso3'] in ['ARG']:
        #    continue

        print("Working on {}".format(country['iso3']))

        output = []

        for scenario_path in scenarios:#[:1]:

            if '_perc_' in scenario_path:
                continue

            scenario = os.path.basename(scenario_path).replace('.tif','')

            print('Working on {}'.format(scenario))

            country_folder = os.path.join(folder_in, country['iso3'], 'regional', scenario)

            min_depth = []
            mean_depth = []
            max_depth = []
            flooded_area_km2 = []

            if os.path.exists(country_folder):
                file_paths = os.listdir(country_folder)
                for filename in file_paths:

                    if not scenario in os.path.basename(filename).replace('.tif',''):
                        continue

                    path = os.path.join(country_folder, filename)
                    if not os.path.exists(path):
                        continue
                    else:
                        try:
                            data = pd.read_csv(path)
                        except:
                            continue
                        data = data.to_dict('records')
                        min_depth.append(data[0]['min_depth'])
                        mean_depth.append(data[0]['mean_depth'])
                        max_depth.append(data[0]['max_depth'])
                        flooded_area_km2.append(data[0]['flooded_area_km2'])

                if len(flooded_area_km2) > 0:
                    min_depth = min(min_depth)
                    mean_depth = sum(mean_depth) / len(mean_depth)
                    max_depth = max(max_depth)
                    flooded_area_km2 = sum(flooded_area_km2)
                else:
                    min_depth = "-"
                    mean_depth = "-"
                    median_depth = "-"
                    max_depth = "-"
                    flooded_area_km2 = "-"
            else:
                min_depth = "-"
                mean_depth = "-"
                median_depth = "-"
                max_depth = "-"
                flooded_area_km2 = "-"
            
            if 'river' in scenario:
                hazard = scenario.split('_')[0]
                climate_scenario = scenario.split('_')[1]
                model = scenario.split('_')[2]
                year = scenario.split('_')[3]
                return_period = scenario.split('_')[4]#[:-4]
                percentile = '-'

            if 'coast' in scenario:
                hazard = scenario.split('_')[0]
                climate_scenario = scenario.split('_')[1]
                model = scenario.split('_')[2]
                year = scenario.split('_')[3]
                return_period = scenario.split('_')[4]
                remaining_portion = scenario.split('_')[5]

                if not len(scenario.split('_')) > 6:
                    percentile = 0
                else:
                    percentile = scenario.split('_')[7]#[:-4]

            output.append({
                'iso3': country['iso3'],
                'hazard': hazard,
                'climate_scenario': climate_scenario,
                'model': model,
                'year': year,
                'return_period': return_period,
                'percentile': percentile,
                'min_depth': min_depth,
                'mean_depth': mean_depth,
                'max_depth': max_depth,
                'flooded_area_km2': flooded_area_km2,
            })

        output = pd.DataFrame(output)
        final_folder = os.path.join(folder_in, country['iso3'])
        if not os.path.exists(final_folder):
            continue 
        output.to_csv(os.path.join(final_folder, 'scenario_stats.csv'), index=False)

    return


def collect_all(countries):
    """
    Collect all results. 

    """
    folder_in = os.path.join(DATA_PROCESSED,'results','validation','country_data')

    output = []

    for country in countries:
        
        #if not country['iso3'] == 'USA':
        #    continue

        path = os.path.join(folder_in,country['iso3'],'scenario_stats.csv')

        if not os.path.exists(path):
            continue

        data = pd.read_csv(path)

        data = data.to_dict('records')

        output = output + data

    output = pd.DataFrame(output)
    output.to_csv(os.path.join(folder_in,'..','scenario_stats.csv'),index=False)

    return


if __name__ == "__main__":


    countries = get_countries()
    scenarios = get_scenarios()
    #scenarios_tropical = get_tropical_storm_scenarios()

    # scenarios = scenarios

    collect(countries, scenarios)

    collect_all(countries)


    
        
            