import json
from abc import ABC, abstractmethod


class Adapter(ABC):
    """
    Abstract base class for an Adapter pattern that processes nodes and edges.

    This class defines a standard interface for pulling data, iterating over nodes
    and edges, processing items, and describing node and edge properties. Subclasses
    should implement the abstract methods to provide specific functionality.
    """

    def __init__(self) -> None:
        """Initialize the Adapter."""
        pass

    def get_nodes(self):
        """
        Iterate over nodes and process each item.

        This method uses `iterate_nodes` to retrieve nodes and processes each node
        using the `process_item` method, then prints the processed result.
        """
        for x in self.iterate_nodes():
            print(self.process_item(x))

    def get_edges(self):
        """
        Iterate over edges and process each item.

        This method uses `iterate_edges` to retrieve edges and processes each edge
        using the `process_item` method, then prints the processed result.
        """
        for x in self.iterate_edges():
            print(self.process_item(x))

    def init(self):
        """Initialize the Adapter. This method can be overridden by subclasses if needed."""
        pass

    def describe(self):
        """
        Describe the properties of nodes and edges.

        This method retrieves descriptions of node and edge properties using
        `describe_node_properties` and `describe_edge_properties` methods and prints
        them as a JSON string.
        """
        node_props = self.describe_node_properties()
        edge_props = self.describe_edge_properties()
        print(json.dumps({"node": node_props, "edge": edge_props}))

    @abstractmethod
    def pull_data(self):
        """Pull data from a data source. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def iterate_nodes(self):
        """Iterate over nodes. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def iterate_edges(self):
        """Iterate over edges. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def process_item(self, item):
        """
        Process a single item (node or edge).

        Parameters:
            item: The item to be processed.

        Returns:
            The processed item.
        """
        pass

    @abstractmethod
    def describe_node_properties(self):
        """
        Describe properties of nodes.

        Returns:
            A description of the node properties.
        """
        pass

    @abstractmethod
    def describe_edge_properties(self):
        """
        Describe properties of edges.

        Returns:
            A description of the edge properties.
        """
        pass
