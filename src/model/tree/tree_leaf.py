import abc
import dataclasses

from model.tree.tree_node import TreeNode


@dataclasses.dataclass(kw_only=True)
class TreeLeaf(TreeNode, abc.ABC):
    deprecated: bool = None

    def get_tree_node_children(self) -> dict[str, 'TreeNode']:
        return {}

    def get_tree_node_name(self) -> str:
        assert False  # TODO this should not be called!!!

    @classmethod
    def from_dict(cls, dikt: dict) -> 'TreeLeaf':
        if 'mode' in dikt:  # MappingLeaf
            from model.mapping.mapping_leaf import MappingLeaf
            return MappingLeaf(**dikt)
        else:  # DataModelLeaf
            from model.datamodel.datamodel_leaf import DataModelLeaf
            return DataModelLeaf.from_dict(dikt)
