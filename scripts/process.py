"""
Process sites data.

Ed Oughton

February 2022

"""
import sys
import os
import configparser
import pandas as pd
import geopandas as gpd
import time
# from shapely.ops import transform
# from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon
from shapely.geometry import Point
import rasterio
from rasterio.transform import rowcol
from tqdm import tqdm

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="geopandas")

from misc import get_countries, get_scenarios, get_regions, get_f_curves
from collect import collect_regional_results, collect_final_results

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def run_site_processing(country):
    """
    Meta function for running site processing.

    """
    regional_level = int(country['gid_region'])
    gid_level = 'GID_{}'.format(regional_level)

    scenarios = get_scenarios()
    regions = get_regions(country, regional_level)

    for region in regions:

        # if not region['GID_2'] == 'USA.1.49_1':
        #     continue

        # print('Working on process_flooding_extent_stats')
        process_flooding_extent_stats(country, region, scenarios, regional_level)

        # # # # # print('Working on query_hazard_layers')
        # query_hazard_layers(country, region, scenarios, regional_level)

        # # # # # print('--Estimating results')
        # estimate_results(country, region, scenarios, regional_level)

        # # # # print('--Converting to regional results')
        # convert_to_regional_results(country, region, scenarios, regional_level)

        # break

    return print('Completed processing')


