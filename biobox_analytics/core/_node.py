"""
BioBox Node
"""
import requests
import biobox_analytics._setup as _setup
from biobox_analytics.core._concept import Concept
from biobox_analytics.core._relationship_group import RelationshipGroup
from urllib.parse import quote
import json
    
class Node:
    @classmethod
    def search_by_name(cls, searchtext, limit=50, offset=0):
        if (limit > 100):
            print("Limit cannot be larger than 100. Use offset to find other objects");
            return
        res = requests.post(
            f"{_setup.BIOBOX_REST_API}/bioref/object/searchbyname",
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            },
            json={
                'displayName': searchtext,
                'limit': limit,
                'offset': offset,
            }
        )

        res.raise_for_status()

        data = res.json()

        print(f"Found {data['total']} objects matching search text. Returning {limit} objects.")
        objs = []

        # print(data['data'])
        for o in data['data']:
            item = Node(uuid=o["uuid"], db_label=None, concept_labels=o['dbLabels'],properties=o['properties'], enable_loading=False)
            objs.append(item)
        return objs

    def __init__(self, uuid, db_label=None, concept_labels=None, properties=None, enable_loading=True):
        self.uuid = uuid
        self._loaded = False
        self._relationships = []
        if db_label != None:
            self.db_label = db_label
        elif (concept_labels != None):
            if 'CellLine' in concept_labels:
                self.db_label = 'CellLine'
            elif 'CellType' in concept_labels:
                self.db_label = 'CellType'
            elif 'Disease' in concept_labels:
                self.db_label = 'Disease'
            elif 'EFO' in concept_labels:
                self.db_label = 'EFO'
            elif 'Gene' in concept_labels:
                self.db_label = 'Gene'
            elif 'Pathway' in concept_labels:
                self.db_label = 'Pathway'
            elif 'Phenotype' in concept_labels:
                self.db_label = 'Phenotype'
            elif 'Protein' in concept_labels:
                self.db_label = 'Protein'
            elif 'Tissue' in concept_labels:
                self.db_label = 'Tissue'
            else:
                self.db_label = 'Object'
        else:
            self.db_label = 'Object'
        self._exists = False

        if (properties != None):
            self._data = properties
            self._exists = True
        elif(enable_loading):
            bx_data = self._load(self.uuid)
            self._loaded = True
            if bx_data is not None:
                self._exists = True
                self._data = bx_data
            else:
                self._data = {
                    'uuid': uuid,
                    'displayName': 'Node'
                }
            if 'relationshipMetadata' in self._data.keys():
                self._relationships = self._data['relationshipMetadata']
                self.__generate_relationship_methods()
        # if concept_labels != None:
        #     self.concept = concept_labels
        # else:
        #     self.concept = Concept.get(db_label)

    def __create_relationship_method(self, name, relationship):
        return RelationshipGroup(name, relationship, self.uuid)

    def __generate_relationship_methods(self):
        for relationship in self._relationships:
            direction = 'inbound'
            if (relationship['outbound'] == True):
                direction = 'outbound'
            rel_name = relationship['relationship']['label'].replace(" ", "_") + "_" + direction
            setattr(self, rel_name, self.__create_relationship_method(rel_name, relationship))

    def __getattr__(self, name):
        attribute = super().__getattribute__(name)
        if callable(attribute):
            return attribute
        else:
            return attribute.metadata

    @property
    def relationshipGroups(self):
        rels = []
        for rel in self._relationships:
            direction = "inbound"
            if (rel["outbound"] == True):
                direction = "outbound"
            r = {
                "label": "associated with",
                "directionality": direction,
                "count": rel["total"],
                "attribute": rel['relationship']['label'].replace(" ", "_") + "_" + direction
            }
            rels.append(r)
        return rels

    def __repr__(self):
        itemLoaded = "Loaded from API"
        if (self._loaded == False):
            itemLoaded = "Item not loaded from API. Call ._load(<node>.uuid) to fetch all relationships"
        return json.dumps({
            "uuid": self.uuid,
            "displayName": self.displayName,
            "itemLoaded": itemLoaded,
            "properties": self.properties,
            "relationships": self.relationshipGroups
        })

    @property
    def displayName(self):
        return self._data.get('displayName')

    @displayName.setter
    def displayName(self, v):
        self._data['displayName'] = v

    @property
    def properties(self):
        return self._data

    @properties.setter
    def properties(self, adict):
        print("setting properties")
        self._data['properties'].update(adict)

    def save(self):
        if self._exists:
            self._update()
        else:
            self._create()
            self._exists = True

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

    def _load(self, uuid):
        res = requests.get(
            f"{_setup.BIOBOX_REST_API}/bioref/object/{quote(uuid)}",
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