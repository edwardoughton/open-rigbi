"""
Download Aquaduct data.

"""
import os
import configparser
from lxml import html
import requests
import urllib.request
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')


def dl_flood_layers():
    """

    """
    path = 'http://wri-projects.s3.amazonaws.com/AqueductFloodTool/download/v2/index.html'
    page = requests.get(path)
    webpage = html.fromstring(page.content)

    for in_path in tqdm(webpage.xpath('//a/@href')):

        if not in_path.endswith('.tif'):
            continue

        #if not 'inuncoast' in in_path:
        #    continue

        filename = os.path.basename(in_path)

        folder = os.path.join(DATA_RAW, 'flood_hazard')

        if not os.path.exists(folder):
            os.mkdir(folder)

        filename = "{}".format(filename)
        out_path = os.path.join(folder, filename)

        #if not os.path.exists(out_path):

        urllib.request.urlretrieve(in_path, out_path)

    return


def dl_water_mask_layer():
    """

    """

    # filename = os.path.basename(in_path)

    folder = os.path.join(DATA_RAW, 'global_surface_water')

    if not os.path.exists(folder):
        os.mkdir(folder)

    DATASET_NAME = 'occurrence'
    longs = [str(w) + "W" for w in range(180,0,-10)]
    longs.extend([str(e) + "E" for e in range(0,180,10)])
    lats = [str(s) + "S" for s in range(50,0,-10)]
    lats.extend([str(n) + "N" for n in range(0,90,10)])
    fileCount = len(longs)*len(lats)

    counter = 1
    for lng in longs:
        for lat in lats:
            filename = DATASET_NAME + "_" + str(lng) + "_" + str(lat) + "v1_3_2020.tif"

            # if not filename == 'occurrence_30E_10Sv1_3_2020.tif':
            #     continue

            path = os.path.join(folder,  filename)

            if os.path.exists(path):
                print(path + " already exists - skipping")
                continue

            else:
                url = "http://storage.googleapis.com/global-surface-water/downloads2020/" + DATASET_NAME + "/" + filename
                code = urllib.request.urlopen(url).getcode()
            if (code != 404):
                try:
                    print("Downloading " + url + " (" + str(counter) + "/" + str(fileCount) + ")")
                    urllib.request.urlretrieve(url, path)
                except:
                    print("Failed " + url + " (" + str(counter) + "/" + str(fileCount) + ")")
            else:
                print(url + " not found")

            counter += 1


if __name__ == "__main__":

    dl_flood_layers()

    dl_water_mask_layer()
