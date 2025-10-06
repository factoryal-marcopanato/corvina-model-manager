import copy
import dataclasses

from model.tree.root_node import RootNode
from model.tree.root_node_aux import RootNodeAux


@dataclasses.dataclass
class MappingRoot(RootNode):
    modelId: str

    @classmethod
    def from_dict(cls, dikt: dict) -> 'MappingRoot':
        d = copy.deepcopy(dikt)
        d['data'] = RootNodeAux.from_dict(dikt.get('data', dikt['json']))
        return MappingRoot(**cls.remove_extra_fields(d))