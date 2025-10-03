import copy
import dataclasses

from model.datamodel.datamodel_leaf import DataModelLeaf
from model.tree.tree_node import TreeNode


@dataclasses.dataclass
class IntermediateNode(TreeNode):
    type: str
    instanceOf: str
    properties: dict[str, TreeNode]

    @classmethod
    def from_dict(cls, dikt: dict) -> 'IntermediateNode':
        d = copy.deepcopy(dikt)
        for p_name, p in dikt['properties'].items():
            if p['type'] == 'object':  # intermediate
                d['properties'][p_name] = IntermediateNode.from_dict(p)
            else:  # leaf
                d['properties'][p_name] = DataModelLeaf.from_dict(p)
        return IntermediateNode(**cls.remove_extra_fields(d))
