"""
Download Aquaduct data.

"""
import os
import configparser
from lxml import html
import requests
import urllib.request
from urllib.parse import urljoin
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.abspath(os.path.join(BASE_PATH, '..', '..', 'data_raw'))


def dl_flood_layers():
    """
    Download WRI Aqueduct flooding layers.
    """
    path = 'https://aqueduct.wridata.org/AqueductFloods20/index.html'
    page = requests.get(path)
    page.raise_for_status()
    webpage = html.fromstring(page.content)

    for in_path in tqdm(webpage.xpath('//a/@href')):

        if not in_path.endswith('.tif'):
            continue

        # if not 'inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00250' in in_path:
        #     continue

        filename = os.path.basename(in_path)

        folder = os.path.join(DATA_RAW, 'flood_hazard')

        if not os.path.exists(folder):
            os.mkdir(folder)

        filename = "{}".format(filename)
        out_path = os.path.join(folder, filename)

        if not os.path.exists(out_path):
            download_url = urljoin(path, in_path)
            urllib.request.urlretrieve(download_url, out_path)

    return


if __name__ == "__main__":

    os.makedirs(DATA_RAW, exist_ok=True)

    dl_flood_layers()


