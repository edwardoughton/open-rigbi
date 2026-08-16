import os
import sys
import configparser
import numpy as np 
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.colors as mcolors
import seaborn as sns
from shapely.geometry import MultiPolygon

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, '..', 'vis', 'processed')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures_final_nat_comms')

FORCED_NA_ISO3 = {'GRL', 'ISL', 'ESH'}

sys.path.insert(1, os.path.join(BASE_PATH, '..','scripts'))
from misc import get_countries

def get_country_outlines():
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
    """
    Collect results.

    """
    filename = 'inuncoast_rcp85_95_conf_perc.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data_new')
    path = os.path.join(folder_out, filename)

    if os.path.exists(path):
        output = pd.read_csv(path)
        # output = output.to_dict('records')
        return output

    filename = 'inuncoast_rcp85_regions.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data_new')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)
    path = os.path.join(folder_out, filename)

    if not os.path.exists(path):

        folder_in = os.path.join(BASE_PATH, 'processed', 'results_new', 'regional')

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


def get_regional_shapes():
    path = os.path.join(VIS, '..', 'data', 'regions.shp')
    if os.path.exists(path):
        return gpd.read_file(path)
    return gpd.GeoDataFrame()


def combine_data(results, regions):
    regions['area_km2'] = regions.geometry.to_crs(epsg=6933).area / 1e6
    results['GID_id'] = results['gid_id']
    regions = regions.merge(results, how='left', on='GID_id')
    country_iso3 = regions['GID_id'].str.split('.', n=1).str[0]
    regions.loc[country_iso3.isin(FORCED_NA_ISO3), 'cost_usd_baseline'] = pd.NA
    regions['cost_per_km2'] = regions['cost_usd_baseline'] / regions['area_km2']
    return regions


def plot_combined_results(regions, countries):
    plt.rcParams['font.family'] = 'Arial'  
    fig, axes = plt.subplots(2, 1, figsize=(10,8))
    
    metrics = {'cost_per_km2': '(A)', 'cost_usd_baseline_m': '(B)'}
    regions['cost_usd_baseline_m'] = regions['cost_usd_baseline'] / 1e6

    bins = {
        'cost_per_km2': [0, 1, 5, 10, 25, 50, 75, 100, 150, 1e12],
        'cost_usd_baseline_m': [0, 1, 2, 3, 4, 5, 6, 7, 8, 1e12]
    }

    legend_labels = {
        'cost_per_km2': ['<$1/km²','$5/km²', '$10/km²', '$25/km²', '$50/km²', '$75/km²', '$100/km²', '$150/km²', '>$150/km²'],
        'cost_usd_baseline_m': ['$<1m', '$2m', '$3m', '$4m', '$5m', '$6m', '$7m', '$8m','>$8m']
    }

    missing_color = '#c9c9c9'

    for ax, (metric, title) in zip(axes, metrics.items()):

        # Missing and non-positive results share the N/A category. Drawing the
        # complete country layer first also covers countries without regional
        # result polygons, which would otherwise remain white.
        na_mask = regions[metric].isna() | regions[metric].le(0)

        # **Step 2: Bin values while ignoring "N/A"**
        regions['bin'] = pd.cut(
            regions[metric].where(~na_mask),
            bins=bins[metric], 
            labels=legend_labels[metric],  
            include_lowest=True
        )

        # **Step 3: Reverse order of legend labels**
        ordered_labels = list(reversed(legend_labels[metric]))  # Reverse the order
        ordered_labels.append('N/A')

        # **Step 4: Convert 'bin' column to categorical with reversed order**
        regions['bin'] = regions['bin'].astype(pd.CategoricalDtype(categories=ordered_labels, ordered=True))

        # Assign missing and no-damage results to the same grey category.
        regions.loc[na_mask, 'bin'] = 'N/A'

        # **Step 6: Create a colormap with 'N/A' explicitly assigned to grey**
        viridis_colors = plt.get_cmap('viridis', len(legend_labels[metric]))
        custom_colors = {
            'N/A': missing_color,
        }
        
        # Assign viridis colors in reversed order
        for i, label in enumerate(ordered_labels[:-1]):
            custom_colors[label] = viridis_colors(i / (len(legend_labels[metric]) - 1))

        # **Step 7: Create colormap, ensuring 'N/A' is explicitly assigned**
        cmap = mcolors.ListedColormap([custom_colors[label] for label in ordered_labels])

        # Paint every country grey before overlaying valid positive results.
        countries.plot(ax=ax, color=missing_color, linewidth=0, rasterized=True)

        # **Step 8: Plot "N/A" regions separately in light gray FIRST**
        regions[na_mask].plot(ax=ax, color=missing_color, linewidth=0, rasterized=True)

        # **Step 9: Plot main regions (without "N/A" regions)**
        base = regions[~na_mask].plot(column='bin', ax=ax, cmap=cmap, linewidth=0, legend=True,
                                      categorical=True, rasterized=True, 
                                      legend_kwds={
                                          'bbox_to_anchor': (1, 1),
                                          'loc': 'upper right',
                                          'borderaxespad': .5,
                                          'labelspacing': .7,
                                          'fontsize': 9,
                                      })

        # These countries have no modeled regional results and must remain N/A.
        countries[countries['GID_0'].isin(FORCED_NA_ISO3)].plot(
            ax=base, color=missing_color, linewidth=0, rasterized=True
        )

        # **Step 10: Overlay country borders**
        countries.plot(ax=base, facecolor="none", edgecolor='grey', linewidth=0.1)
        
        ax.set_title(title, loc='left', fontsize=14)
        minx, miny, maxx, maxy = regions.total_bounds
        ax.set_xlim(-170, 215)
        ax.set_ylim(miny-5, maxy)

    plt.tight_layout()
    output_filenames = [
        'combined_coastal_costs.pdf',
        'Figure 2 Global distribution of coastal flooding impacts on mobile cellular infrastructure under a high-emissions climate scenario.pdf',
    ]
    for filename in output_filenames:
        plt.savefig(os.path.join(VIS, filename), format="pdf", dpi=600)
    plt.close()


if __name__ == "__main__":
    countries_shps = get_country_outlines()
    results = collect_results()
    regions = get_regional_shapes()
    regions = combine_data(results, regions)
    plot_combined_results(regions, countries_shps)
