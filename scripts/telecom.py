"""
Telecom file. This is heavily in progress. Last updated 13/04/2024
"""

import geopandas as gpd
import matplotlib.pylab as plt
from shapely.geometry import Polygon
import osmnx as ox

class GIDTwo:
    def __init__(self, region, telecom=None):
        self.region = region
        self.telecom = telecom
        
    def convert_region_to_polygon(self):
        coordinate_list = []
        for geom in self.region.geometry:
            coordinate_list.extend(list(geom.exterior.coords))
        self.region = Polygon(coordinate_list)

    def get_communications_towers(self, state=None, country=None):
        tags = {"man_made": "communications_tower"}
        if state:
            area_of_interest = {"state": state, "country": country}
        else:
            area_of_interest = {"country": country}

        towers = ox.features_from_place(area_of_interest, tags=tags)

        if towers.empty and state:
            towers = ox.features_from_place(area_of_interest["country"], tags=tags)

        return towers

    def intersect(self):
        subset = self.telecom.overlay(self.region, how='intersection')
        return subset
        

gdf = gpd.read_file('~/Downloads/gadm41_LIE_shp/gadm41_LIE_0.shp', crs='epsg:4326')
print(gdf.to_string)
gid = GIDTwo(gdf)
gid.get_communications_towers(country="Liechtenstein")

gid.region.plot(alpha=0.5, edgecolor='k')
inter = gid.intersect()
inter.plot(alpha=0.5, edgecolor='k')
plt.show()

