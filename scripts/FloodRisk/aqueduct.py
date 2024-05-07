#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# aqueduct.py file for FloodRisk, designed to visalize risk to telecom
# infrastructure due to flooding. This file downloads the aqueduct repository data.
#
# SPDX-FileCopyrightText: Thomas Russel <tom.russel@ouce.ox.ac.uk>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by name


import irv_autopkg_client

import time
from pathlib import Path

data_folder = Path('./data')

country_iso = (input("Enter the country's 3 letter ISO code.: ")).lower().strip()

client = irv_autopkg_client.Client()

job_id = client.job_submit(country_iso, ["wri_aqueduct.version_2"])

while not client.job_complete(job_id):
    print("Processing...")
    time.sleep(1)

client.extract_download(
    country_iso,
    data_folder / "flood_layer",
    dataset_filter=["wri_aqueduct.version_2"],
    overwrite=True,
)

