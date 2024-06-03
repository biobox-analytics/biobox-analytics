from biobox_analytics.data.adapters._base import Adapter
import _structs as structs
from

class ChipSeqAdapter(Adapter):

    def __init__(self, target: structs.Protein ):
        super().__init__()
