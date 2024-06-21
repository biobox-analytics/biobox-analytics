from biobox_analytics.data.adapters._base import Adapter
# import biobox_analytics.data.adapters.chipseq._structs as structs
import pandas as pd
import math
import gzip
import os
import json
import datetime
from nanoid import generate

class ChipSeqAdapter(Adapter):
    def __init__(
        self,
        name: str,
        protein_id: str,
        modification_type: str,
        sample_id: str,
        bed_filepath: str,
        taxon_id: str = "9601",
        objects_file: str = "objs.jsonl.gz",
        edges_file: str = "edges.jsonl.gz",
    ):
        super().__init__()
        self.name = name
        self.protein_id = protein_id
        self.modification_type = modification_type
        self.sample_id = sample_id
        self.bed_filepath = bed_filepath
        self.taxon_id = taxon_id
        self.objects_file = objects_file
        self.edges_file = edges_file
        
        self.chipseq_id = generate()

        self.nodes = []
        self.edges = []

    def pull_data(self):
        self.df = pd.read_csv(self.bed_filepath, sep="\t", header=None)
    
    def iterate_nodes(self):
        return self.df.iterrows()
    
    def iterate_edges(self):
        return super().iterate_edges()
    
    def process_item(self, item):
        chr = item.get(0).removeprefix("chr")
        chrom_start = item.get(1)
        chrom_end = item.get(2)
        name = item.get(3)
        score = item.get(4)
        strand = item.get(5)
        signal_value = item.get(6)
        p_value = item.get(7)
        q_value = item.get(8)
        peak = item.get(9)

        narrow_peak_id = self.bed_filepath.removesuffix(".bed") + "-" + name
        labels = [ "NarrowPeak" ]
        properties = {
            "chr": chr,
            "chrom_start": chrom_start,
            "chrom_end": chrom_end,
            # "name": name,
            "score": score,
            "strand": strand,
            "signal_value": signal_value,
            "p_value": p_value,
            "q_value": q_value,
            "peak": peak
        }

        node_narrow_peak = {
            "_id": narrow_peak_id,
            "labels": labels,
            "properties": properties
        }

        edge_has_narrow_peak = {
            "label": "has narrow peak",
            "from": {
                "uuid": self.chipseq_id
            },
            "to": {
                "uuid": narrow_peak_id
            }
        }

        range_start = math.floor(chrom_start / 1000) * 1000
        edge_peak_start_on = {
            "label": "peak start on",
            "from": {
                "uuid": narrow_peak_id
            },
            "to": {
                "uuid": "{}:{}:{}:{}".format(self.taxon_id, chr, range_start + 1, range_start + 1000)
            }
        }

        range_end = math.floor(chrom_end / 1000) * 1000
        edge_peak_end_on = {
            "label": "peak end on",
            "from": {
                "uuid": narrow_peak_id
            },
            "to": {
                "uuid": "{}:{}:{}:{}".format(self.taxon_id, chr, range_end + 1, range_end + 1000)
            }
        }


        return [
            node_narrow_peak,
            edge_has_narrow_peak,
            edge_peak_start_on,
            edge_peak_end_on,
        ]
    
    def describe_node_properties(self):
        return super().describe_node_properties()
    
    def describe_edge_properties(self):
        return super().describe_edge_properties()
    
    def extra_items(self):
        chipseq = {
            "_id": self.chipseq_id,
            "labels": [ "ChIPseq" ],
            "properties": {
                "uuid": self.chipseq_id,
                "displayName": self.name
            }
        }

        chipseq_to_protein = {
            "label": "assay target on",
            "from": {
                "uuid": self.chipseq_id
            },
            "to": {
                "uuid": self.protein_id
            },
            "properties": {
                "modification_type": self.modification_type
            }
        }
        
        sample_to_chipseq = {
            "label": "has chipseq",
            "from": {
                "uuid": self.sample_id
            },
            "to": {
                "uuid": self.chipseq_id
            },
            # "properties": {
            # }
        }

        return [
            chipseq,
            chipseq_to_protein,
            sample_to_chipseq
        ]
    
    def build(self):
        self.pull_data()
        iterator = self.iterate_nodes()
        for object in self.extra_items():
            print(object)

        for _, row in iterator:
            objects = self.process_item(row)
            for object in objects:
                print(object)
                # if "from" in object:
                #     self.edges.append(object)
                # else:
                #     self.nodes.append(object)

    def write(self):
        obs_file = os.path.join("", self.objects_file)
        edges_file = os.path.join("", self.edges_file)
        with gzip.open(obs_file, "at") as o, gzip.open(edges_file, "at") as e:
            self.pull_data()
            iterator = self.iterate_nodes()
            for object in self.extra_items():
                # print(object)
                if "from" in object:
                    json.dump(object, e)
                    e.write("\n")
                else:
                    json.dump(object, o)
                    o.write("\n")

            for _, row in iterator:
                objects = self.process_item(row)
                for object in objects:
                    # print(object)
                    if "from" in object:
                        json.dump(object, e)
                        e.write("\n")
                    else:
                        json.dump(object, o)
                        o.write("\n")

    def list_schema(self):
        metadata = {
            "_meta": {
                "version": "0.0.1",
                "date_updated": str(datetime.datetime.now()),
            },
            "name": self.name,
            "key": self.name, 
            "description": "",
            "concepts": {
                "NarrowPeak": {
                    "label": "NarrowPeak",
                    "dbLabel": "NarrowPeak",
                    "definition": "",
                },
                "ChIPseq": {
                    "label": "ChIPseq",
                    "dbLabel": "ChIPseq",
                    "definition": "",
                },
            },
            "relationships": {
                "has narrow peak": {
                    "from": "ChIPseq",
                    "to": "NarrowPeak"
                },
                "peak start on": {
                    "from": "NarrowPeak",
                    "to": "GenomicInterval"
                },
                "peak end on": {
                    "from": "NarrowPeak",
                    "to": "GenomicInterval"
                },
                "assay target on": {
                    "from": "ChIPseq",
                    "to": "Protein"
                },
                "has chipseq": {
                    "from": "Sample",
                    "to": "ChIPseq"
                }
            }
        }
        return metadata
