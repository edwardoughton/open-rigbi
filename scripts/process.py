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
import pyproj
from shapely.ops import transform
from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon
# from tqdm import tqdm
import rasterio
import random

from misc import (process_country_shapes, process_regions, params, technologies,
    get_countries, get_regions, get_scenarios)
from flood_hazards import process_flooding_layers, process_surface_water

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def run_site_processing(region):
    """
    Meta function for running site processing.

    """
    iso3 = region[:3]

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    country = countries[countries.iso3 == iso3]
    country = country.to_dict('records')[0]

    regional_level = int(country['gid_region'])

    print('Getting scenarios')
    scenarios = get_scenarios()#[:5]

    # print('Working on create_national_sites_csv')
    # create_national_sites_csv(country)

    # print('Working on process_country_shapes')
    # process_country_shapes(iso3)

    #print('Working on process_regions')
    #process_regions(iso3, regional_level)

    # print('Working on create_national_sites_shp')
    # create_national_sites_shp(iso3)

    # # print('Working on process_surface_water_layers')
    # # process_surface_water(country, region)

    # if regional_level == 1:

    #     print('Working on segment_by_gid_1')
    #     segment_by_gid_1(iso3, 1, region)

    #     print('Working on create_regional_sites_layer')
    #     create_regional_sites_layer(iso3, 1, region)

    # if regional_level == 2:

    #     gid_1 = get_gid_1(region)

    #     print('Working on segment_by_gid_1')
    #     segment_by_gid_1(iso3, 1, gid_1)

    #     print('Working on create_regional_sites_layer')
    #     create_regional_sites_layer(iso3, 1, gid_1)

    #     print('Working on segment_by_gid_2')
    #     segment_by_gid_2(iso3, 2, region, gid_1)

    #     print('Working on create_regional_sites_layer')
    #     create_regional_sites_layer(iso3, 2, region)

    # #print('Working on process_flooding_layers')
    # #process_flooding_layers(country, scenarios)

    # print('Working on query_hazard_layers')
    # query_hazard_layers(country, region, scenarios, regional_level)

    # print('Estimate model-mean')
    # estimate_model_mean(country, region, scenarios, regional_level)

    print('Estimating results')
    estimate_results(country, region, scenarios, regional_level)

    print('Converting to regional results')
    convert_to_regional_results(country, region, scenarios)

    return print('Completed processing')


