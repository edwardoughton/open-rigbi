"""
Collect Cost Data.

Written by Ed Oughton.

March 2022.

"""
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
from misc import get_countries, get_regions


def get_country_outlines():
    """
    Get country shapes.

    """
    path = os.path.join(VIS, '..', 'data', 'simplified_outputs.shp')

    if os.path.exists(path):

        countries = gpd.read_file(path, crs='epsg:4326')

        return countries

    else:
        folder = os.path.join(VIS, '..', 'data')
        if not os.path.exists(folder):
            os.makedirs(folder)

        # iso3_codes = []

        # for item in countries:
        #     iso3_codes.append(item['iso3'])

        path_in = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
        countries = gpd.read_file(path_in, crs='epsg:4326')

        # countries = country_shapes[country_shapes['GID_0'].isin(iso3_codes)]

        countries['geometry'] = countries.apply(remove_small_shapes,axis=1)

        countries['geometry'] = countries['geometry'].simplify(
            tolerance = 0.005,
            preserve_topology=True
        )

        countries.to_file(path) #, crs='epsg:4326'

    return countries


def remove_small_shapes(x):
    """
    Remove small multipolygon shapes.

    Parameters
    ----------
    x : GeoSeries row
        Feature to simplify.

    Returns
    -------
    MultiPolygon or Polygon
        Simplified geometry without small parts.
    """

    # If it's a single Polygon, return it as is
    if x.geometry.geom_type == 'Polygon':
        return x.geometry

    # If it's a MultiPolygon, filter out small polygons
    elif x.geometry.geom_type == 'MultiPolygon':

        area1 = 0.01  # Small area threshold
        area2 = 50    # Large area threshold

        # Don't remove shapes if the total area is already very small
        if x.geometry.area < area1:
            return x.geometry

        # Set area threshold based on country size
        if x['GID_0'] in ['CHL', 'IDN']:
            threshold = 0.01
        elif x['GID_0'] in ['RUS', 'GRL', 'CAN', 'USA']:
            threshold = 0.01
        elif x.geometry.area > area2:
            threshold = 0.1
        else:
            threshold = 0.001

        # Extract individual polygons from the MultiPolygon
        new_geom = [poly for poly in x.geometry.geoms if poly.area > threshold]

        # If all polygons are filtered out, return the original geometry
        if len(new_geom) == 0:
            return x.geometry

        return MultiPolygon(new_geom) if len(new_geom) > 1 else new_geom[0]


def collect_results(countries):
    """
    Collect results.

    """
    filename = 'inunriver_rcp85_mean_results.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data')
    path_out = os.path.join(folder_out, filename)

    if os.path.exists(path_out):
        output = pd.read_csv(path_out)
        # output = output.to_dict('records')
        return output

    filename = 'inunriver_rcp85_regions.csv'
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data')
    path = os.path.join(folder_out, filename)

    if not os.path.exists(path):

        folder_in = os.path.join(BASE_PATH, 'processed', 'results', 'regional')

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
        all_data.to_csv(path)

    else:

        all_data = pd.read_csv(path)#[:10]

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
                'gid_id': items['gid_id'].values[0],
                'mean_cell_count_baseline': cell_count_baseline,
                'cost_usd_baseline': cost_usd_baseline,
            })

        interim = pd.DataFrame(interim)
        filename = 'inunriver_rcp85_mean_results.csv'
        folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data', 'countries', country['iso3'])
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_out = os.path.join(folder_out, filename)
        interim = interim.to_csv(path_out, index=False)

    output = []

    for country in countries:

        print('Working on {}'.format(country['iso3']))

        filename = 'inunriver_rcp85_mean_results.csv'
        folder_in = os.path.join(BASE_PATH, '..', 'vis', 'data', 'countries', country['iso3'])
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
    folder_out = os.path.join(BASE_PATH, '..', 'vis', 'data')
    path_out = os.path.join(folder_out, filename)

    output = pd.DataFrame(output)
    output = output.sort_values(by='gid_id')
    output.to_csv(path_out, index=False)

    return output


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

        output.to_file(path)

        return output


