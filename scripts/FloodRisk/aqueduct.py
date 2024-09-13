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

def download_files(url_list, iso3, download_dir='/home/cisc/projects/open-rigbi/scripts/FloodRisk/data'):
    # Create the base download directory if it does not exist
    base_dir = os.path.join(download_dir, "flood_layer", iso3, "wri_aqueduct.version_2")
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
