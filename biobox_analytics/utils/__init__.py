import os
import json
from tqdm import tqdm

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