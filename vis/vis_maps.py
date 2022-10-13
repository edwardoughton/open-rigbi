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
# import geopy as gp

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

    GID_level = 'GID_{}'.format(country['lowest'])
    regions = regions[[GID_level, 'geometry']]#[:1000]
    regions = regions.copy()

    regions = regions.merge(data, left_on=GID_level, right_on='GID_id')
    regions.reset_index(drop=True, inplace=True)

    metric = 'population_km2'

    bins = [-1, 20, 43, 69, 109, 171, 257, 367, 541, 1104, 1e8]
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
        '>1104 $\mathregular{km^2}$'
    ]

    regions['bin'] = pd.cut(
        regions[metric],
        bins=bins,
        labels=labels
    )

    sns.set(font_scale=1, font="Times New Roman")
    fig, ax = plt.subplots(1, 1, figsize=country['figsize'])
    minx, miny, maxx, maxy = regions.total_bounds

    ax.set_xlim(minx-.5, maxx+.5)
    ax.set_ylim(miny-0.1, maxy+.1)

    regions.plot(column='bin', ax=ax, cmap='viridis_r', linewidth=0.2, alpha=0.8,
    legend=True, edgecolor='grey')

    handles, labels = ax.get_legend_handles_labels()

    fig.legend(handles[::-1], labels[::-1])

    cx.add_basemap(ax, crs=regions.crs, source=cx.providers.CartoDB.Voyager)
    cx.add_basemap(ax, crs='epsg:4326')

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

    filename = 'national_outline.shp'
    path_outline = os.path.join(DATA_PROCESSED, iso3, filename)
    national_outline = gpd.read_file(path_outline, crs='epsg:4326')

    filename = 'surface_water.shp'
    path_water = os.path.join(DATA_PROCESSED, iso3, 'surface_water', filename)
    surface_water = gpd.read_file(path_water, crs='epsg:4326')

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

    # df1.union(df2)
    # sites = sites.difference(surface_water)
    # sites = sites.overlay(surface_water, how='difference')
    # sites = sites.intersection(national_outline)
    # sites = sites.overlay(national_outline, how='intersection')
    # print(sites)
    fig, (ax1, ax2) = plt.subplots(2, 2, figsize=(12,12))
    fig.subplots_adjust(hspace=.2, wspace=.2)

    minx, miny, maxx, maxy = regions.total_bounds
    buffer = 2
    for ax in [ax1, ax2]:
        for dim in [0,1]:
            ax[dim].set_xlim(minx-buffer, maxx+buffer)
            ax[dim].set_ylim(miny-0.1, maxy+.1)

    fig.set_facecolor('gainsboro')

    gsm = sites.loc[sites['radio'] == 'GSM']
    umts = sites.loc[sites['radio'] == 'UMTS']
    lte = sites.loc[sites['radio'] == 'LTE']
    nr = sites.loc[sites['radio'] == 'NR']

    # regions.plot(facecolor="none", lw=.5, edgecolor="grey", ax=ax1[0])
    # regions.plot(facecolor="none", lw=.5, edgecolor="grey", ax=ax1[1])
    # regions.plot(facecolor="none", lw=.5, edgecolor="grey", ax=ax2[0])
    # regions.plot(facecolor="none", lw=.5, edgecolor="grey", ax=ax2[1])

    national_outline.plot(facecolor="none", lw=2, edgecolor="black", ax=ax1[0])
    national_outline.plot(facecolor="none", lw=2, edgecolor="black", ax=ax1[1])
    national_outline.plot(facecolor="none", lw=2, edgecolor="black", ax=ax2[0])
    national_outline.plot(facecolor="none", lw=2, edgecolor="black", ax=ax2[1])

    gsm.plot(color='red', markersize=3, ax=ax1[0])
    umts.plot(color='blue', markersize=3, ax=ax1[1])
    lte.plot(color='yellow', markersize=3, ax=ax2[0])
    nr.plot(color='black', markersize=3, ax=ax2[1])

    ax1[0].set_title('2G GSM Cells')
    ax1[1].set_title('3G UMTS Cells')
    ax2[0].set_title('4G LTE Cells')
    ax2[1].set_title('5G NR Cells')

    filename = 'core_edges_existing.shp'
    folder = os.path.join(DATA_PROCESSED, iso3, 'network_existing')
    path_fiber = os.path.join(folder, filename)
    if os.path.exists(path_fiber):
        fiber = gpd.read_file(path_fiber, crs='epsg:4326')
        fiber.plot(color='orange', lw=2, ax=ax1[0])
        fiber.plot(color='orange', lw=2, ax=ax1[1])
        fiber.plot(color='orange', lw=2, ax=ax2[0])
        fiber.plot(color='orange', lw=2, ax=ax2[1])

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
    bbox_inches='tight',
    dpi=600,
    )
    plt.close()


