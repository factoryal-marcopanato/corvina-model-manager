import copy
import dataclasses

from model.datamodel.datamodel_leaf import DataModelLeaf
from model.tree.intermediate_node import IntermediateNode


@dataclasses.dataclass
class RootNodeAux(IntermediateNode):
    label: str = ''
    unit: str = ''
    description: str = ''
    tags: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, dikt: dict) -> 'RootNodeAux':
        d = copy.deepcopy(dikt)
        for p_name, p in dikt['properties'].items():
            if p['type'] == 'object': # intermediate
                d['properties'][p_name] = IntermediateNode.from_dict(p)
            else: # leaf
                d['properties'][p_name] = DataModelLeaf.from_dict(p)
        return RootNodeAux(**cls.remove_extra_fields(d))
