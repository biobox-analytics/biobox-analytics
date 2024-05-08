"""
LaminDB x BioBox Integrations
"""

import bionty as bt
from biobox_analytics.core import Node


def _uuid_formatter(db_label, lamin_uid):
    return f'lamindb:{db_label}:{lamin_uid}'


class BxLamin:

    def __init__(self, lamin_obj):
        self._lamin_obj = lamin_obj

        self._db_label = self._get_db_label()
        if self._db_label is None:
            raise Exception("Unrecognized Object Type: This may not be implemented as an integration yet.")

        self._uuid = _uuid_formatter(self._db_label, lamin_obj.uid)

        self._node = self._make_node()

    def save(self):
        self._node.save()
        self._attach_parents()

    def _attach_parents(self):
        parent_df = self._lamin_obj.parents.df()
        parent_records = parent_df.to_dict(orient='records')
        for parent in parent_records:
            if parent.get('ontology_id') is not None:
                self._node.attach('is a', parent.get('ontology_id'))
            else:
                parent_id = _uuid_formatter(self._db_label, parent.get('uid'))
                self._node.attach('is a', parent_id)

    def _is_celltype(self):
        return isinstance(self._lamin_obj, bt.CellType)

    def _get_db_label(self):
        if isinstance(self._lamin_obj, bt.CellType):
            return 'CellType'

        if isinstance(self._lamin_obj, bt.Tissue):
            return 'Tissue'

        if isinstance(self._lamin_obj, bt.Disease):
            return 'Disease'

        if isinstance(self._lamin_obj, bt.ExperimentalFactor):
            return 'EFO'

    def _has_ontology_id(self):
        return self._lamin_obj.ontology_id is not None

    def _make_node(self):
        node = None
        if self._has_ontology_id():
            node = Node(self._lamin_obj.ontology_id, self._db_label)
            node.properties = {'lamindb_xref': self._uuid}
        else:
            node = Node(self._uuid, self._db_label)
            node.properties = {'displayName': self._lamin_obj.name}

        return node