def create_national_sites_csv(country):
    """
    Create a national sites csv layer for a selected country.

    """
    iso3 = country['iso3']#.values[0]

    filename = "mobile_codes.csv"
    path = os.path.join(DATA_RAW, filename)

    mobile_codes = pd.read_csv(path)
    mobile_codes = mobile_codes[['iso3', 'mcc']].drop_duplicates()
    all_mobile_codes = mobile_codes[mobile_codes['iso3'] == iso3]
    all_mobile_codes = all_mobile_codes.to_dict('records')

    output = []

    for row in all_mobile_codes:

        mcc = row['mcc']

        filename = '{}.csv'.format(iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
        path_csv = os.path.join(folder, filename)

        ### Produce national sites data layers
        if not os.path.exists(path_csv):

            print('-site.csv data does not exist')
            print('-Subsetting site data for {}: {}'.format(iso3, mcc))

            if not os.path.exists(folder):
                os.makedirs(folder)

            filename = "cell_towers_2022-12-24.csv"
            path = os.path.join(DATA_RAW, filename)

            chunksize = 10 ** 6
            for idx, chunk in enumerate(pd.read_csv(path, chunksize=chunksize)):

                country_data = chunk.loc[chunk['mcc'] == mcc]#[:1]

                country_data = country_data.to_dict('records')

                output = output + country_data

    if len(output) == 0:
        # print('-{} had no data'.format(iso3))
        return

    output = pd.DataFrame(output)
    output.to_csv(path_csv, index=False)

    return


def get_gid_1(region):
    """
    Get gid_1 handle from gid_2
    """
    split = region.split('.')
    iso3 = split[0]
    item1 = split[1]
    item2 = split[2]
    item3 = split[2].split('_')[1]

    gid_2 = "{}.{}_{}".format(iso3, item1, item3)

    return gid_2


def segment_by_gid_1(iso3, level, region):
    """
    Segment sites by gid_1 bounding box.

    """
    gid_level = 'GID_1'#.format(level)
    # if level == 2:
    #     gid_1 = get_gid_1(region)
    # else:
    #     gid_1 = region

    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path = os.path.join(folder, filename)
    sites = pd.read_csv(path)#[:100]

    filename = 'regions_{}_{}.shp'.format(1, iso3)

    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path_regions = os.path.join(folder, filename)
    regions = gpd.read_file(path_regions, crs='epsg:4326')#[:1]
    region_df = regions[regions[gid_level] == region]['geometry'].values[0]

    filename = '{}.csv'.format(region)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
    if not os.path.exists(folder):
        os.makedirs(folder)
    path_out = os.path.join(folder, filename)
    if os.path.exists(path_out):
        return

    xmin, ymin, xmax, ymax = region_df.bounds

    output = []

    for idx, site in sites.iterrows():

        x, y = site['lon'], site['lat']

        if not xmin <= x <= xmax:
            continue

        if not ymin <= y <= ymax:
            continue

        output.append({
            'radio': site['radio'],
            'mcc': site['mcc'],
            'net': site['net'],
            'area': site['area'],
            'cell': site['cell'],
            'unit': site['unit'],
            'lon': site['lon'],
            'lat': site['lat'],
            'range': site['range'],
            'samples': site['samples'],
            'changeable': site['changeable'],
            'created': site['created'],
            'updated': site['updated'],
            'averageSignal': site['averageSignal']
        })

    if len(output) > 0:
        output = pd.DataFrame(output)
        output.to_csv(path_out, index=False)
    else:
        return

    return


def segment_by_gid_2(iso3, level, region, gid_1):
    """
    Segment sites by gid_2 bounding box.

    """
    gid_level = 'GID_{}'.format(level)

    filename = 'regions_{}_{}.shp'.format(level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:1]

    region_df = regions[regions[gid_level] == region]
    region_df = region_df['geometry'].values[0]

    # filename = '{}.shp'.format(region['GID_1'])
    folder_out = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_2', 'interim')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    # path = os.path.join(folder_out, filename)
    #if os.path.exists(path):
    #    return

    filename = '{}.csv'.format(region)
    path_out = os.path.join(folder_out, filename)

    if os.path.exists(path_out):
        return

    try:
        xmin, ymin, xmax, ymax = region_df.bounds
    except:
        return

    filename = '{}.csv'.format(gid_1)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        return
    sites = pd.read_csv(path)

    output = []

    for idx, site in sites.iterrows():

        x, y = site['lon'], site['lat']

        if not xmin < x < xmax:
            continue

        if not ymin < y < ymax:
            continue

        output.append({
            'radio': site['radio'],
            'mcc': site['mcc'],
            'net': site['net'],
            'area': site['area'],
            'cell': site['cell'],
            'unit': site['unit'],
            'lon': site['lon'],
            'lat': site['lat'],
            'range': site['range'],
            'samples': site['samples'],
            'changeable': site['changeable'],
            'created': site['created'],
            'updated': site['updated'],
            'averageSignal': site['averageSignal']
        })

    if len(output) > 0:

        output = pd.DataFrame(output)

        filename = '{}.csv'.format(region)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_2', 'interim')
        path_out = os.path.join(folder, filename)
        output.to_csv(path_out, index=False)

    else:
        return

    return


def create_national_sites_shp(iso3):
    """
    Create a national sites csv layer for a selected country.

    """
    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_csv = os.path.join(folder, filename)

    filename = '{}.shp'.format(iso3)
    path_shp = os.path.join(folder, filename)

    if not os.path.exists(path_shp):

        # print('-Writing site shapefile data for {}'.format(iso3))

        country_data = pd.read_csv(path_csv)#[:10]

        output = []

        for idx, row in country_data.iterrows():
            output.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [row['lon'],row['lat']]
                },
                'properties': {
                    'radio': row['radio'],
                    'mcc': row['mcc'],
                    'net': row['net'],
                    'area': row['area'],
                    'cell': row['cell'],
                }
            })

        output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

        output.to_file(path_shp)


