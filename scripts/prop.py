"""
Propagation functions.

Written by Ed Oughton.

April 5th 2022.

"""
import numpy as np
import math


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
