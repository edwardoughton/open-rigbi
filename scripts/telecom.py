"""
Telecom file. This is heavily in progress. Last updated 21/04/2024
"""

from typing import Dict, List, Union, Optional
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import pandas as pd
import pyproj
import rasterio
from rasterstats import zonal_stats
from shapely.geometry import Polygon, MultiPolygon, Point

class GIDTwo:
    """
    Class representing a geographical area of interest and associated telecom infrastructure.

    Attributes:
        region (gpd.GeoDataFrame): A GeoDataFrame representing the geographical region of interest.
        telecom (Optional[gpd.GeoDataFrame]): A GeoDataFrame representing the existing telecom infrastructure.
        buffer_distance (float): The distance in units to buffer the region.
        centroids (List[Point]): A list to store centroid points of buffered geometries.
        buffer_index (int): Index used for buffering operations.
    """

    def __init__(self, region: gpd.GeoDataFrame, buffer_distance: float = 1, telecom: Optional[gpd.GeoDataFrame] = None) -> None:
        """
        Initialize GIDTwo object with given region and optional telecom infrastructure.

        Args:
            region (gpd.GeoDataFrame): A GeoDataFrame representing the geographical region of interest.
            buffer_distance (float, optional): The distance in units to buffer the region. Defaults to 1.
            telecom (Optional[gpd.GeoDataFrame], optional): A GeoDataFrame representing the existing telecom infrastructure. Defaults to None.
        """
        self.region: gpd.GeoDataFrame = region
        self.telecom: Optional[gpd.GeoDataFrame] = telecom
        self.buffer_distance: float = buffer_distance
        self.centroids: List[Point] = []
        self.buffer_index: int = 0

    def convert_region_to_polygon(self) -> None:
        """
        Convert the region to a Polygon if it's not already in Polygon format.
        """
        coordinate_list: List = []
        for geom in self.region.geometry:
            coordinate_list.extend(list(geom.exterior.coords))
        self.region: Polygon = Polygon(coordinate_list)

    def calculate_and_buffer(self) -> List[Union[Polygon, MultiPolygon, Point]]:
        """
        Calculate buffer geometries for the region.

        Returns:
            List[Union[Polygon, MultiPolygon, Point]]: A list of buffered geometries.
        """
        buffer_geometries: List[Union[Polygon, MultiPolygon, Point]] = []
        self.centroids: List[Point] = []
        
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

    def get_communications_towers(self, state: Optional[str] = None, country: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Retrieve communications towers within the specified region.

        Args:
            state (Optional[str], optional): The state within the country. Defaults to None.
            country (Optional[str], optional): The country of interest. Defaults to None.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing communications towers.

        Note:
            This method is bugged due to the methods requiring pyproj3 but 
            only pyproj2 being available currently within the project environment.

            The code within this method is heavily based upon work done by 
            Dennies Kiprono Bor at George Mason University.
        """
        raise NotImplementedError
    
        tags: Dict[str, str] = {"man_made": "communications_tower"}
        if state:
            area_of_interest: Dict[str, Optional[str]] = {"state": state, "country": country}
        else:
            area_of_interest: Dict[str, Optional[str]] = {"country": country}

        towers: gpd.GeoDataFrame = ox.features_from_place(area_of_interest, tags=tags)

        if towers.empty and state:
            towers: gpd.GeoDataFrame = ox.features_from_place(area_of_interest["country"], tags=tags)

        return towers

    def intersect(self) -> gpd.GeoDataFrame:
        """
        Perform intersection between the telecom infrastructure and the region.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame representing the intersection.
        """
        subset: gpd.GeoDataFrame = self.telecom.overlay(self.region, how='intersection')
        return subset

    
    @staticmethod
    def area_of_polygon(geom: Polygon) -> float:
        """
        Calulate the area of a given polygon.

        Returns the area of a polygon. Assume WGS84 as crs.
        """
        geod: pyproj.Geod = pyproj.Geod(ellps="WGS84")

        poly_area, _ = geod.geometry_area_perimeter(geom)

        return abs(poly_area)


    def get_pop_data(self, country: Dict) -> pd.DataFrame:
        """
        Retrieve regional population and luminosity data for a given country.

        Args:
            country (Dict): Dictionary containing country information including iso3 code and regional level.

        Returns:
            pd.DataFrame: A DataFrame containing regional data including population and area information.

        Note:
            This method requires iso3 codes and magic constants representing data paths.
            As this script has not been fully implemented into open-rigbi, those magic constants
            and codes are placeholders and not implemented into the parsing of this script.

            This function will also require a manual rewrite of the zonal_stats() method
            from rasterstats due to numpy's np.asscalar() being removed.

            Unil this is complete, this method is unusable and will throw an exception.

            The code within this method is adapted from the PyTal library, 
            which was written by Dr. Edward John Oughton and Tom Russel.
        """

        raise NotImplementedError

        iso3: str = country['iso3']
        level: str = country['regional_level']
        gid_level: str = 'GID_{}'.format(level)

        print('----')
        print('Working on population data for {}'.format(iso3))

        path_settlements: str = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements.tif')

        filename: str = 'regions_{}_{}.shp'.format(level, iso3)
        folder: str = os.path.join(DATA_INTERMEDIATE, iso3, 'regions')
        path: str = os.path.join(folder, filename)

        regions: gpd.GeoDataFrame = gpd.read_file(path)

        results: List[Dict[str, float]] = []

        for _, region in regions.iterrows():

            with rasterio.open(path_settlements) as src:

                affine = src.transform
                array = src.read(1)
                array[array <= 0] = 0

                population_summation = [d['sum'] for d in zonal_stats(
                    region['geometry'], array, stats=['sum'], affine=affine)][0]

            area_km2: float = round(self.area_of_polygon(region['geometry']) / 1e6)

            if area_km2 > 0:
                population_km2: float = (
                    population_summation / area_km2 if population_summation else 0)
            else:
                population_km2: float = 0

            results.append({
                'GID_0': region['GID_0'],
                'GID_id': region[gid_level],
                'GID_level': gid_level,
                'population': (population_summation if population_summation else 0),
                'area_km2': area_km2,
                'population_km2': population_km2,
            })

        results_df: pd.DataFrame = pd.DataFrame(results)
        return results_df

    def plot_buffers(self) -> None:
        """
        Plot the region and its buffered geometries.

        This method plots the original region along with its buffered geometries on a Matplotlib plot.
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        
        region_series: gpd.GeoSeries = gpd.GeoSeries(self.region)
        region_series.plot(ax=ax, color='blue', alpha=0.5, label='Region')
        
        buffer_geometries: List[Union[Polygon, MultiPolygon, Point]] = self.calculate_and_buffer()
        num_buffers: int = len(buffer_geometries)
        buffer_colors: np.ndarray = plt.cm.viridis(np.linspace(0, 1, num_buffers))
        
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

if __name__ == "__main__":
    region: gpd.GeoDataFrame = gpd.read_file('~/Downloads/gadm41_LIE_shp/gadm41_LIE_0.shp', crs='epsg:4326')
    gid_two: GIDTwo = GIDTwo(region)
    # gid_two.get_communications_towers(country="Liechtenstein")
    gid_two.region.plot(alpha=0.5, edgecolor='k')
    # inter = gid_two.intersect()
    # inter.plot(alpha=0.5, edgecolor='k')
    plt.show()

