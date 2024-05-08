"""
BioBox Node
"""
import requests
import biobox_analytics._setup as _setup
from biobox_analytics.core._concept import Concept
from urllib.parse import quote
import json
class Node:

    def __init__(self, uuid, db_label):
        self.uuid = uuid
        self.db_label = db_label
        bx_data = self._load()

        self._exists = False

        if bx_data is not None:
            self._exists = True
            self._data = bx_data
        else:
            self._data = {
                'uuid': uuid,
                'displayName': 'Node'
            }
        self.concept = Concept.get(db_label)

    @property
    def displayName(self):
        return self._data.get('displayName')

    @displayName.setter
    def displayName(self, v):
        self._data['displayName'] = v

    @property
    def properties(self):
        return self._data['properties']

    @properties.setter
    def properties(self, adict):
        self._data['properties'].update(adict)

    def save(self):
        if self._exists:
            self._update()
        else:
            self._create()

        print(json.dumps(self._data, indent=2))

    def _update(self):
        res = requests.put(
            f"{_setup.BIOBOX_REST_API}/bioref/object/{quote(self.uuid)}",
            json={
                'uuid': self.uuid,
                'displayName': self.displayName
            },
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            }
        )
        res.raise_for_status()
        return res.json()

    def delete(self):
        pass

    def _load(self):
        res = requests.get(
            f"{_setup.BIOBOX_REST_API}/bioref/object/{quote(self.uuid)}",
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            }
        )
        if res.status_code == 200:
            return res.json()

    def _create(self):
        res = requests.post(
            f"{_setup.BIOBOX_REST_API}/bioref/object",
            json={
                'conceptUri': self.concept.uri,
                'payload': [
                    {
                        'uuid': self.uuid,
                        'displayName': self.displayName,
                        'properties': [
                            {
                                'dataPropertyUri': 'uuid',
                                'value': self.uuid
                            },
                            {
                                'dataPropertyUri': 'displayName',
                                'value': self.displayName
                            }
                        ]
                    }
                ]
            },
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            }
        )
        res.raise_for_status()
        return res.json()

    def attach(self, rel, target):
        res = requests.post(
            f"{_setup.BIOBOX_REST_API}/bioref/attach/object",
            json={
                'from': {
                    'uuid': self.uuid
                },
                'to': {
                    'uuid': target
                },
                'label': rel,
                'properties': []
            },
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            }
        )
        if res.status_code != 200:
            print(res.text)
        res.raise_for_status()
        return res.json()
