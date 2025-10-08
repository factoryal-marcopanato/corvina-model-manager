import enum
import dataclasses

from model.tree.tree_node import TreeNode
from utils.dataclass_utils import BaseDataClass


class DiffEnum(enum.Enum):
    NEW_NODE = 'new_node'
    DELETED_NODE = 'deleted_node'
    NODE_CHANGED = 'node_changed'
    # NEW_LEAF = 'new_leaf'
    # DELETED_LEAF = 'deleted_leaf'
    # LEAF_CHANGED = 'leaf'


@dataclasses.dataclass
class NodeDiff(BaseDataClass):
    op: DiffEnum
    node: TreeNode
    path: str
    new_version: str | None = None
