"""
BioBox Relationship
"""
import requests
import biobox_analytics._setup as _setup
from biobox_analytics.core._concept import Concept
from urllib.parse import quote

class RelationshipGroup:
    def __init__(self, name, relationshipGroup, objUUID):
        self._objectID = objUUID
        self._name = name
        self._relationship = relationshipGroup['relationship']
        self._directionality = 'outbound'
        self._count = relationshipGroup.get('total')
        self._dbLabelToMatch = relationshipGroup['relationship']['range'][0]['dbLabel']
        if relationshipGroup['outbound'] == False:
            self._directionality = 'inbound'
            self._dbLabelToMatch = relationshipGroup['relationship']['domain'][0]['dbLabel']

    def __call__(self, limit=10, offset=0):
        return self.fetch(limit, offset)

    def __repr__(self):
        return f"Relationship '{self._relationship['label']}' on object '{self._objectID}' containing {self._count} connections."
    
    @property
    def metadata(self):
        return {
            "objUUID": self._objectID,
            "name": self._name,
            "directionality": self._directionality,
            "count": self._count,
            "dbLabelToMatch": self._dbLabelToMatch
        }
    
    def fetchAll(self, limit=10):
        if (limit < 1):
            print("Limit must be greater than 1")
            return
        currentOffset = 0
        result = []
        while (currentOffset < self._count):
            result.extend(self.fetch(limit=limit, offset=currentOffset))
            currentOffset += limit
        return result
    
    def fetch(self, limit=10, offset=0):
        res = requests.post(
            f"{_setup.BIOBOX_REST_API}/bioref/object/{quote(self._objectID)}/relationship",
            headers={
                'x-biobox-orgid': _setup.BIOBOX_ORGID,
                'Authorization': f'Bearer {_setup.BIOBOX_TOKEN}'
            },
            json={
                'dbLabel': self._dbLabelToMatch,
                'directionality':  self._directionality,
                'limit': limit,
                'offset': offset,
                'relationshipLabel': self._relationship['label']
            }
        )
        if res.status_code == 200:
            jsonResponse = res.json()
            edge_and_node = []
            for edge in jsonResponse['data']:
                obj = self._formatEdgeResponse(edge)
                edge_and_node.append(obj)
            return edge_and_node
                
    def _formatEdgeResponse(self, response):
        edgeId = response['elementId']
        edgeLabel = response['relationship']['label']
        edgeProperties = response['properties']
        if self._directionality == 'outbound':
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
    