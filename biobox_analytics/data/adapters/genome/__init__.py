from biobox_analytics.data.adapters._base import Adapter
import _structs as structs
import rdflib
import json
import requests
import os
import gzip
import math
from gtfparse import read_gtf
import urllib.request
from datetime import datetime

class GenomeAdapter(Adapter):
    def __init__(self, species='homo sapiens', node_filename='node.jsonl', edge_filename='edge.jsonl' ):
        super().__init__()
        self.species = species
        self.assembly = None
        self.karyotypes = None
        self.chromosome_regions = []
        self.node_filename = node_filename
        self.edge_filename = edge_filename
        self.taxon = self.__get_taxonid()
        self.__get_ensembl_assembly_info()
        dateCreated = datetime()
        self.genome = structs.Genome(
            uuid=f"genome_{self.assembly}",
            species=self.species,
            taxon=self.taxon,
            dateCreated=dateCreated,
            assembly=self.assembly
        )
    
    @property
    def chromosome_regions(self):
        return self.chromosome_regions
    
    @property
    def taxon(self):
        return self.taxon
    
    @property
    def assembly(self):
        return self.assembly
    
    @property
    def karyotypes(self):
        return self.karyotypes
    
    @property
    def chromosome_regions(self):
        return self.chromosome_regions
    
    @property
    def gtf_file(self):
        return self.gtf_file
    
    @property
    def genome(self):
        return self.genome

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
                if (i+1)==(maxCoord):
                    end = chrom['length']
                else:
                    end = (i+1)*1000
                genomicIntervals.append({
                    "_id": f"{self.taxon}:{chrom['name']}:{start}-{end}",
                    "labels": ["GenomicInterval"],
                    "properties": {
                        "uuid": f"{self.taxon}:{chrom['name']}:{start}-{end}",
                        "displayName": f"{self.species} {chrom}:{start}-{end}",
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
        return []
    
    def iterate_nodes(self, gtf_file_path = "genome.gtf.gz"):
        self.genomic_intervals = self._generate_genomic_interval_nodes()
        # Load gtf file into dataframe before processing genes, transcripts, proteins
        self._gtf = read_gtf(gtf_file_path)
        self.genes = self._generate_gene_nodes()
        self.transcripts = self._generate_transcript_nodes()
        self.proteins = self._generate_protein_nodes()
        # write chromosome regions to jsonl file
    
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
                if (i+2)==(maxCoord):
                    end2 = chrom['length']
                else:
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

    def iterate_edges(self):
        genomic_coordinate_edges = self._generate_genomic_interval_edges()

    def process_item(self, item):
        """Processes a single item (node or edge)."""
        # Customize how you want to process each item, e.g., add extra information, filter, etc.
        return item  # In this example, we just return the item as-is.

    def describe_node_properties(self):
        pass

    def describe_edge_properties(self):
        pass

    def write_serialized_data_to_file(self, directory):
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