def combine_data(results, regions):
    """
    Combine results with regional shapefiles and normalize costs by area.
    """
    regions['iso3'] = regions['GID_id'].str[:3]
    regions['gid_id'] = regions['GID_id']
    regions = regions[['gid_id', 'iso3', 'geometry']].copy()

    # Calculate the area in square kilometers (assuming lat/lon CRS)
    regions['area_km2'] = regions.geometry.to_crs(epsg=6933).area / 1e6  # EPSG:6933 is equal-area projection

    # Merge cost data
    regions = regions.merge(results, how='left', on='gid_id')
    
    # Normalize costs by area
    regions['cost_per_km2'] = regions['cost_usd_baseline'] / regions['area_km2']
    
    regions.to_file(os.path.join(VIS, '..', 'data', 'country_data_riverine.shp'))

    return regions


def plot_regional_results(regions, path, countries):
    """
    Plot regions by cost per square kilometer and highlight North Korea and Western Sahara in gray.
    """
    # Ensure cost per km² is filled and rounded
    regions['cost_per_km2'] = regions['cost_per_k'].fillna(0)
    regions['cost_per_km2'] = round(regions['cost_per_km2'], 0)

    # Define bins and labels for classification
    bins = [-10, 1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 1e12]
    labels = ['$<1k/km²','$5k/km²','$10k/km²','$50k/km²','$100k/km²','$500k/km²','$1M/km²','$5M/km²','$10M/km²','>$10M/km²']

    regions['bin'] = pd.cut(
        regions['cost_per_km2'],
        bins=bins,
        labels=labels
    )

    # Set up figure and axis
    sns.set(font_scale=0.9)
    fig, ax = plt.subplots(1, 1, figsize=(9, 4.5))

    minx, miny, maxx, maxy = regions.total_bounds
    ax.set_xlim(-170, 210)
    ax.set_ylim(miny - 5, maxy)

    # Plot main regions with cost bins
    base = regions.plot(column='bin', ax=ax, cmap='viridis', linewidth=0, legend=True, antialiased=False)
    
    # Plot all countries for context
    countries.plot(ax=base, facecolor="none", edgecolor='grey', linewidth=0.1)

    # Identify and plot North Korea and Western Sahara separately in gray
    gray_countries = countries[countries['NAME_0'].isin(['North Korea', 'Western Sahara'])]

    if not gray_countries.empty:
        gray_countries.plot(ax=base, facecolor="lightgray", edgecolor='grey', linewidth=0.3)

    # Customize legend
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles[::-1], labels[::-1])

    # Title
    n = len(regions)
    title = 'Mean Direct Damage Cost From Riverine Flooding (2080, RCP8.5, 1-in-1000) (n={})'.format(n)
    fig.suptitle(title)

    # Save figure
    fig.tight_layout()
    fig.savefig(path, dpi=300, format='png', bbox_inches='tight', pil_kwargs={"quality": 85})

    plt.close(fig)


if __name__ == "__main__":

    countries = get_countries()#[:2]

    countries_shps = get_country_outlines()

    # results = collect_results(countries)#[:300]
    # out = pd.DataFrame(results)
    # out.to_csv(os.path.join(VIS, '..', 'data.csv'))

    # regions = get_regional_shapes(countries)#[:1000]
    # regions = combine_data(results, regions)
    # regions = pd.DataFrame(regions)

    # regions = regions[['gid_id', 'cost_per_km2']]
    # regions.to_csv(os.path.join(VIS, '..', 'test.csv'))

    path_in_shp = os.path.join(VIS,'..','data','country_data_riverine.shp')
    regions = gpd.read_file(path_in_shp, crs='epsg:4326')#[:1000]
    # print(regions.columns)
    path_in = os.path.join(VIS, 'regions_by_cost_riverine.png')
    plot_regional_results(regions, path_in, countries_shps)
