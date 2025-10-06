import copy
import dataclasses

from model.tree.intermediate_node import IntermediateNode
from model.tree.tree_leaf import TreeLeaf


@dataclasses.dataclass(kw_only=True)
class RootNodeAux(IntermediateNode):
    label: str | None = None
    unit: str | None = None
    description: str | None = None
    UUID: str | None = None
    tags: list[str] | None = None

    @classmethod
    def from_dict(cls, dikt: dict) -> 'RootNodeAux':
        d = copy.deepcopy(dikt)
        for p_name, p in dikt['properties'].items():
            if p['type'] == 'object': # intermediate
                d['properties'][p_name] = IntermediateNode.from_dict(p)
            else: # leaf
                d['properties'][p_name] = TreeLeaf.from_dict(p)
        return RootNodeAux(**cls.remove_extra_fields(d))
