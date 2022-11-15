"""
Break down coverage by population percentiles/deciles.

"""
import os
import configparser
import pandas as pd
from tqdm import tqdm

from misc import params, technologies, get_countries, get_regions, get_scenarios


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
RESULTS = os.path.join(BASE_PATH, '..', 'results')


def write_points_as_text(country, regions):
    """
    Write out points layer as single .csv.

    """
    output = []

    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        GID_level = 'GID_{}'.format(country['lowest'])
        gid_id = region[GID_level]

        # if not gid_id == 'GHA.1.1_1':
        #     continue

        path_in = os.path.join(
            DATA_PROCESSED,
            country['iso3'],
            'regional_data',
            gid_id,
            'settlements',
            'points.csv'
        )

        if not os.path.exists(path_in):
            return

        data = pd.read_csv(path_in)
        data = data.to_dict('records')

        for technology in tqdm(technologies):

            # if not technology == 'GSM':
            #     continue

            path_out = os.path.join(
                DATA_PROCESSED,
                country['iso3'],
                'regional_data',
                gid_id,
                'coverage_{}.csv'.format(technology)
            )

            # if os.path.exists(path_out):
            #     return

            output = []

            filename = '{}_sinr_lut.csv'.format(technology)
            folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regional_data', gid_id)
            path_in = os.path.join(folder, filename)
            if not os.path.exists(path_in):
                continue
            sinr_lut = pd.read_csv(path_in)

            seen = set()

            for tile1 in data:

                tile_id1 = '{}_{}'.format(
                    int(round(float(tile1['point_id'].split('_')[0]),5)),
                    int(round(float(tile1['point_id'].split('_')[1]),5)),
                )

                if tile_id1 in seen:
                    continue

                if tile1['point_value'] > 0:
                    population = tile1['point_value']
                else:
                    population = 0

                covered = 0
                sinr = '<1'

                for idx, tile2 in sinr_lut.iterrows():

                    tile_id2 = '{}_{}'.format(
                        int(round(float(tile2['point_id'].split('_')[0]),5)),
                        int(round(float(tile2['point_id'].split('_')[1]),5))
                    )

                    if tile_id1 == tile_id2:
                        if tile2['sinr1'] > 0:
                            covered = 1
                            sinr = tile2['sinr1']

                output.append({
                    'GID_id': gid_id,
                    'GID_level': GID_level,
                    'technology': technology,
                    'population': population,
                    'covered': covered,
                    'area_km2': 1,
                    'sinr1': sinr,
                })
                seen.add(tile_id1)

            output = pd.DataFrame(output)
            output.to_csv(path_out, index=False)

    return


def collect_data(country, regions, technologies):
    """
    Estimate percentiles.

    """
    for technology in tqdm(technologies):

        output = []

        for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

            GID_level = 'GID_{}'.format(country['lowest'])
            gid_id = region[GID_level]

            # if not gid_id == 'GHA.1.1_1':
            #     continue

            path_in = os.path.join(
                DATA_PROCESSED,
                country['iso3'],
                'regional_data',
                gid_id,
                'coverage_{}.csv'.format(technology)
            )

            if not os.path.exists(path_in):
                continue

            data = pd.read_csv(path_in)

            for idx, item in data.iterrows():

                output.append({
                    'technology': technology,
                    'population': item['population'],
                    'covered': item['covered'],
                    'area_km2': 1,
                })

        output = pd.DataFrame(output)

        output = pd.DataFrame(output)
        filename = 'coverage_{}.csv'.format(technology)
        path = os.path.join(DATA_PROCESSED, country['iso3'], filename)
        output.to_csv(path, index=False)

    return


def allocate_groups(country, technologies):
    """
    Estimate percentiles.

    """
    output = []

    for technology in tqdm(technologies):

        path_in = os.path.join(
            DATA_PROCESSED,
            country['iso3'],
            'coverage_{}.csv'.format(technology)
        )

        if not os.path.exists(path_in):
            continue

        data = pd.read_csv(path_in)

        decile_results = define_deciles(data)
        decile_results = decile_results[['decile','technology','covered','population','area_km2']]
        decile_results = decile_results.drop_duplicates().reset_index()
        decile_results = decile_results.groupby(['decile', 'technology', 'covered']).agg({
            'population':'sum', 'area_km2':'sum'}).reset_index()
        decile_results['population_km2'] = (
            decile_results['population'] / decile_results['area_km2'])

        decile_results = decile_results.to_dict('records')
        output = output + decile_results

    output = pd.DataFrame(output)
    filename = 'coverage_by_decile.csv'
    path = os.path.join(DATA_PROCESSED, country['iso3'], filename)
    output.to_csv(path, index=False)

    return


def define_deciles(regions):
    """
    Allocate deciles to regions.

    """
    regions = regions.sort_values(by='population', ascending=True)

    regions['decile'] = regions.groupby([
        'technology'], as_index=True).population.apply(
        pd.qcut, q=10, precision=0,
        labels=[100,90,80,70,60,50,40,30,20,10],
        duplicates='drop') #   [0,10,20,30,40,50,60,70,80,90,100]

    return regions


if __name__ == "__main__":

    countries = get_countries()

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        regions = get_regions(country)

        write_points_as_text(country, regions)

        collect_data(country, regions, technologies)

        allocate_groups(country, technologies)
