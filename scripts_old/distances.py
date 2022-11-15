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

from misc import params, technologies, get_countries, get_regions, get_scenarios

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')









def cut_settlement_layers(country, region):
    """
    Cut the settlement layer by each regional shape

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
        country['iso3'],
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        'settlements'
    )
    shape_path = os.path.join(folder, 'settlements.tif')

    if os.path.exists(shape_path):
        return

    if not os.path.exists(folder):
        os.makedirs(folder)

    bbox = region['geometry'] #.envelope
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
        country['iso3'],
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

        if region['geometry'].contains(geom_centroid):

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


def write_as_text(country, region):
    """
    Write out points layer as text.

    """
    GID_level = 'GID_{}'.format(country['lowest'])
    gid_id = region[GID_level]

    path_out = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'regional_data',
        gid_id,
        'settlements',
        'points.csv'
    )

    if os.path.exists(path_out):
        return

    path = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'regional_data',
        gid_id,
        'settlements',
        'points.shp'
    )

    data = gpd.read_file(path, crs='epsg:4326')
    data = data.to_crs(3857)

    output = []

    for idx, point in data.iterrows():
        output.append({
            # 'GID_0': item['GID_0'],
            'GID_id': gid_id,
            'GID_level': GID_level,
            'point_value': point['value'],
            'point_id': '{}_{}'.format(
                point['geometry'].coords.xy[0][0],
                point['geometry'].coords.xy[1][0]
            ),
        })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def calculate_distances_lut(country, region, technology):
    """
    Calculate distances.

    """
    path_out = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        '{}_distance_lut.csv'.format(technology)
    )

    if os.path.exists(path_out):
        return

    path_points = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        'settlements',
        'points.shp'
    )

    points = gpd.read_file(path_points, crs='epsg:4326')#[100:101]
    points = points.to_crs(epsg=3857)

    path_sites = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'sites',
        technology,
        '{}_{}.shp'.format(technology, region['GID_{}'.format(country['lowest'])])
    )

    if not os.path.exists(path_sites):
        return

    sites = gpd.read_file(path_sites, crs='epsg:3857')#[:1]
    # sites = sites.to_crs(epsg=3857)

    output = []

    for idx, point in points.iterrows(): #tqdm(points.iterrows(), total=points.shape[0]):

        # ## Get sites within x km of the point (e.g. 20 km)
        point_geom = point['geometry'].buffer(10000)
        point_buffer = gpd.GeoDataFrame(geometry=[point_geom], crs='epsg:3857')
        subset_sites = gpd.overlay(sites, point_buffer, how='intersection')

        # ##
        single_point = gpd.GeoDataFrame(geometry=[point['geometry']], crs='epsg:3857')
        site_distances = subset_sites
        site_distances['distance'] = subset_sites.geometry.apply(lambda g: single_point.distance(g))

        if len(site_distances) >= 1:
            site_distances = site_distances.loc[site_distances['distance'] > 250]
            if len(site_distances) >= 1:
                site_distances = site_distances.sort_values('distance')[:params['number_of_cells']]
            else:
                continue
        else:
            continue

        site_distances = site_distances.reset_index(level=0)

        site1 = site_distances.iloc[[0]]
        site1_distance_m = site1['distance'].values[0]
        site1_id = site1['cell_id'].values[0]

        site2_distance_m = 0
        site2_id = 'N/A'

        site3_distance_m = 0
        site3_id = 'N/A'

        site4_distance_m = 0
        site4_id = 'N/A'

        if len(site_distances) >= 2:
            site2 = site_distances.iloc[[1]]
            site2_distance_m = site2['distance'].values[0]
            site2_id = site2['cell_id'].values[0]

        if len(site_distances) >= 3:
            site3 = site_distances.iloc[[2]]
            site3_distance_m = site3['distance'].values[0]
            site3_id = site3['cell_id'].values[0]

        if len(site_distances) >= 4:
            site4 = site_distances.iloc[[2]]
            site4_distance_m = site4['distance'].values[0]
            site4_id = site4['cell_id'].values[0]

        output.append({
            'point_value': point['value'],
            'point_id': '{}_{}'.format(
                point['geometry'].coords.xy[0][0],
                point['geometry'].coords.xy[1][0]
            ),
            'point_lon': point['geometry'].coords.xy[0][0],
            'point_lat': point['geometry'].coords.xy[1][0],
            'site1_distance_m': site1_distance_m,
            'site1_id': site1_id,
            'site2_distance_m': site2_distance_m,
            'site2_id': site2_id,
            'site3_distance_m': site3_distance_m,
            'site3_id': site3_id,
            'site4_distance_m': site4_distance_m,
            'site4_id': site4_id,
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
        country['iso3'],
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        '{}_sinr_lut.csv'.format(technology)
    )

    if os.path.exists(path_out):
        return

    path_dist_lut = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        '{}_distance_lut.csv'.format(technology)
    )

    if not os.path.exists(path_dist_lut):
        return

    dist_lut = pd.read_csv(path_dist_lut)#[:10]

    output = []

    for idx, item in dist_lut.iterrows(): #tqdm(dist_lut.iterrows(), total=dist_lut.shape[0]):

        dist1 = item['site1_distance_m']
        dist2 = item['site2_distance_m']
        dist3 = item['site3_distance_m']
        dist4 = item['site4_distance_m']

        sinr1 = get_sinr(params, dist1, dist2, dist3, dist4)
        sinr2 = get_sinr(params, dist2, dist3, dist4, dist1)
        if dist3 > 0:
            sinr3 = get_sinr(params, dist3, dist4, dist1, dist2)
        else:
            sinr3 = 0
        if dist4 > 0:
            sinr4 = get_sinr(params, dist4, dist1, dist2, dist3)
        else:
            sinr4 = 0

        output.append({
            # 'radio': item['radio'],
            # 'mcc': item['mcc'],
            # 'net': item['net'],
            # 'area': item['area'],
            # 'cell': item['cell'],
            # 'cell_lon': item['cell_lon'],
            # 'cell_lat': item['cell_lat'],
            'point_value': item['point_value'],
            'point_id': item['point_id'],
            'point_lon': item['point_lon'],
            'point_lat': item['point_lat'],
            'site1_distance_m': item['site1_distance_m'],
            'site1_id': item['site1_id'],
            # 'random_variation_mean': random_variation.mean(),
            # 'path_loss': path_loss,
            # 'antenna_gain': antenna_gain,
            # 'eirp': eirp,
            # 'losses': losses,
            # 'received_power': received_power,
            # 'interference': interference,
            # 'noise': noise,
            'sinr1': sinr1,
            'site2_id': item['site2_id'],
            'sinr2': sinr2,
            'site3_id': item['site3_id'],
            'sinr3': sinr3,
            'site4_id': item['site4_id'],
            'sinr4': sinr4,
        })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def get_sinr(params, dist1, dist2, dist3, dist4):
    """
    Estimate the SINR given the main cell site distance,
    and three interfering cell sites.

    """
    if dist1 == 0:
        return -1

    random_variations = generate_log_normal_dist_value(
        params['dl_frequency'],
        params['mu'],
        params['sigma'],
        params['seed_value'],
        params['iterations']
    )

    eirp = calc_eirp(params['power'], params['antenna_gain'])

    path_loss, random_variation = calc_free_space_path_loss(
        dist1, params['dl_frequency'], random_variations
    )

    losses = calc_losses(params['earth_atmospheric_losses'],
        params['all_other_losses'])

    received_power = calc_received_power(eirp, path_loss,
        params['receiver_gain'], losses)

    interference = calc_interference(params, dist2, dist3, dist4)

    noise = calc_noise(params)

    sinr = calc_sinr(received_power, interference, noise)

    return sinr


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


def calc_interference(params, dist2, dist3, dist4):
    """
    Calculate interference.

    """
    # cell_id = '{}_{}'.format(item['cell_lon'], item['cell_lat'])
    # distances = int_dist_lut.loc[int_dist_lut['cell_id_3857'] == cell_id]
    # distances['cell_id_3857'] = distances['cell_id_3857'].drop_duplicates()#.reset_index()
    # item = item.to_dict('records')#[0]

    dist_list = []

    dist_list.append(dist2)
    dist_list.append(dist3)
    dist_list.append(dist4)

    random_variations = generate_log_normal_dist_value(
            params['dl_frequency'],
            params['mu'],
            params['sigma'],
            params['seed_value'],
            params['iterations']
    )

    interference = []

    for distance in dist_list:

        if distance > 0:
            path_loss, random_variation = calc_free_space_path_loss(
                        distance, params['dl_frequency'], random_variations
                    )

            eirp = calc_eirp(params['power'], params['antenna_gain'])

            losses = calc_losses(params['earth_atmospheric_losses'],
                params['all_other_losses'])

            received_interference = calc_received_power(eirp, path_loss,
                params['receiver_gain'], losses)

            received_interference = 10**received_interference #anti-log

            interference.append(received_interference)
        else:
            interference.append(10**params['minimum_interference'])

    return np.log10((sum(interference)))


def calc_noise(params):
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
    b = params['dl_bandwidth'] #Detection bandwidth (BW) in Hz

    noise = (10*(math.log10((k*t*1000)))) + (10*(math.log10(b)))

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
    raw_received_power = 10**received_power
    raw_interference = 10**interference
    raw_noise = 10**noise

    i_plus_n = (raw_interference + raw_noise)

    sinr = round(np.log10(
        raw_received_power / i_plus_n
        ),2)

    return sinr


def query_hazard_layers(country, region, technology, scenario):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']
    gid_level = 'GID_{}'.format(regional_level)
    gid_id = region[gid_level]
    scenario_name = os.path.basename(scenario)

    filename = 'fragility_curve.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    f_curve = pd.read_csv(path_fragility)
    f_curve = f_curve.to_dict('records')

    filename = '{}_{}_{}.shp'.format(gid_id, technology, scenario_name)
    folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
    path_output = os.path.join(folder_out, filename)

    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    if os.path.exists(path_output):
        return

    filename = '{}_{}.shp'.format(technology, gid_id)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        return

    sites = gpd.read_file(path, crs='epsg:3857')#[:1]
    sites = sites.to_crs(4326)

    output = []

    failures = 0

    for idx, site in sites.iterrows():

        with rasterio.open(scenario) as src:

            src.kwargs = {'nodata':255}

            coords = [(site['geometry'].x, site['geometry'].y)]

            depth = [sample[0] for sample in src.sample(coords)][0]

            fragility = query_fragility_curve(f_curve, depth)

            failure_prob = random.uniform(0, 1)

            failed = (1 if failure_prob < fragility else 0)

            if fragility > 0:
                failures += 1

            output.append({
                'type': 'Feature',
                'geometry': site['geometry'],
                'properties': {
                    'radio': site['radio'],
                    'mcc': site['mcc'],
                    'net': site['net'],
                    'area': site['area'],
                    'cell': site['cell'],
                    'gid_level': gid_level,
                    'gid_id': region[gid_level],
                    'depth': depth,
                    'scenario': scenario_name,
                    'fragility': fragility,
                    'fail_prob': failure_prob,
                    'failure': failed,
                    # 'cell_id': site['cell_id'],
                }
            })

    if len(output) == 0:
        return

    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
    output.to_file(path_output, crs=crs)

    return


def query_fragility_curve(f_curve, depth):
    """
    Query the fragility curve.

    """
    if depth < 0:
        return 0

    for item in f_curve:
        if item['depth_lower_m'] <= depth < item['depth_upper_m']:
            return item['fragility']
        else:
            continue

    print('fragility curve failure: {}'.format(depth))

    return 0


def estimate_coverage(country, region, technology, scenario):
    """
    Estimate population coverage by region.

    """
    iso3 = country['iso3']
    # name = country['country']
    regional_level = country['gid_region']
    gid_level = 'GID_{}'.format(regional_level)
    gid_id = region[gid_level]
    scenario_name = os.path.basename(scenario)

    filename = 'covered_{}_{}_{}.csv'.format(gid_id, technology, scenario_name)
    folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
    path_covered = os.path.join(folder_out, filename)
    filename = 'uncovered_{}_{}_{}.csv'.format(gid_id, technology, scenario_name)
    path_uncovered = os.path.join(folder_out, filename)
    # if os.path.exists(path_output):
    #     continue

    filename = '{}_sinr_lut.csv'.format(technology)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)
    path_in = os.path.join(folder, filename)
    if not os.path.exists(path_in):
        return
    sinr_lut = pd.read_csv(path_in)

    filename = '{}_{}_{}.shp'.format(gid_id, technology, scenario_name)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
    path_in = os.path.join(folder, filename)
    if not os.path.exists(path_in):
        return
    sites = gpd.read_file(path_in, crs='epsg:4326')
    sites = sites.to_crs(3857)
    sites = sites.loc[sites['failure'] == 1]
    sites = sites.to_dict('records')

    failed_sites = []

    for item in sites:

        cell_id = '{}_{}'.format(
            int(round(item['geometry'].coords[0][0])),
            int(round(item['geometry'].coords[0][1])),
        )

        failed_sites.append(cell_id)

    # failed_sites_csv = pd.DataFrame(failed_sites)
    # failed_path = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology, 'failed.csv')
    # failed_sites_csv.to_csv(failed_path, index=False)

    covered = []
    uncovered = []

    for idx, item in sinr_lut.iterrows():

        pop = {
            'point_id': item['point_id'],
            'population': item['point_value'],
        }

        lon = int(round(float(item['site1_id'].split('_')[0])))
        lat = int(round(float(item['site1_id'].split('_')[1])))
        site1_id = '{}_{}'.format(lon, lat)

        if item['point_value'] < 0:
            continue

        if item['sinr1'] < params['functioning_sinr']:
            uncovered.append(pop)
            continue

        if site1_id in failed_sites:

            site2_id = '{}_{}'.format(
                int(round(float(item['site1_id'].split('_')[0]))),
                int(round(float(item['site1_id'].split('_')[1])))
            )

            if item['sinr2'] < params['functioning_sinr'] or site2_id in failed_sites:
                uncovered.append(pop)
            else:
                covered.append(pop)
        else:
            covered.append(pop)

    if not len(covered) > 0:
        return

    covered = pd.DataFrame(covered)
    covered.to_csv(path_covered, index=False)

    if not len(uncovered) > 0:
        return

    uncovered = pd.DataFrame(uncovered)
    uncovered.to_csv(path_uncovered, index=False)

    return


def write_out_baseline_tile_coverage(country, technologies):
    """
    Write out site failures to .csv.
    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:1]

    for technology in tqdm(technologies):

        # if not technology == 'NR':
        #     continue

        output = []

        filename = 'baseline_tile_coverage_{}.csv'.format(technology)
        folder_out = os.path.join(DATA_PROCESSED, iso3)
        if not os.path.exists(folder_out):
            os.mkdir(folder_out)
        path_output = os.path.join(folder_out, filename)

        # if os.path.exists(path_output):
        #     continue

        for idx, item in tqdm(regional_data.iterrows(), total=regional_data.shape[0]):

            gid_id = item['GID_id']
            area_km2 = item['area_km2']
            population_total = item['population_total']

            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'settlements')
            path_in = os.path.join(folder, 'points.shp')
            tile_points = gpd.read_file(path_in, crs='epsg:4326')
            tile_points = tile_points.to_crs(3857)

            filename = '{}_sinr_lut.csv'.format(technology)
            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)
            path_in = os.path.join(folder, filename)

            if not os.path.exists(path_in):
                continue

            sinr_lut = pd.read_csv(path_in)

            covered_population = 0

            for idx, tile_point in tile_points.iterrows():

                point_id1 = '{}_{}'.format(
                        round(tile_point['geometry'].coords.xy[0][0],5),
                        round(tile_point['geometry'].coords.xy[1][0],5)
                    )

                for idx, tile in sinr_lut.iterrows():

                    point_id2 = '{}_{}'.format(
                        round(tile['point_lon'],5),
                        round(tile['point_lat'],5)
                    )

                    if point_id1 == point_id2:

                        point_value = float(tile['point_value'])
                        if point_value < 0:
                            point_value = 0
                        if float(tile['sinr1']) > params['functioning_sinr']:
                            covered = 1
                        else:
                            covered = 0

                        output.append({
                            'GID_0': item['GID_0'],
                            'GID_id': item['GID_id'],
                            'GID_level': item['GID_level'],
                            'population_km2': point_value,
                            'technology': technology,
                            'covered': covered,
                            'sinr1': tile['sinr1'],
                            'tile_point': tile_point,
                            'sinr_point': point_id2
                        })

        if not len(output) > 0:
            return

        output = pd.DataFrame(output)
        output.to_csv(path_output, index=False)

    return


