import copy
import dataclasses

from model.tree.root_node_aux import RootNodeAux
from model.tree.tree_node import TreeNode


@dataclasses.dataclass
class RootNode(TreeNode):
    name: str
    data: RootNodeAux

    @classmethod
    def from_dict(cls, dikt: dict) -> 'RootNode':
        d = copy.deepcopy(dikt)
        d['data'] = RootNodeAux.from_dict(dikt.get('data', dikt['json']))
        return RootNode(**cls.remove_extra_fields(d))
