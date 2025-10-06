import dataclasses

from model.tree.tree_node import TreeNode


@dataclasses.dataclass(kw_only=True)
class TreeLeaf(TreeNode):
    pass

    @classmethod
    def from_dict(cls, dikt: dict) -> 'TreeLeaf':
        if 'mode' in dikt:  # MappingLeaf
            from model.mapping.mapping_leaf import MappingLeaf
            return MappingLeaf(**dikt)
        else:  # DataModelLeaf
            from model.datamodel.datamodel_leaf import DataModelLeaf
            return DataModelLeaf(**dikt)
