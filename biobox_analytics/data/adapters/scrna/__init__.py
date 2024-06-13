from biobox_analytics.data.adapters._base import Adapter
# import biobox_analytics.data.adapters.scrna._structs as structs
import json
import requests
import os
import gzip
import math
from gtfparse import read_gtf
import urllib.request
from datetime import datetime
import math
import itertools
import scanpy
import pandas as pd

class ScRNA(Adapter):
    def __init__(
        self,
        h5adFile,
        node_filename='node.jsonl.gz',
        edge_filename='edge.jsonl.gz',
        
    ):
        super().__init__()
        self.rna = scanpy.read_h5ad(h5adFile)
        self.node_filename = node_filename
        self.edge_filename = edge_filename
        self.enableCellTypeConnections = True
        self.enableTissueTypeConnections = True
        self.enableSampleMetadata = True
        self._cellxgeneedges = []
    
    def pull_data(self):
        return super().pull_data()
    
    def create_sample_nodes(self, sample_id_col, sample_cols_to_subset):
        samples = []
        for index, row in self.rna.obs[sample_cols_to_subset].drop_duplicates(subset=sample_id_col).iterrows():
            samples.append({
                "_id": row[sample_id_col],
                "labels": ["Sample"],
                "properties": row.to_dict()
            })
        return samples
    
    def create_sc_experiment_library_nodes(self, sc_library_experiment_id, library_experiment_cols_to_subset):
        experiments = []
        for index, row in self.rna.obs[library_experiment_cols_to_subset].drop_duplicates(subset=sc_library_experiment_id).iterrows():
            experiments.append({
                "_id": row[sc_library_experiment_id],
                "labels": ["SingleCellRNAseqExperiment"],
                "properties": row.to_dict()
            })
        return experiments
    
    def create_cell_nodes(self, sc_library_experiment_id):
        barcodes = []
        for index, row in self.rna.obs.iterrows():
            barcodes.append({
                "_id": f"{row[sc_library_experiment_id]}:{index}",
                "labels": ["CellBarcode"],
                "properties": {}
            })
        return barcodes

    def iterate_nodes(self, sc_library_experiment_id="library_uuid", sample_id_col="sample_uuid", sc_experiment_cols_to_subset=["library_uuid"], sample_metadata_cols_to_subset=["sample_uuid"]):
        barcodes = self.create_cell_nodes(sc_library_experiment_id)
        singleCellExperiments = self.create_sc_experiment_library_nodes(sc_library_experiment_id, sc_experiment_cols_to_subset)
        samples = []
        if (self.enableSampleMetadata):
            samples = self.create_sample_nodes(sample_id_col, sample_metadata_cols_to_subset)
        return list(itertools.chain([barcodes, singleCellExperiments, samples]))
    
    def createSampleToExperimentConnection(self, sc_library_experiment_id, sample_id_col):
        edges = []
        for index, row in self.rna.obs.drop_duplicates(subset=sc_library_experiment_id).iterrows():
            edges.append({
                "from": {
                    "uuid": row[sample_id_col]
                },
                "to": {
                    "uuid": row[sc_library_experiment_id]
                },
                "label": "has experiment"
            })
        return edges
    
    def createExperimentToBarcodeConnection(self, sc_library_experiment_id):
        edges = []
        for index, row in self.rna.obs.iterrows():
            edges.append({
                "from": {
                    "uuid": row[sc_library_experiment_id]
                },
                "to": {
                    "uuid": f"{row[sc_library_experiment_id]}:{index}"
                },
                "label": "contains cell"
            })
        return edges
    
    def createBarcodeToCellTypeConnection(self, sc_library_experiment_id, celltype_id_col):
        edges = []
        for index, row in self.rna.obs.iterrows():
            edges.append({
                "from": {
                    "uuid": f"{row[sc_library_experiment_id]}:{index}"
                },
                "to": {
                    "uuid": row[celltype_id_col]
                },
                "label": "has cell type"
            })
        return edges

    def _process_barcodes_genes(row, barcode):
        return {
            "from": {
                "uuid": barcode
            },
            "to": {
                "uuid": row.name
            },
            "label": "expresses",
            "properties": {
                "normValue": row['expression']
            }
        }
    
    def _process_barcode(self, column, library):
        barcode = column.name + ":" + library
        cell = pd.DataFrame(column)
        filtered_cell = cell[cell[column.name] > 0]
        # cell2 = cell.set_axis(['expression'], axis=1)
        a = filtered_cell.apply(lambda row: self._process_barcodes_genes(row, barcode), axis=1)
        self._cellxgeneedges.extend(a.tolist())
    
    def createBarcodeToGeneConnection(self, sc_library_experiment_id):
        numcells = self.rna.X.shape[0]
        print(f"Number of cells to process: {numcells}")
        print(f"Starting Cell x Gene edge processing now: {datetime.datetime.now()}")
        for i in range(math.ceil(self.rna.X.shape[0]/1000)):
            low = i*1000
            high = (i+1)*1000
            if (high > numcells):
                high = numcells
            print(f"Processing batch index {low}:{high}")
            library = self.rna.obs[sc_library_experiment_id][low:high]
            cell = self.rna.obs.index[low:high]
            cell_uniq = [f"{libi}:{celli}" for libi, celli in zip(library.tolist(), cell.tolist())]
            rowPandas = pd.DataFrame(self.rna.X[low:high].toarray().T, index=self.rna.var.index, columns=cell_uniq)
            rowPandas.apply(self._process_barcode, axis=0)
            self.append_to_file(self._cellxgeneedges, filepath=self.edge_filename)
            self._cellxgeneedges = []
        print(f"Cell x Gene edges written to file: {self.edge_filename}")
        return []

    def iterate_edges(self, sc_library_experiment_id="library_uuid", sample_id_col="sample_uuid", celltype_id_col="cell_type"):
        expToBarcodeEdges = self.createExperimentToBarcodeConnection(sc_library_experiment_id)
        barcodeToGeneEdges = self.createBarcodeToGeneConnection(sc_library_experiment_id)
        sampleExpEdges = []
        if self.enableSampleMetadata:
            sampleExpEdges = self.createSampleToExperimentConnection(sc_library_experiment_id, sample_id_col)
        barcodeCellTypeEdges = []
        if self.enableCellTypeConnections:
            barcodeCellTypeEdges = self.createBarcodeToCellTypeConnection(sc_library_experiment_id, celltype_id_col)
        
        return list(itertools.chain([expToBarcodeEdges, barcodeToGeneEdges, barcodeCellTypeEdges, sampleExpEdges]))

    def process_item(self, item):
        """Processes a single item (node or edge)."""
        # Customize how you want to process each item, e.g., add extra information, filter, etc.
        return item  # In this example, we just return the item as-is.

    def describe_node_properties(self):
        pass

    def describe_edge_properties(self):
        pass
    
    def list_schema(self):
        return None
    
    def append_to_file(self, objs, directory="", filepath="obj.jsonl.gz"):
        with gzip.open(os.path.join(directory, filepath), "at") as f:
            for x in objs:
                json.dump(x, f)
                f.write("\n")

    def write_serialized_data_to_file(self, directory=""):
        node_filepath = os.path.join(directory, self.node_filename)
        edge_filepath = os.path.join(directory, self.edge_filename)

        with gzip.open(node_filepath, "at") as f:
            for x in self.nodes:
                json.dump(x, f)
                f.write("\n")

        with gzip.open(edge_filepath, "at") as f:
            for x in self.edges:
                json.dump(x, f)
                f.write("\n")
