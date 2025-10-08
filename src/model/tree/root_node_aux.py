import copy
import dataclasses

import orjson

from model.tree.intermediate_node import IntermediateNode
from model.tree.tree_leaf import TreeLeaf


@dataclasses.dataclass(kw_only=True)
class RootNodeAux(IntermediateNode):
    label: str | None = None
    unit: str | None = None
    description: str | None = None
    UUID: str | None = None
    tags: list[str] | None = None

    def __eq__(self, other):
        return (
            isinstance(other, RootNodeAux) and
            IntermediateNode.__eq__(self, other) and
            self.label == other.label and
            self.unit == other.unit and
            self.description == other.description and
            self.UUID == other.UUID and
            self.tags == other.tags
        )

    @classmethod
    def from_dict(cls, dikt: dict) -> 'RootNodeAux':
        d = copy.deepcopy(dikt)
        for p_name, p in dikt['properties'].items():
            if p['type'] == 'object': # intermediate
                d['properties'][p_name] = IntermediateNode.from_dict(p)
            else: # leaf
                d['properties'][p_name] = TreeLeaf.from_dict(p)
        return RootNodeAux(**cls.remove_extra_fields(d))

    @classmethod
    def from_intermediate_node(cls, intermediate_node: IntermediateNode) -> 'RootNodeAux':
        d = copy.deepcopy(orjson.loads(orjson.dumps(intermediate_node)))
        for p_name, p in d['properties'].items():
            if p['type'] == 'object':  # intermediate
                d['properties'][p_name] = IntermediateNode.from_dict(p)
            else:  # leaf
                d['properties'][p_name] = TreeLeaf.from_dict(p)
        return RootNodeAux(**cls.remove_extra_fields(d))