def create_regional_sites_layer(iso3, level, region):
    """
    Create regional site layers.

    """
    project = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:4326'), # source coordinate system
        pyproj.Proj('epsg:3857')) # destination coordinate system

    gid_level = 'GID_{}'.format(level)

    filename = '{}.csv'.format(region)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
    if not os.path.exists(folder):
        os.mkdir(folder)
    path_out = os.path.join(folder, filename)

    if os.path.exists(path_out):
        return

    filename = '{}.csv'.format(region)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower(), 'interim')
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        return
    sites = pd.read_csv(path)

    filename = '{}.shp'.format(region)
    folder = os.path.join(DATA_PROCESSED, iso3, 'surface_water', 'regions')
    path_in = os.path.join(folder, filename)
    on_water = 0
    surface_water = []
    if os.path.exists(path_in):
        surface_water = gpd.read_file(path_in, crs='epsg:4326')
        surface_water = surface_water.unary_union

    output = []

    for idx, site in sites.iterrows():

        geom = Point(site['lon'], site['lat'])

        if len(surface_water) > 0:
            try:
                surface_water_results = surface_water.contains(geom)
                if surface_water_results.any():
                    on_water = 1
            except:
                on_water = 0

        geom_4326 = geom

        geom_3857 = transform(project.transform, geom_4326)

        output.append({
            'radio': site['radio'],
            'mcc': site['mcc'],
            'net': site['net'],
            'area': site['area'],
            'cell': site['cell'],
            'gid_level': gid_level,
            'gid_id': region,
            'cellid4326': '{}_{}'.format(
                round(geom_4326.coords.xy[0][0],6),
                round(geom_4326.coords.xy[1][0],6)
            ),
            'cellid3857': '{}_{}'.format(
                round(geom_3857.coords.xy[0][0],6),
                round(geom_3857.coords.xy[1][0],6)
            ),
            'on_water': on_water
        })

    if len(output) > 0:

        output = pd.DataFrame(output)
        output.to_csv(path_out, index=False)

    else:
        return

    return


def query_hazard_layers(country, region, scenarios, regional_level):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level) #regional_level

    for scenario in scenarios: #tqdm(scenarios):

        if 'model-mean' in scenario:
            continue

        print('Working on {}'.format(scenario))

        output = []

        gid_id = region #region[gid_level]
        scenario_name = os.path.basename(scenario).replace('.tif', '')

        filename = '{}_{}.csv'.format(gid_id, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'flood_scenarios')
        path_output = os.path.join(folder_out, filename)

        #if os.path.exists(path_output):
        #    continue

        filename = '{}.csv'.format(region)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
        path = os.path.join(folder, filename)

        if not os.path.exists(path):
            continue

        sites = pd.read_csv(path)#[:10]

        failures = 0

        for idx, site in sites.iterrows():

            x = float(site['cellid4326'].split('_')[0])
            y = float(site['cellid4326'].split('_')[1])

            with rasterio.open(scenario) as src:

                src.kwargs = {'nodata':255}

                coords = [(x, y)]

                depth = [sample[0] for sample in src.sample(coords)][0]

                output.append({
                    'radio': site['radio'],
                    'mcc': site['mcc'],
                    'net': site['net'],
                    'area': site['area'],
                    'cell': site['cell'],
                    'gid_level': gid_level,
                    'gid_id': region,
                    'cellid4326': site['cellid4326'],
                    'cellid3857': site['cellid3857'],
                    'depth': depth,
                })

        if len(output) == 0:
            return

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = pd.DataFrame(output)

        output.to_csv(path_output, index=False)

    return


