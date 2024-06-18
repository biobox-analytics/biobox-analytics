class Edge:
    def __init__(self, label, src=None, trg=None):
        self.label = label
        self.src = src
        self.trg = trg

    def serialize(self, format="data-pack"):
        pass

    def _can_serialize(self):
        if self.src is None:
            raise Exception("Edge Source is missing")


    def _serialize_as_data_pack(self):
        pass