def write_out_baseline_coverage(country, scenarios, technologies):
    """
    Write out site failures to .csv.
    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'baseline_coverage.csv'
    folder_out = os.path.join(DATA_PROCESSED, iso3)
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)
    path_output = os.path.join(folder_out, filename)

    if os.path.exists(path_output):
        return

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:1]

    output = []

    for technology in technologies:

        for idx, item in regional_data.iterrows():

            gid_id = item['GID_id']
            area_km2 = item['area_km2']
            population_total = item['population_total']

            filename = '{}_sinr_lut.csv'.format(technology)
            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)
            path_in = os.path.join(folder, filename)

            if not os.path.exists(path_in):
                continue

            sinr_lut = gpd.read_file(path_in, crs='epsg:4326')

            covered_population = 0

            for idx, tile in sinr_lut.iterrows():
                if float(tile['point_value']) > 0:
                    if float(tile['sinr1']) > params['functioning_sinr']:
                        covered_population += float(tile['point_value'])

            output.append({
                'GID_0': item['GID_0'],
                'GID_id': item['GID_id'],
                'GID_level': item['GID_level'],
                'population_total': item['population_total'],
                'area_km2': item['area_km2'],
                'population_km2': item['population_km2'],
                'technology': technology,
                'covered_pop': covered_population,
                'covered_pop_perc': round((covered_population / item['population_total'])*100),
                'uncovered_pop': item['population_total'] - covered_population,
                'uncovered_pop_perc': round((
                    (item['population_total'] - covered_population) /
                    item['population_total'])*100),
            })

    if not len(output) > 0:
        return

    output = pd.DataFrame(output)
    output.to_csv(path_output, index=False)

    return


def write_out_site_failures(country, scenarios, technologies):
    """
    Write out site failures to .csv.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:5]

    for scenario in tqdm(scenarios):

        scenario_name = os.path.basename(scenario)

        for technology in technologies:

            output = []

            for idx, item in regional_data.iterrows():

                gid_id = item['GID_id']
                area_km2 = item['area_km2']
                population_total = item['population_total']

                filename = '{}_{}_{}.shp'.format(gid_id, technology, scenario_name)
                folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
                path_in = os.path.join(folder, filename)

                if not os.path.exists(path_in):
                    continue

                sites = gpd.read_file(path_in, crs='epsg:4326')

                for idx, site in sites.iterrows():

                    output.append({
                        'GID_0': item['GID_0'],
                        'GID_id': item['GID_id'],
                        'GID_level': item['GID_level'],
                        'scenario': site['scenario'],
                        'technology': site['radio'],
                        'depth': site['depth'],
                        'fragility': site['fragility'],
                        'fail_prob': site['fail_prob'],
                        'failure': site['failure'],
                        'lon': site['geometry'].x,
                        'lat': site['geometry'].y,
                    })

            if not len(output) > 0:
                return

            output = pd.DataFrame(output)

            filename = 'sites_{}_{}.csv'.format(technology, scenario_name)
            folder_out = os.path.join(DATA_PROCESSED, iso3, 'failed_sites')
            if not os.path.exists(folder_out):
                os.mkdir(folder_out)
            path_output = os.path.join(folder_out, filename)

            output.to_csv(path_output, index=False)

    return


