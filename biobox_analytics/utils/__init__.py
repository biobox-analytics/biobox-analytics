import os
import json
from tqdm import tqdm
import requests
from concurrent.futures import ThreadPoolExecutor
import io
import gzip

def setup_working_directories(base_path):
    tmp_data = os.path.join(base_path, 'tmp_data')
    processed_data = os.path.join(base_path, 'processed_data')

    os.makedirs(tmp_data, exist_ok=True)
    os.makedirs(processed_data, exist_ok=True)

def ensure_primitive_or_array_of_primitives(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    elif isinstance(value, list):
        return [ensure_primitive_or_array_of_primitives(v) for v in value]
    else:
        return json.dumps(value)


def read_jsonl_files(directory):
    """
    Recursively reads all .jsonl files in a directory and its subdirectories.

    Args:
        directory (str): The path to the directory to scan for .jsonl files.

    Returns:
        list: A list of dictionaries, where each dictionary represents the contents of a .jsonl file.
    """
    data = []  # Initialize an empty list to store the data
    jsonl_files = []  # Initialize an empty list to store the .jsonl files
    
    # Find all .jsonl files in the directory and its subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".jsonl") or file.endswith(".json"):
                jsonl_files.append(os.path.join(root, file))
    
    # Read the contents of each .jsonl file
    for file_path in tqdm(jsonl_files, desc="Loading .jsonl files"):
        with open(file_path, 'r') as f:
            # Read the file line by line
            for line in f:
                # Parse each line as JSON and add it to the data list
                data.append(json.loads(line))
    
    return data

def download_gzipped_json(uri):
    # Send a GET request to the URI
    response = requests.get(uri)

    # Check if the response was successful
    if response.status_code != 200:
        raise Exception(f"Failed to download file from {uri}")

    # Create a BytesIO object to hold the gzipped data
    gzipped_data = io.BytesIO(response.content)

    # Create a GzipFile object to decompress the data
    with gzip.GzipFile(fileobj=gzipped_data, mode='rb') as f:
        # Read the decompressed data into a string
        json_data = f.read().decode('utf-8')

    # Parse the JSON data into a Python object
    data = json.loads(json_data)

    return data


def oxo_mapping(ids, target_ontologies):
    url = "https://www.ebi.ac.uk/spot/oxo/api/search"
    json_body = {
        'ids': ids,
        'mappingTarget': target_ontologies,
        'distance': 3
    }
    initial_request = requests.post(
        url=url,
        json=json_body
    )
    initial_request.raise_for_status()
    data = initial_request.json()
    total_pages = data.get('page', {}).get('totalPages')
    results = {}
    for i in tqdm(range(total_pages)):
        res = requests.post(
            url=url,
            json=json_body
        )
        data = res.json()
        mappings = data.get('_embedded', {}).get('searchResults', [])

        for m in mappings:
            mappingResponseList = m.get('mappingResponseList', [])
            if len(mappingResponseList) == 0:
                results[m.get('queryId')] = None
            else:
                mapping_prioritized = sorted(mappingResponseList,
                                             key=lambda x: (x['targetPrefix'] != 'EFO', x['distance']))
                results[m.get('queryId')] = [x.get('curie') for x in mapping_prioritized]

        next_url = data.get('_links', {}).get('next', {}).get('href')
        if next_url is None:
            break
        else:
            url = next_url
    return results



def scrape_page(url, page, limit):
    """
    Scrape a single page of records from the API.

    Args:
        url (str): The URL of the API endpoint.
        page (int): The page number to scrape.
        limit (int): The number of records per page.

    Returns:
        list: A list of records from the specified page.
    """
    params = {'page': page, 'limit': limit}
    response = requests.get(url, params=params)
    data = response.json()
    return data['results']

def scrape_all_records(url, limit=20, max_workers=10):
    """
    Scrape all records from the API.

    Args:
        url (str): The URL of the API endpoint.
        limit (int, optional): The number of records per page. Defaults to 20.
        max_workers (int, optional): The maximum number of concurrent requests. Defaults to 10.

    Returns:
        list: A list of all records from the API.
    """
    response = requests.get(url, params={'page': 1, 'limit': limit})
    data = response.json()
    total_pages = -(-data['total'] // limit)  # ceiling division

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(scrape_page, url, page, limit) for page in range(1, total_pages + 1)]
        all_records = [record for future in futures for record in future.result()]

    return all_records