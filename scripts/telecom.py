"""
Telecom file. This is heavily in progress. Last updated 21/04/2024
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
from shapely.geometry import Polygon, MultiPolygon, Point

class GIDTwo:
    """Class for handling geographic information and plotting buffers."""

    def __init__(self, region, buffer_distance=1, telecom=None):
        """
        Initialize GIDTwo object.

        Parameters:
        - region (shapely.geometry.Polygon or shapely.geometry.MultiPolygon): The region of interest.
        - buffer_distance (float): The buffer distance around the region.
        - telecom (optional): Telecommunications data.
        """
        self.region = region
        self.telecom = telecom
        self.buffer_distance = buffer_distance
        self.centroids = []
        self.buffer_index = 0
        
    def convert_region_to_polygon(self):
        """
        Convert region to Polygon.

        This function converts the region to a Polygon.
        """
        coordinate_list = []
        for geom in self.region.geometry:
            coordinate_list.extend(list(geom.exterior.coords))
        self.region = Polygon(coordinate_list)
    
    def calculate_and_buffer(self):
        """
        Calculate and buffer the region.

        Returns:
        - list: List of buffered geometries.
        """
        buffer_geometries = []
        self.centroids = []
        
        if self.region.geom_type == 'Point':
            buffer_geometries.append(self.region.buffer(self.buffer_distance))
            self.centroids.append(self.region)

        elif self.region.geom_type == 'MultiPoint':
            for point in self.region:
                buffer_geometries.append(point.buffer(self.buffer_distance))
                self.centroids.append(point)

        elif self.region.geom_type == 'Polygon':
            for point in self.region.exterior.coords:
                buffer_geometry = Point(point).buffer(self.buffer_distance)
                buffer_geometries.append(buffer_geometry)
                self.centroids.append(buffer_geometry.centroid)

        elif self.region.geom_type == 'GeometryCollection':
            for geom in self.region:
                if geom.geom_type == 'Point':
                    buffer_geometries.append(geom.buffer(self.buffer_distance))
                    self.centroids.append(geom)
        
        return buffer_geometries
    
    def get_communications_towers(self, state=None, country=None):
        """
        Return the communications towers data for a given country.
        This method is bugged due to the methods requiring pyproj3 but
        only pyproj2 being available currently within the project environment.
        
        The code within this method is heavily based upon work done by 
        Dennies Kiprono Bor at George Mason University.
        """
        raise NotImplementedError
    
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
        """Return the set of points within intersection boundaries of the given regions."""
        subset = self.telecom.overlay(self.region, how='intersection')
        return subset

    def plot_buffers(self):
        """Plot the region and its buffers."""
        fig, ax = plt.subplots(figsize=(10, 10))
        
        region_series = gpd.GeoSeries(self.region)
        region_series.plot(ax=ax, color='blue', alpha=0.5, label='Region')
        
        buffer_geometries = self.calculate_and_buffer()
        num_buffers = len(buffer_geometries)
        buffer_colors = plt.cm.viridis(np.linspace(0, 1, num_buffers))
        
        for idx, (buffer_geometry, centroid, buffer_color) in enumerate(zip(buffer_geometries, self.centroids, buffer_colors)):
            if isinstance(buffer_geometry, Polygon):
                gpd.GeoSeries(buffer_geometry).plot(ax=ax, color=buffer_color, alpha=0.5)
                ax.plot(centroid.x, centroid.y, 'o', color=buffer_color, alpha=0.8, markersize=10, label=f'Polygon {idx + 1} Centroid')
            elif isinstance(buffer_geometry, MultiPolygon):
                for polygon in buffer_geometry:
                    gpd.GeoSeries(polygon).plot(ax=ax, color=buffer_color, alpha=0.5)
                    ax.plot(centroid.x, centroid.y, 'o', color=buffer_color, alpha=0.8, markersize=10, label=f'Polygon {idx + 1} Centroid')
            elif isinstance(buffer_geometry, Point):
                gpd.GeoSeries(buffer_geometry).plot(ax=ax, color=buffer_color, alpha=0.8, marker='o', markersize=10)
        
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Region and Buffers')
        plt.grid(True)
        plt.axis('equal')
        
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc='upper right')
        
        text_annotation = ax.annotate('', xy=(0.5, 0.5), xytext=(0, 10),
                                      textcoords='offset points', ha='center',
                                      bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                                      fontsize=10)
        text_annotation.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                x, y = event.xdata, event.ydata
                text_annotation.set_text(f'x={x:.2f}, y={y:.2f}')
                text_annotation.set_position((x, y))
                text_annotation.set_visible(True)
                fig.canvas.draw_idle()
            else:
                text_annotation.set_visible(False)

        fig.canvas.mpl_connect('motion_notify_event', hover)

        plt.show()

region = gpd.read_file('~/Downloads/gadm41_LIE_shp/gadm41_LIE_0.shp', crs='epsg:4326')
gid_two = GIDTwo(region)
gid_two.get_communications_towers(country="Liechtenstein")

"""
df = gpd.read_file('~/Downloads/gadm41_LIE_shp/gadm41_LIE_0.shp', crs='epsg:4326')
print(gdf.to_string)
gid = GIDTwo(gdf)
gid.get_communications_towers(country="Liechtenstein")

gid.region.plot(alpha=0.5, edgecolor='k')
inter = gid.intersect()
inter.plot(alpha=0.5, edgecolor='k')
plt.show()
"""

