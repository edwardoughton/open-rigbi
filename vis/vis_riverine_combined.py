import os
import sys
import configparser
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
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures_new')

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

# def collect_results():
#     """ Load or process flood damage results. """
#     path = os.path.join(BASE_PATH, '..', 'vis', 'data', 'inunriver_rcp85_mean_results.csv')
#     if os.path.exists(path):
#         return pd.read_csv(path)
#     return pd.DataFrame()

def collect_results(countries):
    """
    Collect results.

    """
    filename = 'inunriver_rcp85_mean_results.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data_new')
    path_out = os.path.join(folder_out, filename)

    if os.path.exists(path_out):
        output = pd.read_csv(path_out)
        # output = output.to_dict('records')
        return output

    filename = 'inunriver_rcp85_regions.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data_new')
    path_in = os.path.join(folder_out, filename)

    if not os.path.exists(path_in):

        folder_in = os.path.join(BASE_PATH, 'processed', 'results_new', 'regional')

        all_data = []

        for filename in os.listdir(folder_in):

            if not 'inunriver_rcp8p5' in filename:
                continue

            if not '2080_rp01000' in filename:
                continue

            data = pd.read_csv(os.path.join(folder_in, filename))
            data = data.to_dict('records')
            all_data = all_data + data

        all_data = pd.DataFrame(all_data)
        all_data.to_csv(path_in)

    else:

        all_data = pd.read_csv(path_in)#[:10]

    for country in countries:

        interim = []

        country_data = all_data[all_data['iso3'] == country['iso3']]

        gid_ids = country_data['gid_id'].unique()

        for gid_id in gid_ids:

            cell_count_baseline = []
            cost_usd_baseline = []

            for idx, row in country_data.iterrows():
                if row['gid_id'] == gid_id:
                    cell_count_baseline.append(row['cell_count_baseline'])
                    cost_usd_baseline.append(row['cost_usd_baseline'])

            items = country_data[country_data['gid_id'] == gid_id][:1]
            
            if len(items) == 0:
                continue

            if len(cell_count_baseline) == 0:
                cell_count_baseline = 0
            else:
                cell_count_baseline = sum(cell_count_baseline) / len(cell_count_baseline)

            if len(cost_usd_baseline) == 0:
                cost_usd_baseline = 0
            else:
                cost_usd_baseline = sum(cost_usd_baseline) / len(cost_usd_baseline)

            interim.append({
                # 'iso3': items['iso3'].values[0],
                # 'iso2': items['iso2'].values[0],
                # 'country': items['country'].values[0],
                # 'continent': items['continent'].values[0],
                # 'gid_level': items['gid_level'].values[0],
                'gid_id': items['gid_id'].values[0],
                'mean_cell_count_baseline': cell_count_baseline,
                'cost_usd_baseline': cost_usd_baseline,
            })

        interim = pd.DataFrame(interim)
        filename = 'inunriver_rcp85_mean_results.csv'
        folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data_new', 'countries', country['iso3'])
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_out = os.path.join(folder_out, filename)
        interim = interim.to_csv(path_out, index=False)

    output = []

    for country in countries:

        print('Working on {}'.format(country['iso3']))

        filename = 'inunriver_rcp85_mean_results.csv'
        folder_in = os.path.join(BASE_PATH, '..', 'vis', 'data_new', 'countries', country['iso3'])
        path_in = os.path.join(folder_in, filename)
        if not os.path.exists(path_in):
            continue
        try:
            data = pd.read_csv(path_in)
        except:
            continue
        data = data.to_dict('records')
        output = output + data

    filename = 'inunriver_rcp85_mean_results.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data_new')
    path_out = os.path.join(folder_out, filename)

    output = pd.DataFrame(output)
    output = output.sort_values(by='gid_id')
    output.to_csv(path_out, index=False)

    return output


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
    matplotlib.rcParams['font.family'] = 'Times New Roman'
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    metrics = {'cost_per_km2': '(A)', 'cost_usd_baseline_m': '(B)'}
    regions['cost_usd_baseline_m'] = regions['cost_usd_baseline'] / 1e6

    bins = {
        'cost_per_km2': [-10, 1, 5, 10, 50, 100, 500, 1000, 5000, 1e12],
        'cost_usd_baseline_m': [-10,2,3,4,5,6,7,8,9,1e12]
    }

    legend_labels = {
        'cost_per_km2': ['$<1/km²','$5/km²','$10/km²','$50/km²','$100/km²','$500/km²','$1k/km²','$5k/km²','>$5k/km²'],#[::-1],
        'cost_usd_baseline_m': ['$<2m','$3m','$4m','$5m','$6m','$7m','$8m','$9m','>$9m']#[::-1]
    }

    zero_color = 'lightgrey'  # Color for 'N/A'

    for ax, (metric, title) in zip(axes, metrics.items()):
        
        print(metric, bins[metric], legend_labels[metric])
        
        # **Step 1: Create an explicit mask for "N/A" areas**
        na_mask = regions[metric] == 0

        # **Step 2: Bin values while ignoring "N/A"**
        regions['bin'] = pd.cut(
            regions[metric].where(~na_mask),  # Ignore 0 values for binning
            bins=bins[metric], 
            labels=legend_labels[metric],  
            include_lowest=True
        )

        # **Step 3: Reverse order of legend labels**
        ordered_labels = list(reversed(legend_labels[metric]))  # Reverse the order
        ordered_labels.append('N/A')  # Add 'N/A' at the bottom

        # **Step 4: Convert 'bin' column to categorical with reversed order**
        regions['bin'] = regions['bin'].astype(pd.CategoricalDtype(categories=ordered_labels, ordered=True))

        # **Step 5: Explicitly assign 'N/A' to zero values**
        regions.loc[na_mask, 'bin'] = 'N/A'

        # **Step 6: Create a colormap with 'N/A' explicitly assigned to grey**
        viridis_colors = plt.get_cmap('viridis', len(ordered_labels) - 1)  
        custom_colors = {'N/A': zero_color}  # Start with explicit grey for 'N/A'
        
        # Assign viridis colors in reversed order
        for i, label in enumerate(ordered_labels[:-1]):  # Exclude 'N/A' from viridis mapping
            custom_colors[label] = viridis_colors(i / (len(ordered_labels) - 2))

        # **Step 7: Create colormap, ensuring 'N/A' is explicitly assigned**
        cmap = mcolors.ListedColormap([custom_colors[label] for label in ordered_labels])

        # Normalize color mapping
        norm = mcolors.BoundaryNorm(range(len(ordered_labels) + 1), cmap.N)

        # **Step 8: Plot "N/A" regions separately in light gray FIRST**
        regions[na_mask].plot(ax=ax, color=zero_color, linewidth=0)

        # **Step 9: Plot main regions (without "N/A" regions)**
        base = regions[~na_mask].plot(column='bin', ax=ax, cmap=cmap, linewidth=0, legend=True,
                                      categorical=True, legend_kwds={'bbox_to_anchor': (1, 1), 'labelspacing': .95})

        # **Step 10: Overlay country borders**
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
    countries = get_countries()#[:2]
    countries_shps = get_country_outlines()
    results = collect_results(countries)
    regions = get_regional_shapes()
    regions = combine_data(results, regions)
    plot_combined_results(regions, countries_shps)