def plot_coverage_by_region(country, regions, path):
    """
    Plot regions by geotype.

    """
    iso3 = country['iso3']
    name = country['country']

    filename = 'baseline_coverage.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path_data = os.path.join(folder, filename)
    data = pd.read_csv(path_data, encoding='latin-1')
    data = data[['GID_id', 'technology', 'covered_pop_perc', 'uncovered_pop_perc']]
    data = format_data(data, regions)
    data = pd.DataFrame(data)

    regions = regions.merge(data, left_on='GID_2', right_on='GID_id')
    regions.reset_index(drop=True, inplace=True)

    bins = [-1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 1e8]
    labels = [
        '<10%',
        '10-20%',
        '20-30%',
        '30-40%',
        '40-50%',
        '50-60%',
        '60-70%',
        '70-80%',
        '80-90%',
        '90-100%'
    ]

    regions['bin'] = pd.cut(
        regions['covered_pop_perc'],
        bins=bins,
        labels=labels
    )#.add_categories('missing')

    regions['bin'].fillna('<10%')

    regions.to_csv(os.path.join(VIS, 'test.csv'))

    fig, (ax1, ax2) = plt.subplots(2, 2, figsize=(12,12))
    fig.subplots_adjust(hspace=.2, wspace=.2)

    minx, miny, maxx, maxy = regions.total_bounds
    buffer = 2
    for ax in [ax1, ax2]:
        for dim in [0,1]:
            ax[dim].set_xlim(minx-buffer, maxx+buffer)
            ax[dim].set_ylim(miny-0.1, maxy+.1)

    fig.set_facecolor('gainsboro')

    gsm = regions.loc[regions['technology'] == 'GSM']
    umts = regions.loc[regions['technology'] == 'UMTS']
    lte = regions.loc[regions['technology'] == 'LTE']
    nr = regions.loc[regions['technology'] == 'NR']

    if len(nr) == 0:
        nr = lte.copy()
        nr['technology'] = 'NR'
        nr['bin'] = '<10%'

    gsm.plot(column='bin', cmap='viridis_r', linewidth=0.2, alpha=0.8,
        legend=True, edgecolor='grey', ax=ax1[0])
    umts.plot(column='bin', cmap='viridis_r', linewidth=0.2, alpha=0.8,
    legend=True, edgecolor='grey', ax=ax1[1])
    lte.plot(column='bin', cmap='viridis_r', linewidth=0.2, alpha=0.8,
    legend=True, edgecolor='grey', ax=ax2[0])
    nr.plot(column='bin', cmap='viridis_r', linewidth=0.2, alpha=0.8,
    legend=True, edgecolor='grey', ax=ax2[1])

    ax1[0].set_title('Covered by 2G GSM (%)')
    ax1[1].set_title('Covered by 3G UMTS (%)')
    ax2[0].set_title('Covered by 4G LTE (%)')
    ax2[1].set_title('Covered by 5G NR (%)')

    fig.tight_layout()

    main_title = 'Covered Population by Region: {}'.format(name)
    plt.suptitle(main_title, fontsize=20, y=1.01)

    crs = 'epsg:4326'
    cx.add_basemap(ax1[0], crs=crs)
    cx.add_basemap(ax1[1], crs=crs)
    cx.add_basemap(ax2[0], crs=crs)
    cx.add_basemap(ax2[1], crs=crs)

    plt.savefig(path,
    # pad_inches=0.4,
    bbox_inches='tight'
    )
    plt.close()


