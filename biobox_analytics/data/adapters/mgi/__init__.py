from io import StringIO
import requests
import pandas as pd


def fetch_rpt(url: str, headers: list = None) -> pd.DataFrame:
    """
    Fetch a tab-separated file from a given URL, filter out lines starting with '#', and return the content as a pandas DataFrame.

    Parameters:
    url (str): The URL of the file to be fetched.
    headers (list, optional): A list of strings to use as column headers. If not provided, the DataFrame will have default integer column headers.

    Returns:
    pd.DataFrame: A pandas DataFrame containing the filtered content of the file.

    Raises:
    requests.exceptions.RequestException: If the request to the URL fails.
    ValueError: If the content of the response is empty or cannot be parsed into a DataFrame.
    """

    try:
        # Send a GET request
        response = requests.get(url)

        # If the GET request is successful, the status code will be 200
        response.raise_for_status()

        # Get the content of the response
        content = response.text

        if not content:
            raise ValueError("The content of the response is empty.")

        # Filter out the lines that start with '#'
        filtered_content = '\n'.join([line for line in content.split('\n') if not line.startswith('#')])

        # Convert the filtered content into a file-like object
        file_like_object = StringIO(filtered_content)

        # Read the file-like object into a pandas dataframe
        if headers:
            df = pd.read_csv(file_like_object, sep='\t', header=None, names=headers)
        else:
            df = pd.read_csv(file_like_object, sep='\t', header=None)

        return df

    except requests.exceptions.RequestException as e:
        print(f"Request to {url} failed: {e}")
        raise
    except ValueError as e:
        print(f"Error parsing content from {url}: {e}")
        raise
