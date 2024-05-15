import os

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