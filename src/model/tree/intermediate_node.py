import copy
import dataclasses

from model.tree.tree_leaf import TreeLeaf
from model.tree.tree_node import TreeNode
from utils.corvina_version_utils import version_re


@dataclasses.dataclass(kw_only=True)
class IntermediateNode(TreeNode):
    type: str  # object (always?)
    instanceOf: str
    properties: dict[str, TreeNode]
    deprecated: bool = None

    def __eq__(self, other):
        return (
            isinstance(other, IntermediateNode) and
            TreeNode.__eq__(self, other) and
            self.type == other.type and
            self.instanceOf == other.instanceOf and
            self.properties == other.properties  # yes, it works!!!
        )

    def get_tree_node_children(self) -> dict[str, 'TreeNode']:
        return self.properties

    def get_tree_node_name(self) -> str:
        m = version_re.match(self.instanceOf)
        return m[1] if m else self.instanceOf

    def get_node_version(self) -> str:
        """
        Returns the string "1.0.0" or the effective version
        :return:
        """
        m = version_re.match(self.instanceOf)
        return m[2] if m else self.instanceOf

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
