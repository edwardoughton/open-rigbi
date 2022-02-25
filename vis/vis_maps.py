"""
Plot the geospatial results by country.

Written by Ed Oughton.

February 2022

"""
import os
import sys
import configparser
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as cx
import geopy as gp

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
RESULTS = os.path.join(BASE_PATH, '..', 'results')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')
REPORTS = os.path.join(BASE_PATH, '..', 'reports', 'images')

def get_regional_shapes():
    """
    Load regional shapes.

    """
    output = []

    for item in os.listdir(DATA_INTERMEDIATE):#[:15]:
        if len(item) == 3: # we only want iso3 code named folders

            filename_gid2 = 'regions_2_{}.shp'.format(item)
            path_gid2 = os.path.join(DATA_INTERMEDIATE, item, 'regions', filename_gid2)

            filename_gid1 = 'regions_1_{}.shp'.format(item)
            path_gid1 = os.path.join(DATA_INTERMEDIATE, item, 'regions', filename_gid1)

            if os.path.exists(path_gid2):
                data = gpd.read_file(path_gid2)
                data['GID_id'] = data['GID_2']
                data = data.to_dict('records')

            elif os.path.exists(path_gid1):
                data = gpd.read_file(path_gid1)
                data['GID_id'] = data['GID_1']
                data = data.to_dict('records')
            else:
               print('No shapefiles for {}'.format(item))
               continue

            for datum in data:
                output.append({
                    'geometry': datum['geometry'],
                    'properties': {
                        'GID_id': datum['GID_id'],
                    },
                })

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

    return output


def plot_regions_by_geotype(country, regions, path):
    """
    Plot regions by geotype.

    """
    filename = 'regional_data.csv'
    path_data = os.path.join(DATA_PROCESSED, iso3, filename)
    data = pd.read_csv(path_data)

    n = len(regions)
    data['population_km2'] = round(data['population_total'] / data['area_km2'], 2)
    data = data[['GID_id', 'population_km2']]

    GID_level = 'GID_{}'.format(country['gid_region'])
    regions = regions[[GID_level, 'geometry']]#[:1000]
    regions = regions.copy()

    regions = regions.merge(data, left_on=GID_level, right_on='GID_id')
    regions.reset_index(drop=True, inplace=True)

    metric = 'population_km2'

    bins = [-1, 20, 43, 69, 109, 171, 257, 367, 541, 1104, 111607]
    labels = [
        '<20 $\mathregular{km^2}$',
        '20-43 $\mathregular{km^2}$',
        '43-69 $\mathregular{km^2}$',
        '69-109 $\mathregular{km^2}$',
        '109-171 $\mathregular{km^2}$',
        '171-257 $\mathregular{km^2}$',
        '257-367 $\mathregular{km^2}$',
        '367-541 $\mathregular{km^2}$',
        '541-1104 $\mathregular{km^2}$',
        '>1104 $\mathregular{km^2}$']

    regions['bin'] = pd.cut(
        regions[metric],
        bins=bins,
        labels=labels
    )

    sns.set(font_scale=0.9, font="Times New Roman")
    fig, ax = plt.subplots(1, 1, figsize=country['figsize'])
    # minx, miny, maxx, maxy = regions.total_bounds

    # ax.set_xlim(minx-.5, maxx+.5)
    # ax.set_ylim(miny-0.1, maxy+.1)

    regions.plot(column='bin', ax=ax, cmap='inferno_r', linewidth=0.2,
    legend=True, edgecolor='grey')

    handles, labels = ax.get_legend_handles_labels()

    fig.legend(handles[::-1], labels[::-1])
    # print(cx.providers.CartoDB.Voyager)
    cx.add_basemap(ax, crs=regions.crs, source=cx.providers.CartoDB.Voyager)
    # cx.add_basemap(ax, crs='epsg:4326')

    name = 'Population Density Deciles for Sub-National Regions (n={})'.format(n)
    fig.suptitle(name)

    fig.tight_layout()
    fig.savefig(path, dpi=600)

    plt.close(fig)


