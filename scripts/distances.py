"""
Script to estimate distances between cell sites and tile points.

Written by Ed Oughton.

February 2022.

"""
import os
import configparser
import random
import json
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio import features
from tqdm import tqdm
from shapely.geometry import shape, Point, mapping, LineString
import math

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def query_settlement_layers(country, region):
    """


    """
    path_settlements = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'age_sex_structure',
        'ppp_2020_1km_Aggregated.tif'
    )

    settlements = rasterio.open(path_settlements, 'r+')
    settlements.nodata = 255
    settlements.crs.from_epsg(4326)

    folder = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        'settlements'
    )
    shape_path = os.path.join(folder, 'settlements.tif')

    if os.path.exists(shape_path):
        return #print('Completed settlement layer processing')

    if not os.path.exists(folder):
        os.mkdir(folder)

    bbox = region['geometry'].envelope
    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0])

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(settlements, coords, crop=True)

    out_meta = settlements.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(shape_path, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def convert_to_shapes(country, region):
    """
    Convert settlement raster to vector shapefile by region.

    """
    folder = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        'settlements'
    )
    path_out = os.path.join(folder, 'points.shp')

    if os.path.exists(path_out):
        return

    shape_path = os.path.join(folder, 'settlements.tif')
    settlements = rasterio.open(shape_path, 'r+')
    settlements.nodata = 255
    settlements.crs.from_epsg(4326)
    data = settlements.read(1)

    output = []

    for geom, value in features.shapes(data, transform=settlements.transform):

        geom = rasterio.warp.transform_geom(
            settlements.crs, 'EPSG:4326', geom, precision=6)

        geom_centroid = shape(geom).centroid

        if value == 255:
            continue

        output.append({
            'geometry': geom_centroid,
            'properties': {
                'point_id': '{}-{}'.format(
                    round(geom_centroid.coords.xy[0][0], 6),
                    round(geom_centroid.coords.xy[1][0], 6)
                ),
                'value': value
            }
        })

    output = gpd.GeoDataFrame.from_features(output, crs='EPSG:4326')
    output.to_file(path_out)

    return


def calculate_distances_lut(country, region, technology):
    """
    Calculate distances.

    """
    path_out = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        '{}_distance_lut.csv'.format(technology)
    )

    if os.path.exists(path_out):
        return

    path_points = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        'settlements',
        'points.shp'
    )

    points = gpd.read_file(path_points, crs='epsg:4326')
    points = points.to_crs(epsg=3857)

    path_sites = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'sites',
        technology,
        '{}_{}.shp'.format(technology, region['GID_{}'.format(country['lowest'])])
    )

    sites = gpd.read_file(path_sites, crs='epsg:4326')#[:1]
    sites = sites.to_crs(epsg=3857)

    output = []

    for idx, site in sites.iterrows():

        site_geom = site['geometry'].buffer(15000)

        site_buffer = gpd.GeoDataFrame(geometry=[site_geom], crs='epsg:3857')

        subset_points = gpd.overlay(points, site_buffer, how='intersection')

        for idx, point in subset_points.iterrows():

            line = LineString(
                [
                    (site['geometry'].coords.xy[0][0], site['geometry'].coords.xy[1][0]),
                    (point['geometry'].coords.xy[0][0], point['geometry'].coords.xy[1][0])
                ]
            )

            output.append({
                'radio': site['radio'],
                'mcc': site['mcc'],
                'net': site['net'],
                'area': site['area'],
                'cell': site['cell'],
                'cell_lon': site['geometry'].coords.xy[0][0],
                'cell_lat': site['geometry'].coords.xy[1][0],
                'point_id': point['point_id'],
                'point_lon': point['geometry'].coords.xy[0][0],
                'point_lat': point['geometry'].coords.xy[1][0],
                'distance_m': line.length,
            })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


