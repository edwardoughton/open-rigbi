"""
Visualize data

Written by Ed Oughton.

April 2021.

"""
import os
import configparser
import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import contextily as ctx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
RESULTS = os.path.join(BASE_PATH, '..', 'results')
VIS_FIGURES = os.path.join(BASE_PATH, '..', 'vis', 'figures')

def vis(iso3):
    """
    Visualize results.

    """
    strategy = [
        ('clos', 'Females'),
        ('nlos', 'Males')
    ]

    path = os.path.join(DATA_INTERMEDIATE, iso3,  'regional_data.csv')
    data = pd.read_csv(path, encoding='utf8')

    filename = 'regions_2_{}.shp'.format(iso3)
    path = os.path.join(BASE_PATH, 'intermediate', iso3, 'regions')
    regions = gpd.read_file(os.path.join(path, filename), crs='epsg:4326', encoding='utf8')

    regions = pd.merge(left=regions, right=data, left_on='GID_2', right_on='GID_id')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    regions.plot(column='population_f_80', cmap='OrRd', legend=False, ax=ax1)
    regions.plot(column='population_m_80', cmap='OrRd', legend=True, ax=ax2,
            legend_kwds={'label': "Population by Country", 'orientation': "horizontal"})

    ax1.title.set_text('{}'.format(strategy[0][1]))
    ax2.title.set_text('{}'.format(strategy[1][1]))
    ctx.add_basemap(ax1, crs=regions.crs)
    ctx.add_basemap(ax2, crs=regions.crs)
    fig.subplots_adjust(wspace=0, hspace=0)

    filename = os.path.join(VIS_FIGURES, 'gender.png')
    plt.savefig(filename, pad_inches=0, dpi=100)
    plt.close()

    return print('Completed visualization')


if __name__ == '__main__':

    if not os.path.exists(VIS_FIGURES):
        os.makedirs(VIS_FIGURES)

    vis('GMB')
