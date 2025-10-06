import copy
import dataclasses

from model.tree.root_node import RootNode
from model.tree.root_node_aux import RootNodeAux


@dataclasses.dataclass
class DataModelRoot(RootNode):
    version: str

    @classmethod
    def from_dict(cls, dikt: dict) -> 'DataModelRoot':
        d = copy.deepcopy(dikt)
        d['data'] = RootNodeAux.from_dict(dikt.get('data', dikt['json']))
        return DataModelRoot(**cls.remove_extra_fields(d))