def plot_uncovered_pop_by_region(country, outline, path):
    """
    Plot uncovered population by region.

    """
    iso3 = country['iso3']
    name = country['country']

    fig, (ax1, ax2) = plt.subplots(2, 2, figsize=(12,12))
    fig.subplots_adjust(hspace=.2, wspace=.2)

    minx, miny, maxx, maxy = outline.total_bounds
    buffer = 2
    for ax in [ax1, ax2]:
        for dim in [0,1]:
            ax[dim].set_xlim(minx-buffer, maxx+buffer)
            ax[dim].set_ylim(miny-0.1, maxy+.1)

    fig.set_facecolor('gainsboro')

    outline.plot(facecolor="none", edgecolor="grey", ax=ax1[0])
    outline.plot(facecolor="none", edgecolor="grey", ax=ax1[1])
    outline.plot(facecolor="none", edgecolor="grey", ax=ax2[0])
    outline.plot(facecolor="none", edgecolor="grey", ax=ax2[1])

    folder = os.path.join(DATA_PROCESSED, iso3, 'coverage')

    path1 = os.path.join(folder, 'baseline_uncovered_GSM.shp')
    if os.path.exists(path1):
        gsm = gpd.read_file(path1, crs='epsg:3857')
        gsm = gsm.to_crs(4326)
        gsm.plot(color='red', linewidth=0.2, alpha=0.4,
            legend=True, edgecolor='grey', ax=ax1[0])

    path2 = os.path.join(folder, 'baseline_uncovered_UMTS.shp')
    if os.path.exists(path2):
        umts = gpd.read_file(path2, crs='epsg:3857')
        umts = umts.to_crs(4326)
        umts.plot(color='blue', linewidth=0.2, alpha=0.4,
            legend=True, edgecolor='grey', ax=ax1[1])

    path3 = os.path.join(folder, 'baseline_uncovered_LTE.shp')
    if os.path.exists(path3):
        lte = gpd.read_file(path3, crs='epsg:3857')
        lte = lte.to_crs(4326)
        lte.plot(color='yellow', linewidth=0.2, alpha=0.4,
            legend=True, edgecolor='grey', ax=ax2[0])

    path4 = os.path.join(folder, 'baseline_uncovered_NR.shp')
    if os.path.exists(path4):
        nr = gpd.read_file(path4, crs='epsg:3857')
        nr = nr.to_crs(4326)
        nr.plot(color='black', linewidth=0.2, alpha=0.4,
            legend=True, edgecolor='grey', ax=ax2[1])
    else:
        nr = gpd.read_file(os.path.join(folder, '..', 'national_outline.shp'), crs='epsg:4326')
        nr.plot(color='black', linewidth=0.2, alpha=0.4,
            legend=True, edgecolor='grey', ax=ax2[1])

    ax1[0].set_title('2G GSM Uncovered')
    ax1[1].set_title('3G UMTS Uncovered')
    ax2[0].set_title('4G LTE Uncovered')
    ax2[1].set_title('5G NR Uncovered')

    fig.tight_layout()

    main_title = 'Uncovered Population: {}'.format(name)
    plt.suptitle(main_title, fontsize=20, y=1.01)

    crs = 'epsg:4326'
    cx.add_basemap(ax1[0], crs=crs)
    cx.add_basemap(ax1[1], crs=crs)
    cx.add_basemap(ax2[0], crs=crs)
    cx.add_basemap(ax2[1], crs=crs)

    plt.savefig(path,
    # pad_inches=0.4,
    bbox_inches='tight'
    )
    plt.close()


