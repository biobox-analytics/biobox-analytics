"""
BioBox Concept
"""

import requests
import biobox_analytics._setup as _setup
from urllib.parse import quote
class Concept:

    @classmethod
    def get(cls, db_label):
        res = requests.get(
            f"{_setup.BIOBOX_REST_API}/bioref/concept/{db_label}",
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            }
        )

        res.raise_for_status()

        data = res.json()

        return cls(data)

    def __init__(self, data):
        self._data = data

    @property
    def uri(self):
        return self._data.get('uri')

