"""
Generate an ISO3 code to pass to each node.

Written by Ed Oughton.

August 2022.

"""
import os
import sys
import configparser
import pandas as pd

# sys.path.insert(0, sys.path[0] + '\\..\\scripts\\')
# from misc import get_countries, get_scenarios, get_regions


if __name__ == "__main__":

    countries = ['IRL', 'GBR', 'USA']

    # countries = get_countries()
    # scenarios = get_scenarios()

    # for idx, country in countries.iterrows():

    #     # if not country['iso3'] in ['IRL']:
    #     #     continue

    #     print('-- {}'.format(country['iso3']))
    # print(countries)

    print(*countries, sep='\n')