def format_data(data, regions):
    """

    """
    output = []

    technologies = data['technology'].unique()
    regions = regions['GID_2'].unique()

    for region in regions:
        for technology in technologies:

            if ((data['GID_id'] == region) & (data['technology'] == technology)).any():
                subset = data.loc[(data['GID_id'] == region) & (data['technology'] == technology)]
                covered_pop_perc = subset['covered_pop_perc'].values[0]
                uncovered_pop_perc = subset['uncovered_pop_perc'].values[0]
            else:
                covered_pop_perc = 0
                uncovered_pop_perc = 100

            output.append({
                'GID_id': region,
                'technology': technology,
                'covered_pop_perc': covered_pop_perc,
                'uncovered_pop_perc': uncovered_pop_perc,
            })

    return output


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

    filename = 'core_edges_existing.shp'
    folder = os.path.join(DATA_PROCESSED, iso3, 'network_existing')
    path_fiber = os.path.join(folder, filename)
    fiber = gpd.read_file(path_fiber, crs='epsg:4326')
    fiber.plot(color='orange', lw=0.5, ax=axes)

    cx.add_basemap(axes, crs=regions.crs)

    if len(riverine) > 0:
        sites = gpd.GeoDataFrame(
            riverine,
            geometry=gpd.points_from_xy(
                riverine.lon,
                riverine.lat
            ), crs='epsg:4326'
        )
        sites.plot(color='red', markersize=2, marker="o", ax=axes)
        buffers_red = sites
        buffers_red['geometry'] = buffers_red['geometry'].buffer(0.05)
        buffers_red.plot(color='red', alpha=.08, ax=axes)

    if len(coastal) > 0:
        sites = gpd.GeoDataFrame(
            coastal,
            geometry=gpd.points_from_xy(
                coastal.lon,
                coastal.lat
            ), crs='epsg:4326'
        )
        sites.plot(color='blue', markersize=2, marker="*", ax=axes)
        buffers_blue = sites
        buffers_blue['geometry'] = buffers_blue['geometry'].buffer(0.05)
        buffers_blue.plot(color='blue', alpha=.08, ax=axes)

    axes.legend(["Fiber Network","Riverine Flooding", "Coastal Flooding"], loc="lower right")

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

        if not country['iso3'] in ['MWI']: #['MWI','GHA']
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

        filename = 'regions_{}_{}.shp'.format(country['lowest'], iso3)
        path = os.path.join(DATA_PROCESSED, iso3, 'regions', filename)
        shapes = gpd.read_file(path, crs='epsg:4326')

        filename = 'national_outline.shp'
        path = os.path.join(DATA_PROCESSED, iso3, filename)
        outline = gpd.read_file(path, crs='epsg:4326')

        # path = os.path.join(folder_vis, '{}_by_pop_density.png'.format(iso3))
        # if not os.path.exists(path):
        #     plot_regions_by_geotype(country, shapes, path)

        path = os.path.join(folder_vis, '{}_cells_by_region.tiff'.format(iso3))
        # if not os.path.exists(path):
        plot_cells_per_region(country, shapes, path)

        # path = os.path.join(folder_vis, '{}_covered_by_region.png'.format(iso3))
        # if not os.path.exists(path):
        #     plot_coverage_by_region(country, shapes, path)

        # path = os.path.join(folder_vis, '{}_uncovered_by_region.png'.format(iso3))
        # # if not os.path.exists(path):
        # plot_uncovered_pop_by_region(country, outline, path)

        # path = os.path.join(folder_vis, '{}_single_extreme_plot.png'.format(iso3))
        # # if not os.path.exists(path):
        # single_extreme_plot(country, shapes, outline, path)

        print('Complete')
