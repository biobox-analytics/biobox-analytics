from _base import Adapter
from pydantic import BaseModel, Field, PrivateAttr


class ChipSeqAdapter(Adapter, BaseModel):
    target: str = Field(..., description="The target sequence")
    target_modification: str = Field(..., description="The modification of the target")
    donor: str = Field(..., description="The donor sequence")
    sample: str = Field(..., description="The sample information")

    # Use PrivateAttr for internal data storage
    _data: dict = PrivateAttr(default={})

    def __init__(self, **data):
        super().__init__()
        BaseModel.__init__(self, **data)

    def pull_data(self):
        """
        Simulates pulling Chip-Seq data (replace with actual data retrieval logic).
        """
        self._data = {  # Use _data to store data internally
            "nodes": [
                {"id": "peak1", "target": self.target, "modification": self.target_modification},
                {"id": "peak2", "target": self.target, "modification": self.target_modification},
            ],
            "edges": [
                {"source": "peak1", "target": "peak2", "interaction": "colocalization"},
            ]
        }

    def iterate_nodes(self):
        """Iterates over the nodes in the pulled data."""
        for node in self._data["nodes"]:  # Access _data internally
            yield node

    def iterate_edges(self):
        """Iterates over the edges in the pulled data."""
        for edge in self._data["edges"]:  # Access _data internally
            yield edge

    def process_item(self, item):
        """Processes a single item (node or edge)."""
        # Customize how you want to process each item, e.g., add extra information, filter, etc.
        return item  # In this example, we just return the item as-is.

    def describe_node_properties(self):
        """Describes the properties of nodes."""
        return {
            "id": "string (unique identifier)",
            "target": "string (target sequence)",
            "modification": "string (target modification)"
        }

    def describe_edge_properties(self):
        """Describes the properties of edges."""
        return {
            "source": "string (source node ID)",
            "target": "string (target node ID)",
            "interaction": "string (type of interaction)"
        }