# def calculate_interference_distances_lut(country, region, technology):
    """

    """
    path_out = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        '{}_interference_distance_lut.csv'.format(technology)
    )

    # if os.path.exists(path_out):
    #     return

    path_points = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        'settlements',
        'points.shp'
    )

    points = gpd.read_file(path_points, crs='epsg:4326')
    points = points.to_crs(epsg=3857)

    path_sites = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'sites',
        technology,
        '{}_{}.shp'.format(technology, region['GID_{}'.format(country['lowest'])])
    )

    sites = gpd.read_file(path_sites, crs='epsg:4326')#[:5]
    sites = sites.to_crs(epsg=3857)
    sites['cell_id_index'] = sites['cell_id']
    sites.set_index('cell_id_index', inplace=True)

    output = []

    all_sites = sites

    for idx, site in sites.iterrows():

        single_site = gpd.GeoDataFrame(geometry=[site['geometry']], crs='epsg:3857')

        site_distances = all_sites
        site_distances['distance'] = all_sites.geometry.apply(lambda g: single_site.distance(g))

        site_distances = site_distances.loc[site_distances['distance'] > 100]

        if len(site_distances) >= 1:
            site_distances = site_distances.sort_values('distance')[1:4]

        if len(site_distances) == 0:
            continue

        site_distances = site_distances.reset_index(level=0)

        int1 = site_distances.iloc[[0]]
        int1_distance_m = int1['distance'].values[0]
        int_1_cell_id = int1['cell_id'].values[0]

        int2_distance_m = 0
        int_2_cell_id = 'N/A'

        int3_distance_m = 0
        int_3_cell_id = 'N/A'

        if len(site_distances) >= 2:
            int2 = site_distances.iloc[[1]]
            int2_distance_m = int2['distance'].values[0]
            int_2_cell_id = int2['cell_id'].values[0]

        if len(site_distances) >= 3:
            int3 = site_distances.iloc[[2]]
            int3_distance_m = int3['distance'].values[0]
            int_3_cell_id = int3['cell_id'].values[0]

        output.append({
            'radio': site['radio'],
            'mcc': site['mcc'],
            'net': site['net'],
            'area': site['area'],
            'cell': site['cell'],
            'cell_id': site['cell_id'],
            'cell_lon': site['geometry'].coords.xy[0][0],
            'cell_lat': site['geometry'].coords.xy[1][0],
            'int1_distance_m': int1_distance_m,
            'int2_distance_m': int2_distance_m,
            'int3_distance_m': int3_distance_m,
            'int_1_cell_id': int_1_cell_id,
            'int_2_cell_id': int_2_cell_id,
            'int_3_cell_id': int_3_cell_id,
        })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def calculate_sinr_lut(country, region, technology):
    """
    Calculate the sinr for each settlement tile.

    """
    path_out = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        '{}_sinr_lut.csv'.format(technology)
    )

    # if os.path.exists(path_out):
    #     return

    path_dist_lut = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        # 'settlements',
        '{}_distance_lut.csv'.format(technology)
    )

    dist_lut = pd.read_csv(path_dist_lut)[:1000]

    path_interference_dist_lut = os.path.join(
        DATA_PROCESSED,
        iso3,
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        # 'settlements',
        '{}_interference_distance_lut.csv'.format(technology)
    )

    int_dist_lut = pd.read_csv(path_interference_dist_lut)[:1000]
    int_dist_lut['cell_id_3857'] = (
        int_dist_lut['cell_lon'].astype(str) +
        '_' +
        int_dist_lut['cell_lat'].astype(str)
    )

    output = []

    for idx, item in dist_lut.iterrows():

        random_variations = generate_log_normal_dist_value(
                8*10**9,#params['dl_frequency'],
                2,#params['mu'],
                10,#params['sigma'],
                42,#params['seed_value'],
                1,#params['iterations']
        )

        distance = item['distance_m']

        path_loss, random_variation = calc_free_space_path_loss(
            distance, 8*10**9, random_variations
        )
        # path_loss = 160

        antenna_gain = 18
        # eirp = calc_eirp(44, antenna_gain)
        eirp = 60.5
        losses = calc_losses(12, .5)

        received_power = calc_received_power(eirp, path_loss, 0, losses)

        interference = calc_interference(item, int_dist_lut)

        noise = calc_noise()

        sinr = calc_sinr(received_power, interference, noise)

        output.append({
            'radio': item['radio'],
            'mcc': item['mcc'],
            'net': item['net'],
            'area': item['area'],
            'cell': item['cell'],
            'cell_lon': item['cell_lon'],
            'cell_lat': item['cell_lat'],
            'point_id': item['point_id'],
            'point_lon': item['point_lon'],
            'point_lat': item['point_lat'],
            'distance_m': item['distance_m'],
            # 'random_variation_mean': random_variation.mean(),
            'path_loss': path_loss,
            'antenna_gain': antenna_gain,
            'eirp': eirp,
            'losses': losses,
            'received_power': received_power,
            'interference': interference,
            'noise': noise,
            'sinr': sinr,
        })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return



