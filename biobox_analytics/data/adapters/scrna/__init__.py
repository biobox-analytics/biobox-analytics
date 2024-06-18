from biobox_analytics.data.adapters._base import Adapter
# import biobox_analytics.data.adapters.scrna._structs as structs
import json
import os
import gzip
import math
import datetime
import itertools
import scanpy
import pandas as pd

class ScRNAAdapter(Adapter):
    def __init__(
        self,
        h5adFile,
        node_filename='node.jsonl.gz',
        edge_filename='edge.jsonl.gz',
    ):
        super().__init__()
        self.input_file = h5adFile
        self.pull_data()
        self.node_filename = node_filename
        self.edge_filename = edge_filename
        self.current_date_time = str(datetime.datetime.now())
        self.displayName = f"SingleCellRNASeq Datapack - {self.current_date_time}"
        self.description = "SingleCellRNASeq Datapack created through Python SDK"
        self.key = f"scrna:{self.current_date_time}"
        self._cellxgeneedges = []
    
    def pull_data(self):
        self.rna = scanpy.read_h5ad(self.input_file)

    def set_metadata(self, displayName, description, key):
        self.displayName = displayName
        self.description = description
        self.key = key
    
    def create_sample_nodes(self, sample_id_col, sample_cols_to_subset):
        samples = []
        for index, row in self.rna.obs[sample_cols_to_subset].drop_duplicates(subset=sample_id_col).iterrows():
            props = row.to_dict()
            props['displayName'] = row[sample_id_col]
            samples.append({
                "_id": row[sample_id_col],
                "labels": ["Sample"],
                "properties": props
            })
        return samples
    
    def create_sc_experiment_library_nodes(self, sc_library_experiment_id, library_experiment_cols_to_subset):
        experiments = []
        for index, row in self.rna.obs[library_experiment_cols_to_subset].drop_duplicates(subset=sc_library_experiment_id).iterrows():
            props = row.to_dict()
            props['displayName'] = row[sc_library_experiment_id]
            experiments.append({
                "_id": row[sc_library_experiment_id],
                "labels": ["Experiment","SingleCellExperiment","SingleCellRNAseqExperiment"],
                "properties": props
            })
        return experiments
    
    def create_cell_nodes(self, sc_library_experiment_id):
        barcodes = []
        for index, row in self.rna.obs.iterrows():
            barcodes.append({
                "_id": f"{row[sc_library_experiment_id]}:{index}",
                "labels": ["CellBarcode"],
                "properties": {
                    "displayName": f"{row[sc_library_experiment_id]}:{index}"
                }
            })
        return barcodes

    def iterate_nodes(self, write_to_disk=True, sc_library_experiment_id="library_uuid", sample_id_col="sample_uuid", sc_experiment_cols_to_subset=["library_uuid"], sample_metadata_cols_to_subset=["sample_uuid"]):
        if (write_to_disk):
            print(f"Running function in write mode. Writing to file {self.node_filename}. To return nodes, set write_to_disk=False in function call")
            nodes = []
            print(f"Create cell nodes")
            nodes = self.create_cell_nodes(sc_library_experiment_id)
            print(f"Writing {len(nodes)} cell nodes to file")
            self.append_to_file(nodes, filepath=self.node_filename)
            nodes = []
            print(f"Create experiment nodes")
            nodes = self.create_sc_experiment_library_nodes(sc_library_experiment_id, sc_experiment_cols_to_subset)
            print(f"Writing {len(nodes)} experiment nodes to file")
            self.append_to_file(nodes, filepath=self.node_filename)
            if (sample_id_col):
                nodes = []
                print(f"Create sample nodes")
                nodes = self.create_sample_nodes(sample_id_col, sample_metadata_cols_to_subset)
                print(f"Writing {len(nodes)} sample nodes to file")
                self.append_to_file(nodes, filepath=self.node_filename)
                nodes = []
            print(f"All nodes written to file: {self.node_filename}")
        else:
            print("Running function in non-write mode. Returning nodes. To write to file, set write_to_disk=True in function call")
            barcodes = self.create_cell_nodes(sc_library_experiment_id)
            singleCellExperiments = self.create_sc_experiment_library_nodes(sc_library_experiment_id, sc_experiment_cols_to_subset)
            samples = []
            if (sample_id_col):
                samples = self.create_sample_nodes(sample_id_col, sample_metadata_cols_to_subset)
            return list(itertools.chain(*[barcodes, singleCellExperiments, samples]))
    
    def create_sample_to_experiment_connection(self, sc_library_experiment_id, sample_id_col):
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
    
    def create_experiment_to_barcode_connection(self, sc_library_experiment_id):
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
    
    def create_barcode_to_celltype_connection(self, sc_library_experiment_id, celltype_id_col):
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

    def _process_barcodes_genes(self, row, barcode):
        return {
            "from": {
                "uuid": barcode
            },
            "to": {
                "uuid": row.name
            },
            "label": "expresses",
            "properties": {
                "normValue": row[barcode].astype(float)
            }
        }
    
    def _process_barcode(self, column):
        barcode = column.name
        cell = pd.DataFrame(column)
        filtered_cell = cell[cell[column.name] > 0]
        # cell2 = cell.set_axis(['expression'], axis=1)
        a = filtered_cell.apply(lambda row: self._process_barcodes_genes(row, barcode), axis=1)
        self._cellxgeneedges.extend(a.tolist())
    
    def create_barcode_to_gene_connection(self, sc_library_experiment_id):
        numcells = self.rna.X.shape[0]
        print(f"Number of cells to process: {numcells}")
        print(f"Starting Cell x Gene edge processing now: {datetime.datetime.now()}")
        for i in range(math.ceil(self.rna.X.shape[0]/1000)):
            low = i*1000
            high = (i+1)*1000
            if (high > numcells):
                high = numcells
            print(f"Processing batch index {low}:{high} at time {datetime.datetime.now()}")
            library = self.rna.obs[sc_library_experiment_id][low:high]
            cell = self.rna.obs.index[low:high]
            cell_uniq = [f"{libi}:{celli}" for libi, celli in zip(library.tolist(), cell.tolist())]
            rowPandas = pd.DataFrame(self.rna.X[low:high].toarray().T, index=self.rna.var.index, columns=cell_uniq)
            rowPandas.apply(self._process_barcode, axis=0)
            self.append_to_file(self._cellxgeneedges, filepath=self.edge_filename)
            self._cellxgeneedges = []
        print(f"Cell x Gene edges written to file: {self.edge_filename} at time {datetime.datetime.now()}")
        return []

    def iterate_edges(self, write_to_disk=True, sc_library_experiment_id="library_uuid", sample_id_col=None, celltype_id_col=None, tissuetype_id_col=None):
        if (write_to_disk):
            print(f"Running function in write mode. Writing to file {self.edge_filename}. To return edges, set write_to_disk=False in function call")
            edges = []
            print(f"Calculating experiment-cell edges")
            edges = self.create_experiment_to_barcode_connection(sc_library_experiment_id)
            print(f"Writing {len(edges)} experiment-cell edges to file")
            self.append_to_file(edges, filepath=self.edge_filename)
            if sample_id_col != None:
                print(f"Calculating sample-experiment edges")
                edges = self.create_sample_to_experiment_connection(sc_library_experiment_id, sample_id_col)
                print(f"Writing {len(edges)} sample-experiment edges to file")
                self.append_to_file(edges, filepath=self.edge_filename)
                edges = []
            if celltype_id_col != None:
                print(f"Calculating cell-celltype edges")
                edges = self.create_barcode_to_celltype_connection(sc_library_experiment_id, celltype_id_col)
                print(f"Writing {len(edges)} cell-celltype edges to file")
                self.append_to_file(edges, filepath=self.edge_filename)
                edges = []
            print(f"Calculating cell-gene edges")
            self.create_barcode_to_gene_connection(sc_library_experiment_id)
            print(f"All edges written to file: {self.edge_filename}")
        else:
            print("Running function in non-write mode. Returning edges. To write to file, set write_to_disk=True in function call")
            exp_to_barcode_edges = self.create_experiment_to_barcode_connection(sc_library_experiment_id)
            print("Skipping cell-gene edges as the matrix is too large")
            # barcode_to_gene_edges = self.create_barcode_to_gene_connection(sc_library_experiment_id)
            sample_exp_edges = []
            if sample_id_col != None:
                sample_exp_edges = self.create_sample_to_experiment_connection(sc_library_experiment_id, sample_id_col)
            barcode_celltype_edges = []
            if self.enable_celltype_connections:
                barcode_celltype_edges = self.create_barcode_to_celltype_connection(sc_library_experiment_id, celltype_id_col)
            return list(itertools.chain(*[exp_to_barcode_edges, barcode_celltype_edges, sample_exp_edges]))

    def process_item(self, item):
        """Processes a single item (node or edge)."""
        # Customize how you want to process each item, e.g., add extra information, filter, etc.
        return item  # In this example, we just return the item as-is.

    def describe_node_properties(self):
        pass

    def describe_edge_properties(self):
        pass
    
    def list_schema(self):
        metadata = {
            "_meta": {
                "version": "0.0.1",
                "date_updated": self.current_date_time,
            },
            "name": self.displayName,
            "key": self.key, 
            "description": self.description,
            "dependencies": ["Ensembl"],
            "concepts": {
                "Experiment": {
                    "label": "Experiment",
                    "dbLabel": "Experiment",
                    "definition": "Experiment of the sample tissue",
                },
                "SingleCellExperiment": {
                    "label": "SingleCellExperiment",
                    "dbLabel": "SingleCellExperiment",
                    "definition": "Single Cell Experiment of the sample tissue",
                    "sco": "Experiment",
                },
                "SingleCellRNAseqExperiment": {
                    "label": "SingleCellRNAseqExperiment",
                    "dbLabel": "SingleCellRNAseqExperiment",
                    "definition": "Single Cell RNAseq Experiment of the sample tissue",
                    "sco": "SingleCellExperiment",
                },
                "Sample": {
                    "label": "Sample",
                    "dbLabel": "Sample",
                    "definition": "Sample organism from which tissue was taken to be analyzed",
                },
                "CellBarcode": {
                    "label": "Cell Barcode",
                    "dbLabel": "CellBarcode",
                    "definition": "Individual cell from scRNA experiment, identified by barcode",
                }
            },
            "relationships": {
                "contains cell": {
                    "from": "SingleCellExperiment",
                    "to": "CellBarcode"
                },
                "expresses": {
                    "from": "CellBarcode",
                    "to": "Gene"
                },
                "has experiment": {
                    "from": "Sample",
                    "to": "Experiment"
                },
                "has cell type": {
                    "from": "CellBarcode",
                    "to": "CellType"
                },
            }
        }
        return metadata
    
    def append_to_file(self, objs, directory="", filepath="obj.jsonl.gz"):
        with gzip.open(os.path.join(directory, filepath), "at") as f:
            for x in objs:
                json.dump(x, f)
                f.write("\n")

    # def write_serialized_data_to_file(self, directory=""):
    #     node_filepath = os.path.join(directory, self.node_filename)
    #     edge_filepath = os.path.join(directory, self.edge_filename)

    #     with gzip.open(node_filepath, "at") as f:
    #         for x in self.nodes:
    #             json.dump(x, f)
    #             f.write("\n")

    #     with gzip.open(edge_filepath, "at") as f:
    #         for x in self.edges:
    #             json.dump(x, f)
    #             f.write("\n")