def write_out_tiles_served_by_failures(country, scenarios, technologies):
    """
    Write out site failures to .csv.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    # filename = 'regional_data.csv'
    # folder = os.path.join(DATA_PROCESSED, iso3)
    # path = os.path.join(folder, filename)
    # regional_data = pd.read_csv(path)#[:1]

    for scenario in tqdm(scenarios):

        # if not scenario == 'data\processed\GHA\hazards\inuncoast_rcp8p5_wtsub_2080_rp1000_0_perc_50.tif':
        #     continue

        scenario_name = os.path.basename(scenario)

        print('--Working on {}'.format(scenario_name))

        for technology in technologies:

            output = []

            filename = 'sites_{}_{}.csv'.format(technology, scenario_name)
            folder_in = os.path.join(DATA_PROCESSED, iso3, 'failed_sites')
            path_in = os.path.join(folder_in, filename)
            if not os.path.exists(path_in):
                continue
            failed_sites = gpd.read_file(path_in, crs='epsg:4326')
            failed_sites = failed_sites.loc[failed_sites['failure'] == '1']
            if len(failed_sites) == 0:
                print('--no failed sites {}, {}'.format(technology, scenario_name))
                continue
            # print('----{}'.format(len(failed_sites)))

            for idx, failed_site in failed_sites.iterrows():

                gid_id = failed_site['GID_id']

                geom = Point(float(failed_site['lon']), float(failed_site['lat']))
                geom = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326", index=[0])
                geom = geom.to_crs(3857)
                geom = geom.to_dict('records')[0]

                cell_id1 = '{}_{}'.format(
                    int(round(geom['geometry'].coords[0][0],5)),
                    int(round(geom['geometry'].coords[0][1],5)),
                )

                # if not gid_id == 'GHA.9.7_1': #'GHA.1.1_1':#: #'GHA.1.12_1':
                #     continue

                filename = '{}_sinr_lut.csv'.format(technology)
                folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)
                path_in = os.path.join(folder, filename)
                if not os.path.exists(path_in):
                    continue
                sinr_lut = pd.read_csv(path_in)

                for idx, tile in sinr_lut.iterrows():

                    cell_id2 = '{}_{}'.format(
                        int(round(float(tile['site1_id'].split('_')[0]),5)),
                        int(round(float(tile['site1_id'].split('_')[1]),5))
                    )

                    if cell_id1 == cell_id2:
                        # print(cell_id1, cell_id2)
                        point_value = tile['point_value']
                        if tile['point_value'] < 0:
                            point_value = 0
                        output.append({
                            # 'point_id': tile['point_id'],
                            'pop_covered': 1,
                            'population': point_value,
                            'pop_density_km': point_value,
                            'technology': technology,
                            'scenario': scenario_name,
                        })

            if not len(output) > 0:
                return

            output = pd.DataFrame(output)

            filename = 'pop_affected_by_failures_{}_{}.csv'.format(technology, scenario_name)
            folder_out = os.path.join(DATA_PROCESSED, iso3, 'failed_sites', 'coverage')
            if not os.path.exists(folder_out):
                os.mkdir(folder_out)
            path_output = os.path.join(folder_out, filename)

            output.to_csv(path_output, index=False)

    return


if __name__ == '__main__':

    crs = 'epsg:4326'
    os.environ['GDAL_DATA'] = ("C:\\Users\edwar\\Anaconda3\\Library\\share\\gdal")
    random.seed(params['seed_value'])

    countries = get_countries()

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'MWI':
            continue

        scenarios  = get_scenarios(country)

        regions = get_regions(country)

        for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

            GID_level = 'GID_{}'.format(country['lowest'])
            gid_id = region[GID_level]

            if not gid_id == 'MWI.1.1_1': #'GHA.9.7_1': #:#: #'GHA.1.12_1':
                continue

            cut_settlement_layers(country, region) # Cut settlement layers by region

            # convert_to_shapes(country, region) # Convert settlement layers to points

            # write_as_text(country, region) # Write out points as .csv

            # for technology in technologies:

            #     # if not technology == 'GSM':
            #     #     continue

            #     folder_out = os.path.join(DATA_PROCESSED, country['iso3'], 'regional_data', gid_id)

            #     if not os.path.exists(folder_out):
            #         os.makedirs(folder_out)

            #     calculate_distances_lut(country, region, technology)

            #     calculate_sinr_lut(country, region, technology)

        #         for scenario in scenarios:

        #             # if not scenario == 'data\processed\GHA\hazards\inuncoast_rcp8p5_wtsub_2080_rp1000_0_perc_50.tif':
        #             #     continue

        #             query_hazard_layers(country, region, technology, scenario)

        #             estimate_coverage(country, region, technology, scenario)

        # write_out_baseline_tile_coverage(country, technologies)

        # write_out_baseline_coverage(country, scenarios, technologies)

        # write_out_site_failures(country, scenarios, technologies)

        # write_out_tiles_served_by_failures(country, scenarios, technologies)