def calc_free_space_path_loss(distance, dl_frequency, random_variations):
    """
    Calculate the free space path loss in decibels.
    FSPL(dB) = 20log(d) + 20log(f) + 32.44
    Where distance (d) is in km and frequency (f) is MHz.

    Parameters
    ----------
    distance : float
        Distance between transmitter and receiver in metres.
    dl_frequency : dict
        Downlink frequency.
    i : int
        Iteration number.
    random_variation : list
        List of random variation components.

    Returns
    -------
    path_loss : float
        The free space path loss over the given distance.
    random_variation : float
        Stochastic component.

    """
    frequency_MHz = dl_frequency / 1e6
    distance = distance / 1e3
    path_loss = 20*math.log10(distance) + 20*math.log10(frequency_MHz) + 32.44

    random_variation = random_variations.mean()

    path_loss = path_loss + random_variation

    return path_loss, random_variation


def generate_log_normal_dist_value(frequency, mu, sigma, seed_value, draws):
    """
    Generates random values using a lognormal distribution, given a specific mean (mu)
    and standard deviation (sigma).
    Original function in pysim5G/path_loss.py.
    The parameters mu and sigma in np.random.lognormal are not the mean and STD of the
    lognormal distribution. They are the mean and STD of the underlying normal distribution.

    Parameters
    ----------
    frequency : float
        Carrier frequency value in Hertz.
    mu : int
        Mean of the desired distribution.
    sigma : int
        Standard deviation of the desired distribution.
    seed_value : int
        Starting point for pseudo-random number generator.
    draws : int
        Number of required values.

    Returns
    -------
    random_variation : float
        Mean of the random variation over the specified itations.
    """
    if seed_value == None:
        pass
    else:
        frequency_seed_value = seed_value * frequency * 100
        np.random.seed(int(str(frequency_seed_value)[:2]))

    normal_std = np.sqrt(np.log10(1 + (sigma/mu)**2))
    normal_mean = np.log10(mu) - normal_std**2 / 2

    random_variation  = np.random.lognormal(normal_mean, normal_std, draws)

    return random_variation


def calc_eirp(power, antenna_gain):
    """
    Calculate the Equivalent Isotropically Radiated Power.
    Equivalent Isotropically Radiated Power (EIRP) = (
        Power + Gain
    )
    Parameters
    ----------
    power : float
        Transmitter power in watts.
    antenna_gain : float
        Antenna gain in dB.
    losses : float
        Antenna losses in dB.
    Returns
    -------
    eirp : float
        eirp in dB.
    """
    eirp = power + antenna_gain

    return eirp


def calc_losses(earth_atmospheric_losses, all_other_losses):
    """
    Estimates the transmission signal losses.
    Parameters
    ----------
    earth_atmospheric_losses : int
        Signal losses from rain attenuation.
    all_other_losses : float
        All other signal losses.
    Returns
    -------
    losses : float
        The estimated transmission signal losses.
    """
    losses = earth_atmospheric_losses + all_other_losses

    return losses


def calc_received_power(eirp, path_loss, receiver_gain, losses):
    """
    Calculates the power received at the User Equipment (UE).
    Parameters
    ----------
    eirp : float
        The Equivalent Isotropically Radiated Power in dB.
    path_loss : float
        The free space path loss over the given distance.
    receiver_gain : float
        Antenna gain at the receiver.
    losses : float
        Transmission signal losses.
    Returns
    -------
    received_power : float
        The received power at the receiver in dB.
    """
    received_power = eirp + receiver_gain - path_loss - losses

    return received_power