def process_flooding_extent_stats(country, region, scenarios, regional_level):
    """
    Get aggregate statistics on flooding extent by region.

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level) #regional_level
    region = region[gid_level]

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'hazards', 'flooding', 'regional')

    for scenario_path in scenarios:#[:1]:

        #if not 'inuncoast_rcp8p5_wtsub_2080_rp1000_0' in scenario_path:
        #    continue

        filename = os.path.basename(scenario_path).replace('.tif','')

        folder_out = os.path.join(DATA_PROCESSED,'results','validation','country_data',
            country['iso3'], 'regional', filename)

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        path_out = os.path.join(folder_out, region + '_' + filename + '.csv')

        if os.path.exists(path_out):
            continue

        # print('Working on flood extent for {}'.format(filename))

        metrics = []

        path = os.path.join(folder, region + '_' + filename + '.tif')

        if not os.path.exists(path):
            # print('path does not exist: {}'.format(path))

            continue
        # print(path)
        # try:
        raster = rasterio.open(path)
        data = raster.read(1)
        # except:
        #     print('reading failed {}'.format(filename))
        #     continue

        output = []
        depths = []

        for idx, row in enumerate(data):
            for idx2, i in enumerate(row):
                if i >= 0.000001 and i < 150:
                    coords = raster.transform * (idx2, idx)
                    depths.append(i)
                    # print(i)
                else:
                    continue

        depths.sort()

        if 'river' in filename:
            hazard = filename.split('_')[0]
            climate_scenario = filename.split('_')[1]
            model = filename.split('_')[2]
            year = filename.split('_')[3]
            return_period = filename.split('_')[4]#[:-4]
            percentile = '-'

        if 'coast' in filename:
            hazard = filename.split('_')[0]
            climate_scenario = filename.split('_')[1]
            model = filename.split('_')[2]
            year = filename.split('_')[3]
            return_period = filename.split('_')[4]
            remaining_portion = filename.split('_')[5]
            if remaining_portion == '0':
                percentile = 0
            else:
                percentile = filename.split('_')[7]#[:-4]

        if len(depths) == 0:
            continue

        metrics.append({
            'hazard': hazard,
            'climate_scenario': climate_scenario,
            'model': model,
            'year': year,
            'return_period': return_period,
            'percentile': percentile,
            'min_depth': round(min(depths),2),
            'mean_depth': sum(depths) / len(depths),
            'median_depth': depths[len(depths)//2],
            'max_depth': max(depths),
            'flooded_area_km2': len(depths),
        })

        metrics = pd.DataFrame(metrics)
        metrics.to_csv(path_out, index=False)

    return


def query_hazard_layers(country, region, scenarios, regional_level):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level) #regional_level
    region = region[gid_level]

    filename = 'coastal_lookup.csv'
    folder = os.path.join(DATA_PROCESSED, iso3, 'coastal')
    path_coastal = os.path.join(folder, filename)
    if not os.path.exists(path_coastal):
        coastal_lut = []
    else:
        coastal_lut = pd.read_csv(path_coastal)
        coastal_lut = list(coastal_lut['gid_id'])

    for scenario in scenarios: #tqdm(scenarios):

        scenario_name = os.path.basename(scenario).replace('.tif', '')

        output = []

        filename = '{}_{}_unique.gpkg'.format(region, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', 
                                  region, 'flood_scenarios')
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_output = os.path.join(folder_out, filename)

        if os.path.exists(path_output):
           continue

        if 'inuncoast' in scenario and region not in coastal_lut:
            # print('not coastal: {} in {}'.format(region, scenario))
            continue

        filename = '{}_{}.tif'.format(region, scenario_name)
        folder_in = os.path.join(DATA_PROCESSED, iso3, 'hazards', 
                                 'flooding', 'regional')
        path_in = os.path.join(folder_in, filename)

        if not os.path.exists(path_in):
            # print('path did not exist: {}'.format(path_in))
            continue

        filename = '{}_unique.gpkg'.format(region)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
        path_sites = os.path.join(folder, filename)

        if not os.path.exists(path_sites):
            # print('path did not exist: {}'.format(path_sites))
            continue

        sites = gpd.read_file(path_sites)

        # Ensure folder_out exists
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = []

        # Open the raster file
        with rasterio.open(path_in) as src:
            raster_data = src.read(1)
            transform = src.transform

            # Iterate over each site in the GeoDataFrame
            for _, site in sites.iterrows():

                x = float(site['longitude'])
                y = float(site['latitude'])

                # Map longitude/latitude to raster row/col
                row, col = rowcol(transform, x, y)

                # Check if coordinates are within raster bounds
                if 0 <= row < raster_data.shape[0] and 0 <= col < raster_data.shape[1]:
                    depth = raster_data[row, col]
                else:
                    depth = 255  # Handle out-of-bounds

                # Ensure depth is not negative
                depth = max(depth, 0)

                # Append processed data
                output.append({
                    'geometry': Point(x, y),
                    'properties': {
                        'radio': site.get('radio'),
                        'net': site.get('net'),
                        'latitude': site['latitude'],
                        'longitude': site['longitude'],
                        'gid_level': gid_level,
                        'gid_id': region,
                        'depth': depth,
                    }
                })

        if len(output) == 0:
            return

        output = gpd.GeoDataFrame.from_features(output)
        output.set_crs("EPSG:4326", inplace=True)

        # if os.path.exists(path_output):
        #     os.remove(path_output)

        output.to_file(path_output, driver="GPKG")

    return


def estimate_results(country, region, scenarios, regional_level):
    """
    Relate the exposure value to the vulnerability curve.  

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level)
    region = region[gid_level]

    # filename = 'fragility_curve.csv'
    # path_fragility = os.path.join(DATA_RAW, filename)
    low, baseline, high = load_f_curves() #path_fragility)

    filename = 'coastal_lookup.csv'
    folder = os.path.join(DATA_PROCESSED, iso3, 'coastal')
    path_coastal = os.path.join(folder, filename)
    if not os.path.exists(path_coastal):
        coastal_lut = []
    else:
        coastal_lut = pd.read_csv(path_coastal)
        coastal_lut = list(coastal_lut['gid_id'])

    for scenario in scenarios: #tqdm

        output = []

        scenario_name = os.path.basename(scenario)#[:-4]

        # if not region == 'EGY.1_1':
        #     continue

        filename = '{}_{}_unique.csv'.format(region, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario_name)
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_output = os.path.join(folder_out, filename)

        if os.path.exists(path_output):
            # print('path_output exists {}'.format(path_output))
            continue

        if 'inuncoast' in scenario and region not in coastal_lut:
            # print('if inuncoast in scenario and region not in coastal_lut:')
            continue

        filename = '{}_{}_unique.gpkg'.format(region, scenario_name)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', 
                              region, 'flood_scenarios')
        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            # print('path_in does not exist {}'.format(path_in))
            continue
        
        sites = gpd.read_file(path_in)
        sites = sites[(sites['depth'] > 0.001) & (sites['depth'] < 200)]

        sites = sites.to_dict('records')

        for site in sites:

            damage_low = query_fragility_curve(low, site['depth'])
            damage_baseline = query_fragility_curve(baseline, site['depth'])
            damage_high = query_fragility_curve(high, site['depth'])

            output.append({
                'radio': site['radio'],
                'net': site['net'],
                # 'cell': site['cell'],
                'latitude': site['latitude'],
                'longitude': site['longitude'],
                'gid_level': gid_level,
                'gid_id': region,
                # 'cellid4326': site['cellid4326'],
                'depth': site['depth'],
                'damage_low': damage_low,
                'damage_baseline': damage_baseline,
                'damage_high': damage_high,
                'cost_usd_low': round(33333.333 * damage_low),
                'cost_usd_baseline': round(33333.333 * damage_baseline),
                'cost_usd_high': round(33333.333 * damage_high),
            })

        if len(output) == 0:
            output.append({
                'radio': 'NA',
                'net': 'NA',
                'cell': 'NA',
                'latitude': 'NA',
                'longitude': 'NA',
                'gid_level': 'NA',
                'gid_id': 'NA',
                'cellid4326': 'NA',
                'depth': 'NA',
                'damage_low': 'NA',
                'damage_baseline': 'NA',
                'damage_high': 'NA',
                'cost_usd_low': 'NA',
                'cost_usd_baseline': 'NA',
                'cost_usd_high': 'NA',
            })

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = pd.DataFrame(output)
        output.to_csv(path_output)

    return


