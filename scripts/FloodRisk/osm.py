import geopandas as gpd
import requests
from shapely import Point

from typing import Optional

def get_telecom_features(self) -> Optional[gpd.GeoDataFrame]:
    """
    Fetch telecom features data for the specified country from the Overpass API.

    Returns:
        Optional[gpd.GeoDataFrame]: GeoDataFrame containing telecom features or None if the request fails.
    """
    print(f"Fetching telecom features data for country: {self.iso2}")
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    area["ISO3166-1"="{self.iso2}"]->.searchArea;
    (
    nwr["telecom"](area.searchArea);
    );
    out center;
    """

    response = requests.get(overpass_url, params={'data': overpass_query})

    if response.status_code == 200:
        data = response.json()

        features = []
        for element in data['elements']:
            if 'lat' in element and 'lon' in element:
                lon = element['lon']
                lat = element['lat']
                point = Point(lon, lat)
                tags = element.get('tags', {})
                features.append({'geometry': point, 'tags': tags})

        gdf = gpd.GeoDataFrame(features, columns=['geometry', 'tags'])

        gdf.set_crs('EPSG:4326', inplace=True)
        print("Telecom features data fetched successfully.")
        return gdf
    else:
        print("Error fetching telecom features data. Status code:", response.status_code)
        return None