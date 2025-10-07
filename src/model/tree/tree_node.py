import abc
import dataclasses

from utils.dataclass_utils import BaseDataClass


@dataclasses.dataclass(kw_only=True)
class TreeNode(BaseDataClass, abc.ABC):

    @abc.abstractmethod
    def get_tree_node_children(self) -> dict[str, 'TreeNode']:
        pass

    @abc.abstractmethod
    def get_tree_node_name(self) -> str:
        pass
