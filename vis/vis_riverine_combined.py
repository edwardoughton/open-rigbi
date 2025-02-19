import os
import sys
import configparser
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import MultiPolygon

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, '..', 'vis', 'processed')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')

sys.path.insert(1, os.path.join(BASE_PATH, '..','scripts'))
from misc import get_countries

def get_country_outlines():
    """ Load or generate country outlines. """
    path = os.path.join(VIS, '..', 'data', 'simplified_outputs.shp')
    if os.path.exists(path):
        return gpd.read_file(path, crs='epsg:4326')
    else:
        path_in = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
        countries = gpd.read_file(path_in, crs='epsg:4326')
        countries['geometry'] = countries['geometry'].simplify(0.005, preserve_topology=True)
        countries.to_file(path)
        return countries

def collect_results():
    """ Load or process flood damage results. """
    path = os.path.join(BASE_PATH, '..', 'vis', 'data', 'inunriver_rcp85_mean_results.csv')
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def get_regional_shapes():
    """ Load regional shapefiles. """
    path = os.path.join(VIS, '..', 'data', 'regions.shp')
    if os.path.exists(path):
        return gpd.read_file(path)
    return gpd.GeoDataFrame()

def combine_data(results, regions):
    """ Merge cost data with regions and compute cost per km². """
    regions['area_km2'] = regions.geometry.to_crs(epsg=6933).area / 1e6
    results['GID_id'] = results['gid_id']
    regions = regions.merge(results, how='left', on='GID_id')
    regions['cost_per_km2'] = regions['cost_usd_baseline'] / regions['area_km2']
    regions['cost_usd_baseline'].fillna(0, inplace=True)
    regions['cost_per_km2'].fillna(0, inplace=True)
    return regions

def plot_combined_results(regions, countries):
    """ Generate a combined panel plot. """
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    metrics = {'cost_per_km2': '(A)', 'cost_usd_baseline_m': '(B)'}
    regions['cost_usd_baseline_m'] = regions['cost_usd_baseline'] / 1e6

    bins = {
        'cost_per_km2': [-10, 1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 1e12],
        'cost_usd_baseline_m': [-10,2,3,4,5,6,7,8,9,10,1e12]
    }

    legend_labels = {
        'cost_per_km2': ['$<1k/km²','$5k/km²','$10k/km²','$50k/km²','$100k/km²','$500k/km²','$1M/km²','$5M/km²','$10M/km²','>$10M/km²'][::-1],
        'cost_usd_baseline_m': ['$<2m','$3m','$4m','$5m','$6m','$7m','$8m','$9m','$10m','>$10m'][::-1]
    }

    for ax, (metric, title) in zip(axes, metrics.items()):
        regions['bin'] = pd.cut(
            regions[metric],
            bins=bins[metric],
            labels=legend_labels[metric]
        )
        base = regions.plot(column='bin', ax=ax, cmap='viridis', linewidth=0, legend=True)
        countries.plot(ax=base, facecolor="none", edgecolor='grey', linewidth=0.1)
        ax.set_title(title, loc='left', fontsize=14)
        minx, miny, maxx, maxy = regions.total_bounds
        ax.set_xlim(-170, 215)
        ax.set_ylim(miny-5, maxy)
    
    # fig.suptitle('Flood Damage Costs: Cost per km² & Total Cost')
    plt.tight_layout()
    plt.savefig(os.path.join(VIS, 'combined_flood_costs.png'), dpi=300)
    plt.close()



if __name__ == "__main__":
    countries_shps = get_country_outlines()
    results = collect_results()
    regions = get_regional_shapes()
    regions = combine_data(results, regions)
    plot_combined_results(regions, countries_shps)