def plot_cells_per_region(country, regions, path):
    """
    Plot regions by geotype.

    """
    iso3 = country['iso3']
    name = country['country']

    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_sites = os.path.join(folder, filename)
    sites = pd.read_csv(path_sites, encoding='latin-1')

    sites = gpd.GeoDataFrame(
        sites,
        geometry=gpd.points_from_xy(
            sites.lon,
            sites.lat
        ), crs='epsg:4326'
    )

    fig, (ax1, ax2) = plt.subplots(2, 2, figsize=(12,12))
    fig.subplots_adjust(hspace=.2, wspace=.2)
    fig.set_facecolor('gainsboro')

    gsm = sites.loc[sites['radio'] == 'GSM']
    umts = sites.loc[sites['radio'] == 'UMTS']
    lte = sites.loc[sites['radio'] == 'LTE']
    nr = sites.loc[sites['radio'] == 'NR']

    regions.plot(facecolor="none", edgecolor="grey", ax=ax1[0])
    regions.plot(facecolor="none", edgecolor="grey", ax=ax1[1])
    regions.plot(facecolor="none", edgecolor="grey", ax=ax2[0])
    regions.plot(facecolor="none", edgecolor="grey", ax=ax2[1])

    gsm.plot(color='red', markersize=1, ax=ax1[0])
    umts.plot(color='blue', markersize=1, ax=ax1[1])
    lte.plot(color='yellow', markersize=1, ax=ax2[0])
    nr.plot(color='black', markersize=1, ax=ax2[1])

    ax1[0].set_title('2G GSM Cells')
    ax1[1].set_title('3G UMTS Cells')
    ax2[0].set_title('4G LTE Cells')
    ax2[1].set_title('5G NR Cells')

    fig.tight_layout()

    main_title = 'Mobile Cellular Infrastructure: {}'.format(name)
    plt.suptitle(main_title, fontsize=20, y=1.03)

    crs = 'epsg:4326'
    cx.add_basemap(ax1[0], crs=crs)
    cx.add_basemap(ax1[1], crs=crs)
    cx.add_basemap(ax2[0], crs=crs)
    cx.add_basemap(ax2[1], crs=crs)

    plt.savefig(path,
    pad_inches=0.4,
    bbox_inches='tight'
    )
    plt.close()


def plot_failed_cells_by_scenario_points(country, regions, outline, path):
    """
    Plot regions by geotype as points.

    """
    iso3 = country['iso3']
    name = country['country']

    filename = 'sites_{}.csv'.format(iso3)
    path_data = os.path.join(RESULTS, filename)
    data = pd.read_csv(path_data)

    unique_scenarios = data['scenario'].unique()#[:4]
    num_scenarios = len(unique_scenarios)

    fig, axes = plt.subplots(4, 4, figsize=(10,10))
    fig.subplots_adjust(hspace=.4, wspace=.4)
    fig.set_facecolor('lightgrey')

    technologies = [
        ('GSM', 'black'),
        ('UMTS', 'blue'),
        ('LTE', 'green'),
        ('NR', 'red')
    ]

    for idx, ax in enumerate(axes): #vertical

        for i, technology in enumerate(technologies):

            subset = data.loc[data['scenario'] == unique_scenarios[(idx)]] #not sure this works correctly

            tech_subset = subset.loc[subset['technology'] == technology[0]]

            tech_subset = tech_subset.loc[tech_subset['fragility'] > 0]

            regions.plot(facecolor="none", edgecolor="lightgrey", lw=.5, ax=ax[i])

            # cx.add_basemap(ax[i], crs=regions.crs)

            scenario_name = 'S{}'.format(idx)
            ax[i].set_title('{}_{}'.format(scenario_name, technology[0]))

            if len(tech_subset) > 0:

                sites = gpd.GeoDataFrame(
                    tech_subset,
                    geometry=gpd.points_from_xy(
                        tech_subset.lon,
                        tech_subset.lat
                    ), crs='epsg:4326'
                )

                sites.plot(color=technology[1], markersize=3, ax=ax[i])

    fig.tight_layout()

    main_title = 'Mobile Cellular Infrastructure at Risk by Scenario'
    plt.suptitle(main_title, fontsize=16, y=1.03)

    # crs = 'epsg:4326'
    # cx.add_basemap(ax1[0], crs=crs)
    # cx.add_basemap(ax1[1], crs=crs)
    # cx.add_basemap(ax2[0], crs=crs)
    # cx.add_basemap(ax2[1], crs=crs)

    plt.savefig(path,
    pad_inches=0.4,
    bbox_inches='tight'
    )

    plt.close()


def plot_failed_cells_by_scenario_polygons(country, regions, path):
    """
    Plot regions by geotype.

    """
    iso3 = country['iso3']
    name = country['country']
    GID_level = 'GID_{}'.format(country['gid_region'])

    filename = 'regions_{}.csv'.format(iso3)
    path_data = os.path.join(RESULTS, filename)
    data = pd.read_csv(path_data)

    unique_scenarios = data['scenario'].unique()[:4]
    num_scenarios = len(unique_scenarios)

    fig, axes = plt.subplots(len(unique_scenarios), 4, figsize=(10,10))
    fig.subplots_adjust(hspace=.4, wspace=.4)
    fig.set_facecolor('lightgrey')

    technologies = [
        ('GSM', 'black'),
        ('UMTS', 'blue'),
        ('LTE', 'green'),
        ('NR', 'red')
    ]

    for idx, ax in enumerate(axes): #vertical
        for i, technology in enumerate(technologies):

            subset = data.loc[data['scenario'] == unique_scenarios[idx]]

            tech_subset = subset.loc[subset['technology'] == technology[0]]

            scenario_name = 'S{}'.format(idx)
            ax[i].set_title('{}_{}'.format(scenario_name, technology[0]))

            tech_subset = regions.merge(tech_subset, left_on=GID_level, right_on='GID_id', how='outer')

            cx.add_basemap(ax[i], crs=regions.crs)

            tech_subset = tech_subset[['geometry', 'sites_fail']]

            tech_subset['sites_fail'] = tech_subset['sites_fail'].replace(np.nan, 0)

            if len(tech_subset) > 0:
                tech_subset.plot(column='sites_fail', cmap='viridis',
                    edgecolor="lightgrey", lw=.5, ax=ax[i])

    fig.tight_layout()

    main_title = 'Mobile Cellular Infrastructure at Risk by Scenario'
    plt.suptitle(main_title, fontsize=16, y=1.03)

    # crs = 'epsg:4326'
    # cx.add_basemap(ax1[0], crs=crs)
    # cx.add_basemap(ax1[1], crs=crs)
    # cx.add_basemap(ax2[0], crs=crs)
    # cx.add_basemap(ax2[1], crs=crs)

    plt.savefig(path,
    pad_inches=0.4,
    bbox_inches='tight'
    )

    plt.close()