def load_f_curves():
    """
    Load depth-damage curves.

    """
    low = []
    baseline = []
    high = []

    f_curves = get_f_curves()

    for item in f_curves:

        my_dict = {
            'depth_lower_m': item['depth_lower_m'],
            'depth_upper_m': item['depth_upper_m'],
            'damage': item['damage'],
        }

        if item['scenario'] == 'low':
            low.append(my_dict)
        elif item['scenario'] == 'baseline':
            baseline.append(my_dict)
        elif item['scenario'] == 'high':
            high.append(my_dict)

    return low, baseline, high


def query_fragility_curve(f_curve, depth):
    """
    Query the fragility curve.

    """
    if depth < 0:
        return 0

    for item in f_curve:
        if item['depth_lower_m'] <= depth < item['depth_upper_m']:
            return item['damage']
        else:
            continue

    if depth >= max([d['depth_upper_m'] for d in f_curve]):
        return 1

    print('fragility curve failure: {}'.format(depth))

    return 0


def convert_to_regional_results(country, region, scenarios, regional_level):
    """
    Collect all results.

    """
    scenarios = get_scenarios()#[::-1]

    iso3 = country['iso3']
    # name = country['country']
    gid_level = 'GID_{}'.format(regional_level)
    region = region[gid_level]

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 
                              'regional_aggregated', 'regions')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    for scenario in scenarios:
        # Prepare output list
        output = []

        # Extract scenario name and file paths
        scenario_name = os.path.basename(scenario)
        filename = f"{region}_{scenario_name}_unique.csv"
        folder_in = os.path.join(DATA_PROCESSED, iso3, 'results', 
                                 'regional_data', scenario_name)
        path_in = os.path.join(folder_in, filename)
        path_out = os.path.join(folder_out, filename)

        # Check if the input file exists
        if not os.path.exists(path_in):
            output.append({
                'iso3': country['iso3'],
                'iso2': country['iso2'],
                'country': country['country'],
                'continent': country['continent'],
                'gid_level': 'NA',
                'gid_id': 'NA',
                'radio': 'NA',
                'network': 'NA',
                'cell_count_low': 0,
                'cell_count_baseline': 0,
                'cell_count_high': 0,
                'cost_usd_low': 0,
                'cost_usd_baseline': 0,
                'cost_usd_high': 0,
            })
            continue

        # Load data
        data = pd.read_csv(path_in)

        # Handle empty dataframes
        if data.empty:
            continue

        # Filter out rows with 'NA' in 'cost_usd_baseline'
        data = data[data['cost_usd_baseline'] != 'NA']

        # Group by 'gid_id' and calculate aggregated values
        grouped = data.groupby('gid_id').agg(
            cell_count_low=('cost_usd_low', lambda x: (x > 0).sum()),
            cost_usd_low=('cost_usd_low', 'sum'),
            cell_count_baseline=('cost_usd_baseline', lambda x: (x > 0).sum()),
            cost_usd_baseline=('cost_usd_baseline', 'sum'),
            cell_count_high=('cost_usd_high', lambda x: (x > 0).sum()),
            cost_usd_high=('cost_usd_high', 'sum'),
        ).reset_index()

        # Add metadata columns
        grouped['iso3'] = country['iso3']
        grouped['iso2'] = country['iso2']
        grouped['country'] = country['country']
        grouped['continent'] = country['continent']
        grouped['gid_level'] = gid_level

        # Append to output list
        output.append(grouped)

        # If no valid output, skip writing
        if not output:
            continue

        # Combine all outputs and save to CSV
        final_output = pd.concat(output, ignore_index=True)
        final_output.to_csv(path_out, index=False)

    return


if __name__ == "__main__":

    start_time = time.time()

    countries = get_countries()

    failures = []

    for country in tqdm(countries[::-1]):

        # if not country['iso3'] in ['GBR']:
        #     continue

        print(f"--Working on {country['country']}")
        run_site_processing(country)

    # scenarios = get_scenarios()
    # for scenario in scenarios:
    #     collect_regional_results(scenario)
    #     collect_final_results(scenario)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Function executed in {elapsed_time:.2f} seconds")