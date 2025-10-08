import enum
import dataclasses

from model.tree.tree_node import TreeNode
from utils.dataclass_utils import BaseDataClass


class DiffEnum(enum.Enum):
    NEW_NODE = 'new'
    NODE_CHANGED = 'change'
    LEAF_CHANGED = 'leaf'
    DELETED_NODE = 'delete'


@dataclasses.dataclass
class NodeDiff(BaseDataClass):
    op: DiffEnum
    node: TreeNode
    new_version: str | None = None