def estimate_model_mean(country, region, scenarios, regional_level):
    """
    Estimate the model mean values.

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level) #regional_level

    model_mean_scenarios = []
    scenarios_for_averaging = []

    #get the scenario names for averaging
    for scenario in scenarios:
        if 'inunriver' in scenario: #and 'MIROC-ESM-CHEM'
            if not 'historical' in scenario:
                if not 'model-mean' in scenario:
                    scenarios_for_averaging.append(scenario)
                else:
                    model_mean_scenarios.append(scenario)
            else:
                continue

    for scenario in model_mean_scenarios: #tqdm(scenarios):

        print('Working on {}'.format(scenario))

        output = []

        gid_id = region #region[gid_level]
        basename = os.path.basename(scenario).replace('.tif', '')

        filename = '{}_{}.csv'.format(gid_id, basename)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'flood_scenarios')
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_output = os.path.join(folder_out, filename)

        #if os.path.exists(path_output):
        #    continue

        climate_scenario = basename.split('_')[1]
        year = basename.split('_')[3]
        return_period = basename.split('_')[4]

        scenario_data = {}

        for scenario_for_averaging in scenarios_for_averaging:

            basename_for_averaging = os.path.basename(scenario_for_averaging).replace('.tif', '')

            if not climate_scenario in basename_for_averaging:
                continue

            if not year in basename_for_averaging:
                continue

            if not return_period in basename_for_averaging:
                continue

            filename = '{}_{}.csv'.format(gid_id, os.path.basename(basename_for_averaging))
            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'flood_scenarios')
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                continue

            sites = pd.read_csv(path)

            for idx, site in sites.iterrows():

                key = site['cellid4326']
                value = site['depth']

                if not key in scenario_data.keys():

                    depth_dict = {
                        'radio': site['radio'],
                        'mcc': site['mcc'],
                        'net': site['net'],
                        'area': site['area'],
                        'cell': site['cell'],
                        'gid_level': site['gid_level'],
                        'gid_id': site['gid_id'],
                        'cellid4326': site['cellid4326'],
                        'cellid3857': site['cellid3857'],
                        basename_for_averaging: value
                    }
                    scenario_data[key] = depth_dict

                else:

                    for k, v in scenario_data.items():
                        if k == key:
                            depth_dict = {}
                            depth_dict[basename_for_averaging] = value
                            v.update(depth_dict)
                            scenario_data[key] = v

        for key, my_dict in scenario_data.items():

            depth_dict = {key: value for (key, value) in my_dict.items() if 'inunriver' in key}

            output.append({
                'radio': my_dict['radio'],
                'mcc': my_dict['mcc'],
                'net': my_dict['net'],
                'area': my_dict['area'],
                'cell': my_dict['cell'],
                'gid_level': my_dict['gid_level'],
                'gid_id': my_dict['gid_id'],
                'cellid4326': my_dict['cellid4326'],
                'cellid3857': my_dict['cellid3857'],
                'depth': sum(depth_dict.values()) / len(depth_dict),
            })

        if len(output) == 0:
            return
        output = pd.DataFrame(output)
        output.to_csv(path_output, index=False)

    return


def estimate_results(country, region, scenarios, regional_level):
    """

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level)

    filename = 'fragility_curve.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    low, baseline, high = load_f_curves(path_fragility)

    for scenario in scenarios: #tqdm

        output = []

        gid_id = region#[gid_level]
        scenario_name = os.path.basename(scenario)[:-4]
        print(scenario_name)
        # if not gid_id == 'EGY.1_1':
        #     continue

        filename = '{}_{}.csv'.format(gid_id, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario_name)
        path_output = os.path.join(folder_out, filename)

        #if os.path.exists(path_output):
            #print('path_output exists {}'.format(path_output))
        #    continue

        filename = '{}_{}.csv'.format(gid_id, scenario_name)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'flood_scenarios')
        path_in = os.path.join(folder, filename)
        if not os.path.exists(path_in):
            # print('path_in does not exist {}'.format(path_in))
            continue
        sites = pd.read_csv(path_in)

        for idx, site in sites.iterrows():

            if not site['depth'] > 0:
                continue

            damage_low = query_fragility_curve(low, site['depth'])
            damage_baseline = query_fragility_curve(baseline, site['depth'])
            damage_high = query_fragility_curve(high, site['depth'])
            
            output.append({
                'radio': site['radio'],
                'mcc': site['mcc'],
                'net': site['net'],
                'area': site['area'],
                'cell': site['cell'],
                'gid_level': gid_level,
                'gid_id': region,
                'cellid4326': site['cellid4326'],
                'cellid3857': site['cellid3857'],
                'depth': site['depth'],
                'damage_low': damage_low,
                'damage_baseline': damage_baseline,
                'damage_high': damage_high,
                'cost_usd_low': round(40000 * damage_low),
                'cost_usd_baseline': round(40000 * damage_baseline),
                'cost_usd_high': round(40000 * damage_high),
            })

        if len(output) == 0:
            #print('len(output) == 0')
            continue

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = pd.DataFrame(output)
        output.to_csv(path_output, index=False)

    return


