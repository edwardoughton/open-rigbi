import requests
import os
from bs4 import BeautifulSoup
"""
url_list = [
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp1000_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2030_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2080_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00100-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0025_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2080_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0500_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_MIROC-ESM-CHEM_2050_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_hist_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2080_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2050_rp00500-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2080_rp0100_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2080_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2030_rp0050_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2050_rp01000-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2080_rp0005_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0250_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000HadGEM2-ES_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_0000GFDL-ESM2M_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_historical_wtsub_2050_rp0002_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2030_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000HadGEM2-ES_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00IPSL-CM5A-LR_2030_rp00002-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2030_rp00250-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00000NorESM1-M_2030_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2080_rp00025-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00050-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp8p5_00IPSL-CM5A-LR_2050_rp00010-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2050_rp0010_0-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_0000GFDL-ESM2M_2030_rp00005-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inuncoast_rcp4p5_wtsub_2050_rp0001_5-afg.tif",
    "https://irv-autopkg.s3.eu-west-2.amazonaws.com/afg/datasets/wri_aqueduct/version_2/data/wri_aqueduct-version_2-inunriver_rcp4p5_00000NorESM1-M_2080_rp00010-afg.tif"
]
query_parameters = {"downloadformat": "tif"}

def download_files(url_list, iso3, download_dir='/home/tcc/Downloads'):
    # Create the base download directory if it does not exist
    base_dir = os.path.join(download_dir, iso3, "flood_layer", "wri_aqueduct.version_2")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    for idx, url in enumerate(url_list):
        print(f"Downloading file {idx + 1} from URL: {url}")
        response = requests.get(url, params=query_parameters)
        
        if response.status_code == 200:
            filename = url.split('/')[-1]
            filepath = os.path.join(base_dir, filename)
            
            with open(filepath, "wb") as file:
                file.write(response.content)
            print(f"Saved to {filepath}")
        else:
            print(f"Failed to download file {idx + 1} from URL: {url}")
"""

import os
import requests

query_parameters = {"downloadformat": "tif"}

def get_areas():
    areas = []
    url = 'https://global.infrastructureresilience.org/extract/v1/boundaries'
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        
        for area in data:
            areas.append(area['name'])
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred while fetching areas: {http_err}')
    except Exception as err:
        print(f'Other error occurred while fetching areas: {err}')
    
    return areas

def get_filelist(area):
    url = f'https://global.infrastructureresilience.org/extract/v1/packages/{area}'
    downloadset = []
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        
        for resource in data['datapackage']['resources']:
            if resource['name'] == 'wri_aqueduct':
                downloadset = resource['path']
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred while fetching file list for {area}: {http_err}')
    except KeyError as key_err:
        print(f'Missing key in response data for {area}: {key_err}')
    except Exception as err:
        print(f'Other error occurred while fetching file list for {area}: {err}')
    
    return downloadset

def download_files(url_list, iso3, download_dir='/home/tcc/Downloads'):
    # Create the base download directory if it does not exist
    base_dir = os.path.join(download_dir, iso3, "flood_layer", "wri_aqueduct.version_2")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    for idx, url in enumerate(url_list):
        print(f"Downloading file {idx + 1} from URL: {url}")
        response = requests.get(url, params=query_parameters)
        
        if response.status_code == 200:
            filename = url.split('/')[-1]
            filepath = os.path.join(base_dir, filename)
            
            with open(filepath, "wb") as file:
                file.write(response.content)
            print(f"Saved to {filepath}")
        else:
            print(f"Failed to download file {idx + 1} from URL: {url}")

def main():
    countries = get_areas()
    
    for country in countries:
        print(f'Now processing: {country}')
        
        try:
            country_dataset = get_filelist(country)
            
            if country_dataset:
                download_files(country_dataset, country)
            else:
                print(f'No files found for {country}')
        
        except Exception as e:
            print(f'Error processing {country}: {e}')
            continue  # Continue to the next country

if __name__ == "__main__":
    main()

"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# aqueduct.py file for FloodRisk, designed to visalize risk to telecom
# infrastructure due to flooding. This file downloads the aqueduct repository data.
#
# SPDX-FileCopyrightText: Tom Russel <tom.russel@ouce.ox.ac.uk>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by Tom Russel and lightly modified by Aryaman Rajaputra

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

"""