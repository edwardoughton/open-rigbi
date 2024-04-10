"""
Collect Cost Data.

Written by Ed Oughton.

March 2022.

"""
import os
import sys
import configparser
# import json
# import csv
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
# import contextily as ctx
# import openpyxl
# import xlwings as xw
from shapely.geometry import MultiPolygon

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
# DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED = os.path.join(BASE_PATH, '..', 'vis', 'processed')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')

sys.path.insert(1, os.path.join(BASE_PATH, '..','scripts'))
from misc import get_countries, get_regions


def get_country_outlines(countries):
    """
    Get country shapes.

    """
    path = os.path.join(VIS, '..', 'data', 'simplified_outputs.shp')
    
    if os.path.exists(path):

        countries = gpd.read_file(path, crs='epsg:4326')

        return countries

    else:

        iso3_codes = []

        for item in countries:
            iso3_codes.append(item['iso3'])

        path_in = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
        country_shapes = gpd.read_file(path_in, crs='epsg:4326')

        countries = country_shapes[country_shapes['GID_0'].isin(iso3_codes)]

        countries['geometry'] = countries.apply(remove_small_shapes,axis=1)

        countries['geometry'] = countries['geometry'].simplify(
            tolerance = 0.005,
            preserve_topology=True
        )

        countries.to_file(path, crs='epsg:4326')

    return countries


def remove_small_shapes(x):
    """
    Remove small multipolygon shapes.

    Parameters
    ---------
    x : polygon
        Feature to simplify.

    Returns
    -------
    MultiPolygon : MultiPolygon
        Shapely MultiPolygon geometry without tiny shapes.

    """
    # if its a single polygon, just return the polygon geometry
    if x.geometry.geom_type == 'Polygon':
        return x.geometry

    # if its a multipolygon, we start trying to simplify
    # and remove shapes if its too big.
    elif x.geometry.geom_type == 'MultiPolygon':

        area1 = 0.01
        area2 = 50

        # dont remove shapes if total area is already very small
        if x.geometry.area < area1:
            return x.geometry
        # remove bigger shapes if country is really big

        if x['GID_0'] in ['CHL','IDN']:
            threshold = 0.01
        elif x['GID_0'] in ['RUS','GRL','CAN','USA']:
            threshold = 0.01

        elif x.geometry.area > area2:
            threshold = 0.1
        else:
            threshold = 0.001

        # save remaining polygons as new multipolygon for
        # the specific country
        new_geom = []
        for y in x.geometry:
            if y.area > threshold:
                new_geom.append(y)

        return MultiPolygon(new_geom)


def collect_results(countries):
    """
    Collect results.

    """
    filename = 'inuncoast_rcp85_95_conf_perc.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data')
    path_out = os.path.join(folder_out, filename)

    # if os.path.exists(path_out):
    #     output = pd.read_csv(path_out)
    #     # output = output.to_dict('records')
    #     return output

    filename = 'inuncoast_rcp85_regions.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)
    path = os.path.join(folder_out, filename)

    if not os.path.exists(path):

        folder_in = os.path.join(VIS, '..', 'regional_results_coastal_flooding_final')

        all_data = []

        for filename in os.listdir(folder_in):

            if not 'inuncoast_rcp8p5_wtsub' in filename:
                continue

            if not '2080_rp1000_0_unique.csv' in filename:
                continue

            data = pd.read_csv(os.path.join(folder_in, filename))
            data['gid_id'].replace('', np.nan, inplace=True)
            data.dropna(subset=['gid_id'], inplace=True)
            data = data.to_dict('records')
            all_data = all_data + data

        all_data = pd.DataFrame(all_data)
        all_data.to_csv(path, index=False)

    else:

        all_data = pd.read_csv(path)#[:10]

    return all_data