def single_extreme_plot(country, regions, outline, path):
    """
    Plot regions by geotype as points.

    """
    iso3 = country['iso3']
    name = country['country']

    filename = 'sites_{}.csv'.format(iso3)
    path_data = os.path.join(RESULTS, filename)
    data = pd.read_csv(path_data)

    unique_scenarios = data['scenario'].unique()#[:4]
    num_scenarios = len(unique_scenarios)
    unique_scenarios = [
        'inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp01000.tif',
        'inuncoast_rcp8p5_wtsub_2080_rp1000_0_perc_50.tif'
    ]

    fig, axes = plt.subplots(figsize=(10,10))
    fig.subplots_adjust(hspace=.4, wspace=.4)
    fig.set_facecolor('gainsboro')

    riverine = data.loc[data['scenario'] == unique_scenarios[0]]
    riverine = riverine.loc[riverine['fragility'] > 0]

    coastal = data.loc[data['scenario'] == unique_scenarios[1]]
    coastal = coastal.loc[coastal['fragility'] > 0]

    regions.plot(facecolor="none", edgecolor="lightgrey", lw=1, ax=axes)
    outline.plot(facecolor="none", edgecolor="black", lw=1, ax=axes)

    cx.add_basemap(axes, crs=regions.crs)

    if len(riverine) > 0:
        sites = gpd.GeoDataFrame(
            riverine,
            geometry=gpd.points_from_xy(
                riverine.lon,
                riverine.lat
            ), crs='epsg:4326'
        )
        sites.plot(color='red', markersize=4, marker="o", ax=axes)

    if len(coastal) > 0:
        sites = gpd.GeoDataFrame(
            coastal,
            geometry=gpd.points_from_xy(
                coastal.lon,
                coastal.lat
            ), crs='epsg:4326'
        )
        sites.plot(color='blue', markersize=4, marker="*", ax=axes)

    axes.legend(["Riverine Flooding", "Coastal Flooding"], loc="lower right")

    fig.tight_layout()

    main_title1 = 'Climate Hazard Risk to Mobile Infrastructure in Ghana:\n'
    main_title2 = '1-in-1000 Event for Riverine and Coastal Flooding in 2080'
    plt.title((main_title1+main_title2), fontsize=14, y=1)
    sup_title = 'Scenario: RCP8.5-SSP3, Riverine Model: MIROC-ESM-CHEM, Coastal Model: RISES-AM)'
    plt.suptitle(sup_title, fontsize=10)#, y=1.03

    plt.savefig(path,
    pad_inches=0.4,
    bbox_inches='tight'
    )

    plt.close()


if __name__ == '__main__':

    filename = 'countries.csv'
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        iso3 = country['iso3']
        country['figsize'] = (8,10)

        print('-- {} --'.format(iso3))

        folder_reports = os.path.join(REPORTS, iso3)
        if not os.path.exists(folder_reports):
            os.makedirs(folder_reports)

        folder_vis = os.path.join(VIS, iso3)
        if not os.path.exists(folder_vis):
            os.makedirs(folder_vis)

        filename = 'regions_{}_{}.shp'.format(country['gid_region'], iso3)
        path = os.path.join(DATA_PROCESSED, iso3, 'regions', filename)
        shapes = gpd.read_file(path, crs='epsg:4326')

        filename = 'national_outline.shp'
        path = os.path.join(DATA_PROCESSED, iso3, filename)
        outline = gpd.read_file(path, crs='epsg:4326')

        path = os.path.join(folder_vis, '{}_by_pop_density.png'.format(iso3))
        if not os.path.exists(path):
            plot_regions_by_geotype(country, shapes, path)

        path = os.path.join(folder_vis, '{}_cells_by_region.png'.format(iso3))
        if not os.path.exists(path):
            plot_cells_per_region(country, shapes, path)

        # path = os.path.join(folder_vis, '{}_failed_cells_by_scenario_points.png'.format(iso3))
        # # if not os.path.exists(path):
        # plot_failed_cells_by_scenario_points(country, shapes, outline, path)

        path = os.path.join(folder_vis, '{}_single_extreme_plot.png'.format(iso3))
        # if not os.path.exists(path):
        single_extreme_plot(country, shapes, outline, path)

        # path = os.path.join(folder_vis, '{}_failed_cells_by_scenario.png'.format(iso3))
        # # if not os.path.exists(path):
        # plot_failed_cells_by_scenario_polygons(country, shapes, path)

        print('Complete')
