from biobox_analytics.data.adapters._base import Adapter
import _structs as structs
import rdflib
import json
import requests


class GoAdapter(Adapter):
    def pull_data(self):
        pass

    def iterate_nodes(self):
        pass

    def iterate_edges(self):
        pass

    def process_item(self, item):
        """Processes a single item (node or edge)."""
        # Customize how you want to process each item, e.g., add extra information, filter, etc.
        return item  # In this example, we just return the item as-is.

    def describe_node_properties(self):
        pass

    def describe_edge_properties(self):
        pass