def load_f_curves(path_fragility):
    """
    Load depth-damage curves.

    """
    low = []
    baseline = []
    high = []

    f_curves = pd.read_csv(path_fragility)

    for idx, item in f_curves.iterrows():

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


def convert_to_regional_results(country, region, scenarios):
    """
    Collect all results.

    """
    scenarios = get_scenarios()[::-1]

    iso3 = region[:3]

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated', 'regions')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    for scenario in scenarios:

        output = []

        scenario_name = os.path.basename(scenario)[:-4]
        filename = '{}_{}.csv'.format(region, scenario_name)
        path_out = os.path.join(folder_out, filename)

        filename = '{}_{}.csv'.format(region, scenario_name)
        folder_in = os.path.join(DATA_PROCESSED, iso3, 'results',
            'regional_data', scenario_name)
        path_in = os.path.join(folder_in, filename)

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

        data = pd.read_csv(path_in, sep=',')

        if len(data) == 0:
            continue

        gid_ids = list(data['gid_id'].unique())
        # radios = list(data['radio'].unique())
        # networks = list(data['net'].unique())

        for gid_id in gid_ids:

            #for network in networks:

            cell_count_low = 0
            cell_count_baseline = 0
            cell_count_high = 0
            cost_usd_low = 0
            cost_usd_baseline = 0
            cost_usd_high = 0

            for idx, item in data.iterrows():

                if not item['gid_id'] == gid_id:
                    continue

                if item['cost_usd_low'] > 0:
                    cell_count_low += 1
                    cost_usd_low += item['cost_usd_low']

                if item['cost_usd_baseline'] > 0:
                    cell_count_baseline += 1
                    cost_usd_baseline += item['cost_usd_baseline']

                if item['cost_usd_high'] > 0:
                    cell_count_high += 1
                    cost_usd_high += item['cost_usd_high']

            output.append({
                'iso3': country['iso3'],
                'iso2': country['iso2'],
                'country': country['country'],
                'continent': country['continent'],
                'gid_level': item['gid_level'],
                'gid_id': gid_id,
                'cell_count_low': cell_count_low,
                'cost_usd_low': cost_usd_low,
                'cell_count_baseline': cell_count_baseline,
                'cost_usd_baseline': cost_usd_baseline,
                'cell_count_high': cell_count_high,
                'cost_usd_high': cost_usd_high,
                })

        if len(output) == 0:
            continue

        output = pd.DataFrame(output)

        output.to_csv(path_out, index=False)

    return


def collect_final_results(collection_type):
    """
    Collect all results.

    """
    scenarios = get_scenarios()[::-1]
    countries = get_countries()

    folder_out = os.path.join(DATA_PROCESSED, 'results')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    for scenario in scenarios:

        output = []

        scenario_name = os.path.basename(scenario)[:-4]

        path_out = os.path.join(folder_out, scenario_name + '.csv')

        for idx, country in countries.iterrows():

            if not collection_type == 'all':
                if not country['iso3'] == collection_type:
                    continue

            collect_national_results(country['iso3'], scenario)

            path = os.path.join(DATA_PROCESSED, country['iso3'], 'results',
                'national_data', scenario_name + '.csv')

            if not os.path.exists(path):
                output.append({
                        'iso3': country['iso3'],
                        'iso2': country['iso2'],
                        'country': country['country'],
                        'continent': country['continent'],
                        'radio': 'NA',
                        'network': 'NA',
                        'cell_count': 0,
                        'cost_usd': 0,
                    })
                continue

            # print(path)
            data = pd.read_csv(path, sep=',')
            # print(data.columns)
            if len(data) == 0:
                continue

            radios = list(data['radio'].unique())
            networks = list(data['net'].unique())

            for radio in radios:

                #for network in networks:

                cell_count = 0
                cost_usd = 0

                for idx, item in data.iterrows():

                    if not item['radio'] == radio:
                        continue

                #        if not item['net'] == network:
                #            continue

                    if not item['failure'] == 1:
                        continue
                    # print(cell_count)
                    cell_count += 1
                    cost_usd += item['cost_usd']

                output.append({
                    'iso3': country['iso3'],
                    'iso2': country['iso2'],
                    'country': country['country'],
                    'continent': country['continent'],
                    'radio': radio,
                    #'network': network,
                    'cell_count': cell_count,
                    'cost_usd': cost_usd,
                    })

        if len(output) == 0:
            # print('output len = 0')
            continue

        output = pd.DataFrame(output)

        output.to_csv(path_out, index=False)

    return