def calc_interference(item, int_dist_lut):
    """
    Calculate interference

    """
    cell_id = '{}_{}'.format(item['cell_lon'], item['cell_lat'])

    distances = int_dist_lut.loc[int_dist_lut['cell_id_3857'] == cell_id]

    distances['cell_id_3857'] = distances['cell_id_3857'].drop_duplicates()#.reset_index()

    distances = distances.to_dict('records')[0]

    dist_list = []

    if 'int1_distance_m' in distances.keys():
        dist_list.append(distances['int1_distance_m'])
    if 'int2_distance_m' in distances.keys():
        dist_list.append(distances['int2_distance_m'])
    if 'int3_distance_m' in distances.keys():
        dist_list.append(distances['int3_distance_m'])

    random_variations = generate_log_normal_dist_value(
            8*10**9,#params['dl_frequency'],
            2,#params['mu'],
            10,#params['sigma'],
            42,#params['seed_value'],
            1,#params['iterations']
    )

    interference = []

    for item in dist_list:

        if item > 0:
            path_loss, random_variation = calc_free_space_path_loss(
                        item, 8*10**9, random_variations
                    )

            eirp = 60.5
            received_interference = calc_received_power(eirp, path_loss, 0, 4)

            received_interference = 10**received_interference #anti-log

            interference.append(received_interference)
        else:
            interference.append(10**-120)

    return np.log10((sum(interference)))


def calc_noise():
    """
    Estimates the potential noise.

    Terminal noise can be calculated as:
    “K (Boltzmann constant) x T (290K) x bandwidth”.
    The bandwidth depends on bit rate, which defines the number
    of resource blocks. We assume 50 resource blocks, equal 9 MHz,
    transmission for 1 Mbps downlink.
    Required SNR (dB)
    Detection bandwidth (BW) (Hz)
    k = Boltzmann constant
    T = Temperature (Kelvins) (290 Kelvin = ~16 degrees celcius)
    NF = Receiver noise figure (dB)
    NoiseFloor (dBm) = 10log10(k * T * 1000) + NF + 10log10BW
    NoiseFloor (dBm) = (
        10log10(1.38 x 10e-23 * 290 * 1x10e3) + 1.5 + 10log10(10 x 10e6)
    )

    Parameters
    ----------
    bandwidth : int
        The bandwidth of the carrier frequency (MHz).

    Returns
    -------
    noise : float
        Received noise at the UE receiver in dB.
    """
    k = 1.38e-23 #Boltzmann's constant k = 1.38×10−23 joules per kelvin
    t = 290 #Temperature of the receiver system T0 in kelvins
    b = 0.25 #Detection bandwidth (BW) in Hz

    noise = (10*(math.log10((k*t*1000)))) + (10*(math.log10(b*10**9)))

    return noise


def calc_sinr(received_power, interference, noise):
    """
    Calculate the Signal-to-Interference+Noise Ratio (SINR).

    Returns
    -------
    received_power : float
        The received signal power at the receiver in dB.
    noise : float
        Received noise at the UE receiver in dB.

    Returns
    -------
    cnr : float
        Carrier-to-Noise Ratio (CNR) in dB.
    """
    # sinr = received_power - (interference + noise)

    raw_received_power = 10**received_power
    raw_interference = 10**interference
    raw_noise = 10**noise
    # print(raw_received_power, raw_interference, raw_noise)
    i_plus_n = (raw_interference + raw_noise)

    sinr = round(np.log10(
        raw_received_power / i_plus_n
        ),2)

    return sinr


if __name__ == '__main__':

    crs = 'epsg:4326'
    os.environ['GDAL_DATA'] = ("C:\\Users\edwar\\Anaconda3\\Library\\share\\gdal")
    random.seed(44)

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    technologies = [
        'GSM',
        'UMTS',
        'LTE',
        'NR',
    ]

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        iso3 = country['iso3']
        level = country['lowest']

        print('Working on {}'.format(iso3))

        filename = 'regions_{}_{}.shp'.format(level, iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
        path = os.path.join(folder, filename)
        regions = gpd.read_file(path, crs=crs)#[:1]

        for idx, region in regions.iterrows():

            GID_level = 'GID_{}'.format(level)
            gid_id = region[GID_level]

            if not gid_id == 'GHA.1.12_1':
                continue

            for technology in technologies:

                if not technology == 'GSM':
                    continue

                folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)

                if not os.path.exists(folder_out):
                    os.makedirs(folder_out)

                query_settlement_layers(country, region)

                convert_to_shapes(country, region)

                calculate_distances_lut(country, region, technology)

                calculate_interference_distances_lut(country, region, technology)

                calculate_sinr_lut(country, region, technology)
