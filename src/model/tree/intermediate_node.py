import copy
import dataclasses

from model.tree.tree_leaf import TreeLeaf
from model.tree.tree_node import TreeNode


@dataclasses.dataclass(kw_only=True)
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
                d['properties'][p_name] = TreeLeaf.from_dict(p)
        return IntermediateNode(**cls.remove_extra_fields(d))

    def get_intermediate_elems(self) -> list[str]:
        res = []
        for child in self.properties.values():
            if isinstance(child, IntermediateNode):
                res.append(child.instanceOf)
                res.extend(child.get_intermediate_elems())
        return res