def collect_national_results(iso3, scenario):
    """
    Collect regional results and write to national results folder.

    """
    output = []

    scenario_name = os.path.basename(scenario)[:-4]
    #print('collecting national results for {}'.format(scenario_name))
    folder = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario_name)

    if not os.path.exists(folder):
        #print('collect_national_results: folder does not exist: {}'.format(folder))
        return

    all_regional_results = os.listdir(folder)

    if len(all_regional_results) == 0:
        #print('len of all_regional_results = 0')
        return

    for filename in all_regional_results:

        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            continue
        try:
            data = pd.read_csv(path_in)
            data = data.to_dict('records')
            output = output + data
        except:
            print('failed on {})'.format(path_in))

    if len(output) == 0:
        #print('2. len of output = 0')
        return

    output = pd.DataFrame(output)

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'national_data')
    if not os.path.exists(folder_out):
        print('folder out did not exist')
        os.mkdir(folder_out)
    path_out = os.path.join(folder_out, scenario_name + '.csv')
    output.to_csv(path_out, index=False)

    return


def collect_regional_results(collection_type):
    """
    Collect all results.

    """
    scenarios = get_scenarios()[::-1]
    countries = get_countries()

    folder_out = os.path.join(DATA_PROCESSED, 'results', 'regional')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    for scenario in scenarios:

        if not 'rcp4p5' in scenario and '2030' in scenario:
            continue

        output = []

        scenario_name = os.path.basename(scenario)[:-4]
        #print(scenario_name)
        path_out = os.path.join(folder_out, scenario_name + '.csv')

        for idx, country in countries.iterrows():

            if not collection_type == 'all':
                if not country['iso3'] == collection_type:
                    continue

            collect_country_regional_results(country['iso3'], scenario)

            scenario_name = os.path.basename(scenario)[:-4]
            #print('collecting national results for {}'.format(scenario_name))
            folder = os.path.join(DATA_PROCESSED, country['iso3'],
                'results', 'regional_aggregated', 'regions')

            if not os.path.exists(folder):
                #print('collect_national_results: folder does not exist: {}'.format(folder))
                return

            all_regional_results = os.listdir(folder)

            if len(all_regional_results) == 0:
                #print('len of all_regional_results = 0')
                return

            for filename in all_regional_results:

                path_in = os.path.join(folder, filename)
                # print(filename)
                if not os.path.exists(path_in):
                    continue
                try:
                    data = pd.read_csv(path_in)
                    data = data.to_dict('records')
                    output = output + data
                except:
                    print('failed on {})'.format(path_in))

        if len(output) == 0:
            #print('2. len of output = 0')
            return

        output = pd.DataFrame(output)

        output.to_csv(path_out, index=False)

    return


def collect_country_regional_results(iso3, scenario):
    """
    Collect regional results and write to national results folder.

    """
    output = []

    scenario_name = os.path.basename(scenario)[:-4]
    #print('collecting national results for {}'.format(scenario_name))
    folder = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated', 'regions')

    if not os.path.exists(folder):
        #print('collect_national_results: folder does not exist: {}'.format(folder))
        return

    all_regional_results = os.listdir(folder)

    if len(all_regional_results) == 0:
        #print('len of all_regional_results = 0')
        return

    for filename in all_regional_results:

        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            continue
        try:
            data = pd.read_csv(path_in)
            data = data.to_dict('records')
            output = output + data
        except:
            print('failed on {})'.format(path_in))

    if len(output) == 0:
        #print('2. len of output = 0')
        return

    output = pd.DataFrame(output)

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated')
    if not os.path.exists(folder_out):
        print('folder out did not exist')
        os.mkdir(folder_out)
    path_out = os.path.join(folder_out, scenario_name + '.csv')
    output.to_csv(path_out, index=False)

    return


if __name__ == "__main__":

    args = sys.argv

    region = args[1]

    if not region == 'collect':

        run_site_processing(region)
