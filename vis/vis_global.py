"""
Plot scenarios geographically.

Written by Ed Oughton.

October 2022.

"""
import os
import configparser
# import json
# import csv
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
# import contextily as ctx
# import openpyxl
import xlwings as xw

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')


def plot_regions(regions, path, imf_countries, non_imf):
    """
    Plot regions by geotype.

    """
    metric = 'cost'

    regions['cost'] = round(regions['cost'] / 1e6)

    regions['cost'] = regions['cost'].fillna(0)
    regions.to_file(os.path.join(VIS,'..','data','test4.shp'))

    satellite = regions[regions['GID_0'].isna()]

    regions = regions.dropna()
    zeros = regions[regions['cost'] == 0]
    regions = regions[regions['cost'] != 0]

    bins = [0,10,20,30,40,50,60,70,80,90,1e12]
    labels = ['<$10m','$20m','$30m','$40m','$50m','$60m','$70m','$80m','$90m','>$100m']

    regions['bin'] = pd.cut(
        regions[metric],
        bins=bins,
        labels=labels
    )

    sns.set(font_scale=0.9)
    fig, ax = plt.subplots(1, 1, figsize=(10, 4.5))

    minx, miny, maxx, maxy = regions.total_bounds
    # ax.set_xlim(minx+20, maxx-2)
    # ax.set_ylim(miny+2, maxy-10)
    ax.set_xlim(minx-20, maxx+5)
    ax.set_ylim(miny-5, maxy)

    base = regions.plot(column='bin', ax=ax, cmap='viridis', linewidth=0, #inferno_r
        legend=True, antialiased=False)
    # # imf_countries.plot(ax=base, facecolor="none", edgecolor='grey', linewidth=0.1)
    zeros = zeros.plot(ax=base, color='dimgray', edgecolor='dimgray', linewidth=0)
    non_imf.plot(ax=base, color='lightgrey', edgecolor='lightgrey', linewidth=0)

    handles, labels = ax.get_legend_handles_labels()

    fig.legend(handles[::-1], labels[::-1])

    # ctx.add_basemap(ax, crs=regions.crs, source=ctx.providers.CartoDB.Voyager)

    n = len(regions)
    name = 'Universal Broadband Infrastructure Investment Cost by Sub-National Region (n={})'.format(n)
    fig.suptitle(name)

    fig.tight_layout()
    fig.savefig(path)

    plt.close(fig)
