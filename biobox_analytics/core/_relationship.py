"""
BioBox Relationship
"""
import requests
import biobox_analytics._setup as _setup
from biobox_analytics.core._concept import Concept
from urllib.parse import quote
import json

class Relationship:
    def __init__(self, name, metadata, call_function):
        self.name = name
        self.metadata = metadata
        self.fetch = call_function

    def __call__(self, limit=10, offset=0):
        return self.call_function(limit, offset)

    def __repr__(self):
        return f"{self.name}: {self.metadata}"