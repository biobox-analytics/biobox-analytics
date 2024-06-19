from biobox_analytics.data.adapters._base import Adapter
import biobox_analytics.data.adapters.genome._structs as structs
import json
import requests
import os
import gzip
import math
from gtfparse import read_gtf
import urllib.request
import datetime
import itertools

class GenomeAdapter(Adapter):
    def __init__(self, species='homo sapiens', node_filename='node.jsonl.gz', edge_filename='edge.jsonl.gz' ):
        super().__init__()
        self.species = species
        self.assembly = ""
        self.karyotypes = ""
        self.chromosome_regions = []
        self.nodes = []
        self.edges = []
        self.node_filename = node_filename
        self.edge_filename = edge_filename
        self.current_date_time = str(datetime.datetime.now())
        self._gtfloaded = False
        self.taxon = self.__get_taxonid()
        self.__get_ensembl_assembly_info()
        self.displayName = f"Genome Datapack - {self.species} {self.taxon} ({self.current_date_time})"
        self.description = "Genome Datapack created through Python SDK"
        self.key = f"genome:{self.taxon}:{self.current_date_time}"
        # dateCreated = str(datetime.now().isoformat())
        self.genome = structs.Genome(
            uuid=f"genome_{self.assembly}",
            displayName=f"{self.species} - {self.assembly}",
            species=self.species,
            taxon=self.taxon,
            # dateCreated=dateCreated,
            assembly=self.assembly
        )

    def __get_taxonid(self):
        species = self.species
        # curl request the species name here: curl "https://www.ebi.ac.uk/ena/taxonomy/rest/scientific-name/Leptonycteris%20nivalis"
        url = "https://www.ebi.ac.uk/ena/taxonomy/rest/scientific-name/" + species.replace(" ","%20")
        r = requests.get(url)
        r.json()
        if len(r.json()) == 1:
            return int(r.json()[0]['taxId'])
        else:
            print('Taxon not found on species ' + self.species + ' at link ' + url)
            return None

    def __get_ensembl_assembly_info(self, primary_assembly_only=False):
        species = self.species
        server = "https://rest.ensembl.org"
        ext = "/info/assembly/" + species.replace(" ","_")  + "?"
         
        r = requests.get(server+ext, headers={ "Content-Type" : "application/json"})
                  
        decoded = r.json()
        if ('error' in decoded):
            print("Error when fetching ensembl assembly info. " + decoded['error'])
        else:
            self.assembly = decoded['assembly_name']
            self.karyotypes = decoded['karyotype']
            chromosomes = []
            if (primary_assembly_only):
                for chrom in decoded['top_level_region']:
                    if (chrom['coord_system'] == "chromosome"):
                        chromosomes.append(chrom)
            else:
                chromosomes = decoded['top_level_region']
            self.chromosome_regions = chromosomes
                
    def pull_data(self, gtf_url=None):
        if (gtf_url != None):
            url = gtf_url
        elif (self.taxon == 9606):
            url = "https://ftp.ensembl.org/pub/release-112/gtf/homo_sapiens/Homo_sapiens.GRCh38.112.gtf.gz"
        elif (self.taxon == 10090):
            url = "https://ftp.ensembl.org/pub/release-112/gtf/mus_musculus/Mus_musculus.GRCm39.112.gtf.gz"
        else:
            print("Taxon id was not found and gtf_url was not provided")
            return
        
        urllib.request.urlretrieve(url, 'genome.gtf.gz')

    def _generate_genomic_interval_nodes(self):
        genomicIntervals = []
        for chrom in self.chromosome_regions:
            maxCoord = math.ceil(chrom['length']/1000)
            for i in range(maxCoord):
                start = (i*1000) + 1
                # In order to make the end more predictable, the uuid will use (i+1)*1000
                if (i+1)==(maxCoord):
                    end = chrom['length']
                else:
                    end = (i+1)*1000
                genomicIntervals.append({
                    "_id": f"{self.taxon}:{chrom['name']}:{start}-{(i+1)*1000}",
                    "labels": ["GenomicInterval"],
                    "properties": {
                        "uuid": f"{self.taxon}:{chrom['name']}:{start}-{end}",
                        "displayName": f"{self.species} {chrom['name']}:{start}-{end}",
                        "taxon": self.taxon,
                        "species": self.species,
                        # "assembly": decoded['assembly_name'],
                        "chr": chrom['name'],
                        "start": start,
                        "end": end,
                    }
                })
                # chromRegion = structs.GenomicInterval(
                #     taxon=self.taxon,
                #     species=self.species,
                #     uuid=f"{self.taxon}:{chrom['name']}:{start}-{end}",
                #     displayName=f"{self.species} {chrom}:{start}-{end}",
                #     chr=chrom['name'],
                #     start=start,
                #     end=end
                # )
                # genomicIntervals.append({
                #   "_id": f"{self.taxon}:{chrom['name']}:{start}-{end}",
                #   "labels": ["GenomicInterval"],
                #   "properties": chromRegion
                # })
        return genomicIntervals
    
    def _generate_gene_nodes(self):
        genes = self._gtf.filter(feature='gene')
        genes_fixed = []
        for g in genes.iter_rows(named=True):
            name = g['gene_name']
            if name == "":
                name = g['gene_id']
            genes_fixed.append({
                "_id": g['gene_id'],
                "labels": ["Gene"],
                "properties": {
                    "uuid": g['gene_id'],
                    "displayName": name,
                    "chr": g['seqname'],
                    "start": g['start'],
                    "end": g['end'],
                    "assembly": self.assembly,
                    "taxon": self.taxon,
                    "strand": g['strand']
                }
            })
        return genes_fixed
    
    def _generate_transcript_nodes(self):
        transcripts = self._gtf.filter(feature='transcript')
        transcripts_fixed = []
        for t in transcripts.iter_rows(named=True):
            name = t['transcript_name']
            if name == "":
                name = t['transcript_id']
            transcripts_fixed.append({
                "_id": t['transcript_id'],
                "labels": ["Transcript"],
                "properties": {
                    "uuid": t['transcript_id'],
                    "displayName": name,
                    "chr": t['seqname'],
                    "start": t['start'],
                    "end": t['end'],
                    "assembly": self.assembly,
                    "taxon": self.taxon,
                    "strand": t['strand']
                }
            })
        return transcripts_fixed
    
    def _generate_protein_nodes(self):
        protein = self._gtf.filter(self._gtf["protein_id"] != "")
        protein_subset = protein.select(['transcript_id', 'protein_id']).unique()
        protein_distinct = []
        for p in protein_subset.iter_rows(named=True):
            protein_distinct.append({
                "_id": p['protein_id'],
                "labels": ["Protein"],
                "properties": {
                    "uuid": p['protein_id'],
                    "displayName": p['protein_id'],
                    "assembly": self.assembly,
                    "taxon": self.taxon,
                }
            })
        return protein_distinct
    
    def iterate_nodes(self, write_to_disk=True, gtf_file_path = "genome.gtf.gz"):
        if (write_to_disk):
            print(f"Running function in write mode. Writing to file {self.node_filename}. To return nodes, set write_to_disk=False in function call")
            print("Generating genome node")
            nodes = [
                {
                    "_id": self.genome.uuid,
                    "labels": ["Genome"],
                    "properties": {
                        "_id": self.genome.uuid,
                        "displayName": self.genome.displayName,
                        "assembly": self.genome.assembly,
                        "taxon": self.genome.taxon,
                        "chromosomes": json.dumps(self.chromosome_regions)
                    }
                }
            ]
            print("Writing genome node to file")
            self.append_to_file(nodes, filepath=self.node_filename)
            nodes = []
            print("Generating genomic interval nodes")
            nodes = self._generate_genomic_interval_nodes()
            print(f"Writing {len(nodes)} genomic interval nodes to file")
            self.append_to_file(nodes, filepath=self.node_filename)
            nodes = []
            # Load gtf file into dataframe before processing genes, transcripts, proteins
            self._gtf = read_gtf(gtf_file_path)
            self._gtfloaded = True
            print("Generating gene nodes")
            nodes = self._generate_gene_nodes()
            print(f"Writing {len(nodes)} gene nodes to file")
            self.append_to_file(nodes, filepath=self.node_filename)
            nodes = []
            print("Generating transcript nodes")
            nodes = self._generate_transcript_nodes()
            print(f"Writing {len(nodes)} transcript nodes to file")
            self.append_to_file(nodes, filepath=self.node_filename)
            nodes = []
            print("Generating protein nodes")
            nodes = self._generate_protein_nodes()
            print(f"Writing {len(nodes)} protein nodes to file")
            self.append_to_file(nodes, filepath=self.node_filename)
            nodes = []
            print(f"All nodes written to file: {self.node_filename}")
        else:
            print("Running function in non-write mode. Returning nodes. To write to file, set write_to_disk=True in function call")
            genome = [
                {
                    "_id": self.genome.uuid,
                    "labels": ["Genome"],
                    "properties": {
                        "_id": self.genome.uuid,
                        "displayName": self.genome.displayName,
                        "assembly": self.genome.assembly,
                        "taxon": self.genome.taxon,
                        "chromosomes": self.chromosome_regions
                    }
                }
            ]
            print("Generating genomic interval nodes")
            genomic_intervals = self._generate_genomic_interval_nodes()
            # Load gtf file into dataframe before processing genes, transcripts, proteins
            self._gtf = read_gtf(gtf_file_path)
            self._gtfloaded = True
            print("Generating gene nodes")
            genes = self._generate_gene_nodes()
            print("Generating transcript nodes")
            transcripts = self._generate_transcript_nodes()
            print("Generating protein nodes")
            proteins = self._generate_protein_nodes()
            allNodes = [genome, genomic_intervals, genes, transcripts, proteins]
            self.nodes = list(itertools.chain(*allNodes))
            return self.nodes
    
    def _generate_genome_to_genomic_interval_edges(self):
        edges = []
        for chrom in self.chromosome_regions:
            maxCoord = math.ceil(chrom['length']/1000)
            for i in range(maxCoord):
                start = (i*1000) + 1
                # # In order to make uuid's more predictable for genomic intervals, the end is simply (i+1)*1000
                # if (i+1)==(maxCoord):
                #     end = chrom['length']
                # else:
                end = (i+1)*1000
                edges.append({
                    "from": {
                        "uuid": self.genome.uuid,
                    },
                    "to": {
                        "uuid": f"{self.taxon}:{chrom['name']}:{start}-{end}",
                    },
                    "label": "genome contains interval"
                })
        return edges
    
    def _generate_genomic_interval_edges(self):
        # Generate edges between adjacent genomic coordinates
        coordinateEdges = []
        for chrom in self.chromosome_regions:
            maxCoord = math.ceil(chrom['length']/1000)
            # One fewer edge than num nodes
            for i in range(maxCoord-1):
                # current node
                start1 = (i*1000) + 1
                end1 = (i+1)*1000
                start2 = end1 + 1
                # if (i+2)==(maxCoord):
                #     end2 = chrom['length']
                # else:
                # # In order to make uuid's more predictable for genomic intervals, the end is simply (i+2)*1000
                end2 = (i+2)*1000
                # write the edges to a file
                coordinateEdges.append({
                    "from": {
                        "uuid": f"{self.taxon}:{chrom['name']}:{start1}-{end1}",
                    },
                    "to": {
                        "uuid": f"{self.taxon}:{chrom['name']}:{start2}-{end2}",
                    },
                    "label": "next"
                })
        return coordinateEdges
    
    def _generate_gene_transcript_edges(self):
        transcripts = self._gtf.filter(feature='transcript')
        edges = []
        for t in transcripts.iter_rows(named=True):
            edges.append({
                "from": {
                    "uuid": t["gene_id"],
                },
                "to": {
                    "uuid": t["transcript_id"],
                },
                "label": "transcribed to"
            })
        return edges
    
    def _generate_transcript_protein_edges(self):
        protein = self._gtf.filter(self._gtf["protein_id"] != "")
        protein_subset = protein.select(['transcript_id', 'protein_id']).unique()
        edges = []
        for t in protein_subset.iter_rows(named=True):
            edges.append({
                "from": {
                    "uuid": t["transcript_id"],
                },
                "to": {
                    "uuid": t["protein_id"],
                },
                "label": "has translation"
            })
        return edges

    def iterate_edges(self, write_to_disk=True):
        edges = []
        if self._gtfloaded == False:
            print("Run iterate_nodes() to load in the gtf file, prior to this function being callable. Alternatively, call <INSTANCE>._gtf = <INSTANCE>.read_gtf() and <INSTANCE>._gtfloaded = True")
            return
        if (write_to_disk):
            print(f"Running function in write mode. Writing to file {self.edge_filename}. To return edges, set write_to_disk=False in function call")
            print("Processing genome to genomic interval edges")
            edges = self._generate_genome_to_genomic_interval_edges()
            print(f"Writing {len(edges)} genome to genomic interval edges to file")
            self.append_to_file(edges, filepath=self.edge_filename)
            edges = []
            print("Processing genomic interval next edges")
            edges = self._generate_genomic_interval_edges()
            print(f"Writing {len(edges)} genomic interval next edges to file")
            self.append_to_file(edges, filepath=self.edge_filename)
            edges = []
            print("Processing gene to transcript edges")
            edges = self._generate_gene_transcript_edges()
            print(f"Writing {len(edges)} gene to transcript edges to file")
            self.append_to_file(edges, filepath=self.edge_filename)
            edges = []
            print("Processing transcript to protein edges")
            edges = self._generate_transcript_protein_edges()
            print(f"Writing {len(edges)} transcript to protein edges to file")
            self.append_to_file(edges, filepath=self.edge_filename)
            edges = []
            print(f"All edges written to file: {self.edge_filename}")
        else:
            print("Running function in non-write mode. Returning edges. To write to file, set write_to_disk=True in function call")
            print("Processing genome to genomic interval edges")
            gene_genomic_edges = self._generate_genome_to_genomic_interval_edges()
            print("Processing genomic interval next edges")
            genomic_coordinate_edges = self._generate_genomic_interval_edges()
            print("Processing gene to transcript edges")
            gene_transcript_edges = self._generate_gene_transcript_edges()
            transcript_protein_edges = self._generate_transcript_protein_edges()
            print("Processing transcript to protein edges")
            allEdges = [gene_genomic_edges, genomic_coordinate_edges, gene_transcript_edges, transcript_protein_edges]
            print("Returning edges")
            return list(itertools.chain(*allEdges))

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
            "concepts": {
                "Gene": {
                    "label": "Gene",
                    "dbLabel": "Gene",
                    "definition": "Gene encompassing all biotypes",
                },
                "Transcript": {
                    "label": "Transcript",
                    "dbLabel": "Transcript",
                    "definition": "Transcripts derived from gene",
                },
                "Protein": {
                    "label": "Protein",
                    "dbLabel": "Protein",
                    "definition": "Protein derived from gene",
                },
                "Genome": {
                    "label": "Genome",
                    "dbLabel": "Genome",
                    "definition": "Genome encompassing this data pack",
                },
                "GenomicInterval": {
                    "label": "Genomic Interval",
                    "dbLabel": "GenomicInterval",
                    "definition": "Genomic Interval splitting the genome's chromosomal regions into sections of 1kbp",
                },
            },
            "relationships": {
                "genome contains interval": {
                    "from": "Genome",
                    "to": "GenomicInterval"
                },
                "next": {
                    "from": "GenomicInterval",
                    "to": "GenomicInterval"
                },
                "transcribed to": {
                    "from": "Gene",
                    "to": "Transcript"
                },
                "has translation": {
                    "from": "Transcript",
                    "to": "Protein"
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
