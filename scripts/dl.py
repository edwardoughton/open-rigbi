"""
Download Aquaduct data.

"""
import os
from lxml import html
import requests
import urllib.request
from tqdm import tqdm

path = 'http://wri-projects.s3.amazonaws.com/AqueductFloodTool/download/v2/index.html'
page = requests.get(path)
webpage = html.fromstring(page.content)

for in_path in tqdm(webpage.xpath('//a/@href')):

    if not in_path.endswith('.tif'):
        continue

    # if 'wtsub' in in_path:
    #     continue

    filename = os.path.basename(in_path)

    out_path = "data/raw/hazard_scenarios/{}".format(filename)

    if not os.path.exists(out_path):

        urllib.request.urlretrieve(in_path, out_path)