def get_regional_shapes(countries):
    """
    Load regional shapes.

    """
    folder = os.path.join(VIS, '..', 'data')
    if not os.path.exists(folder):
        os.makedirs(folder)
    path = os.path.join(folder, 'regions.shp')

    if os.path.exists(path):
        output = gpd.read_file(path)
        # output = output[output['GID_id'].str.startswith('AFG')]
        return output
    else:

        output = []

        for country in countries:#[:10]:

            # if not country['iso3'] == 'AFG':
            #     continue

            iso3 = country['iso3']
            gid_region = country['gid_region']
            gid_level = 'GID_{}'.format(gid_region)

            filename = 'gadm36_{}.shp'.format(gid_region)
            folder = os.path.join(DATA_RAW, 'gadm36_levels_shp')
            path_in = os.path.join(folder, filename)
            shapes = gpd.read_file(path_in, crs='epsg:4326')

            country_shapes = shapes[shapes['GID_0'] == iso3]
            country_shapes['GID_id'] = country_shapes[gid_level]
            country_shapes = country_shapes.to_dict('records')

            for item in country_shapes:
                output.append({
                    'geometry': item['geometry'],
                    'properties': {
                        'GID_id': item['GID_id'],
                        # 'area_km2': datum['area_km2']
                    },
                })

        output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

        output.to_file(path, crs='epsg:4326')

        return output


def combine_data(results, regions):
    """

    """
    regions['iso3'] = regions['GID_id'].str[:3]
    regions['gid_id'] = regions['GID_id']
    regions = regions[['gid_id', 'iso3', 'geometry']] #[:1000]
    regions = regions.copy()

    regions = regions.merge(results, how='left', left_on='gid_id', right_on='gid_id')
    regions.reset_index(drop=True, inplace=True)

    # regions['gid_region'] == 'AUS.5.130_1' = 0
    regions['cost_usd_baseline'][regions['gid_id'] == 'AUS.5.130_1'] = 0
    # df['FirstName'][df.ID == 103] = "Matt"
    regions.to_file(os.path.join(VIS,'..','data','country_data_coast.shp'))

    return regions


def plot_regional_results(regions, path, countries):
    """
    Plot regions by geotype.

    """
    metric = 'cost'

    regions['cost'] = regions['cost_usd_b'].fillna(0)
    # regions.to_file(os.path.join(VIS,'..','data','test4.shp'))
    regions['cost'] = round(regions['cost'] / 1e6,0) #_b short for baseline, not billions

    bins = [-10,.2,.3,.4,.5,.6,.7,.8,.9,1,1e12]
    labels = ['$<0.2m','$.3m','$.4m','$.5m','$.6m','$.7m','$.8m','$.9m','$1m','>$1m']

    regions['bin'] = pd.cut(
        regions[metric],
        bins=bins,
        labels=labels
    )

    sns.set(font_scale=0.9)
    fig, ax = plt.subplots(1, 1, figsize=(10, 4.5))

    minx, miny, maxx, maxy = regions.total_bounds
    ax.set_xlim(-170, 190)
    ax.set_ylim(miny-5, maxy)

    base = regions.plot(column='bin', ax=ax, cmap='viridis', linewidth=0, #inferno_r
        legend=True, antialiased=False)
    countries.plot(ax=base, facecolor="none", edgecolor='grey', linewidth=0.15)

    handles, labels = ax.get_legend_handles_labels()

    fig.legend(handles[::-1], labels[::-1])

    n = len(regions)
    name = 'Direct Damage Cost From Coastal Flooding (2080, RCP8.5, 1-in-1000, 95% CI) (n={})'.format(n)
    fig.suptitle(name)

    fig.tight_layout()
    fig.savefig(path)

    plt.close(fig)


if __name__ == "__main__":

    countries = get_countries()#[:2]

    print('get_country_outlines')
    countries_shps = get_country_outlines(countries)

    print('collect_results')
    results = collect_results(countries)#[:300]

    print('get_regional_shapes...')
    regions = get_regional_shapes(countries)#[:1000]

    print('combine_data...')
    regions = combine_data(results, regions)

    path_in_shp = os.path.join(VIS,'..','data','country_data_coast.shp')
    regions = gpd.read_file(path_in_shp, crs='epsg:4326')#[:1000]

    path_in = os.path.join(VIS, 'regions_by_cost_coast.png')
    print('plot_regional_results...')
    plot_regional_results(regions, path_in, countries_shps)
