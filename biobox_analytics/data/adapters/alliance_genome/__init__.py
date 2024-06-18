from enum import Enum, auto
import requests
import os
import json
from biobox_analytics.utils import download_gzipped_json, oxo_mapping, scrape_all_records
import io
import pandas as pd
from tqdm import tqdm


class AllianceDownloads(Enum):
    DISEASE_HUMAN = "https://fms.alliancegenome.org/download/DISEASE-ALLIANCE-JSON_HUMAN.json.gz"
    DISEASE_MOUSE = "https://fms.alliancegenome.org/download/DISEASE-ALLIANCE-JSON_MGI.json.gz"


class AllianceGenomeAdapter:

    def __init__(self):
        self._api = "https://www.alliancegenome.org/api/"
        self._disease_gene_associations = []
        self._prepare_mappers()
        self._download_disease_associations()

        self.metadata = {
            '_meta': {
                'version': '0.1.0',
                'date_updated': '2024-05-19',
                'maintainer': 'BioBox Analytics'
            },
            'key': 'alliance_genome',
            'name': 'Alliance of Genome Resources',
            'description': 'TBD',
            'source': [
                {
                    'uri': 'https://www.alliancegenome.org/',
                    'type': 'doc'
                },
                {
                    'uri': 'https://www.alliancegenome.org/downloads',
                    'type': 'data',
                    'version': '7.1.0'
                }
            ],
            'concepts': {},
            'relationships': {}
        }

    def _prepare_mappers(self):

        human = pd.read_table("https://www.alliancegenome.org/api/geneMap/ensembl?species=NCBITaxon:9606", sep="\t")

        mouse = pd.read_table("https://www.alliancegenome.org/api/geneMap/ensembl?species=NCBITaxon:10090", sep="\t")

        self._gene_map = pd.concat([human, mouse])

    def _download_disease_associations(self):
        human_results = download_gzipped_json(AllianceDownloads.DISEASE_HUMAN.value)
        DISEASE_IDS = list(set([x.get('DOID') for x in human_results['data']]))

        self._doid_mapping = oxo_mapping(DISEASE_IDS, ["EFO", "MONDO"])

        for _id in tqdm(DISEASE_IDS, desc="Collecting DiseaseGene Annotations"):
            try:
                harmonized_disease_id = self._doid_mapping.get(_id)[0]
            except:
                continue

            records = scrape_all_records(
                f"https://www.alliancegenome.org/api/disease/{_id}/genes?filter.species=Homo sapiens")
            associations = []
            for anno in records:
                association = self._format_disease_gene_annotation(anno, harmonized_disease_id)
                if association is not None:
                    associations.append(association)
            self._disease_gene_associations.extend(associations)

    def _hgnc2ensembl(self, hgnc):
        hgnc_id = hgnc.split(':').pop()

        subset = self._gene_map[self._gene_map['NCBI ID'] == hgnc_id]
        return subset['Ensembl ID']

    def _format_disease_gene_annotation(self, anno, disease_id, fmt="edge"):

        relation_str = anno.get('generatedRelationString').replace('_', ' ')
        disease_qualifiers = anno.get('diseaseQualifiers', [])

        if len(disease_qualifiers) > 1:
            print(anno)
            raise Exception("Disease Qualifiers should not be more than one in length")

        if len(disease_qualifiers) == 1:
            disease_qualifier_str = disease_qualifiers[0].replace('_', ' ')
            relation_str = f'{relation_str} {disease_qualifier_str}'

        uuid = anno.get("uniqueId")

        references = anno.get('pubmedPubModIDs')
        evidence = map(lambda x: x.get('abbreviation'), anno.get('evidenceCodes', []))

        try:
            gene_hgnc = anno['subject']['modEntityId']
            ensembl_id = self._hgnc2ensembl(gene_hgnc)
        except:
            return

        output = {
            'from': {
                'uuid': ensembl_id
            },
            'to': {
                'uuid': disease_id
            },
            'label': relation_str,
            'properties': {
                'uuid': uuid,
                'references': references,
                'evidence': evidence,
                'citation_authority': 'Alliance of Genome Resources'
            }
        }
        return output
