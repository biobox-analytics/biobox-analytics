"""
BioBox Relationship
"""
import requests
import biobox_analytics._setup as _setup
from biobox_analytics.core._concept import Concept
from urllib.parse import quote
import json

class Relationship:
    def __init__(self, name, relationshipGroup, objUUID):
        self.objectID = objUUID
        self.name = name
        self.metadata = relationshipGroup['relationship']
        self.directionality = 'outbound'
        self.count =relationshipGroup.get('total')
        if relationshipGroup['outbound'] == False:
            self.directionality = 'inbound'

    def __call__(self, limit=10, offset=0):
        return self.fetch(limit, offset)

    def __repr__(self):
        return f"{self.name}: {self.metadata}"
    
    def fetch(self, limit=10, offset=0):
        res = requests.post(
            f"{_setup.BIOBOX_REST_API}/bioref/object/{quote(self.objectID)}/relationship",
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            },
            json={
                'dbLabel': self.metadata['domain'][0]['dbLabel'],
                'directionality':  self.directionality,
                'limit': limit,
                'offset': offset,
                'relationshipLabel': self.metadata['label']
            }
        )
        if res.status_code == 200:
            jsonResponse = res.json()
            edge_and_node = []
            for edge in jsonResponse['data']:
                obj = self.formatEdgeResponse(edge)
                edge_and_node.append(obj)
            return edge_and_node
                
    def formatEdgeResponse(self, response):
        edgeId = response['elementId']
        edgeLabel = response['relationship']['label']
        edgeProperties = response['properties']
        if self.directionality == 'outbound':
            nodeProperties = response['endNode']
        else:
            nodeProperties = response['startNode']
        return {
            "edge": {
                "elementId": edgeId,
                "label": edgeLabel,
                "properties": edgeProperties
            },
            "node": nodeProperties
        }
    