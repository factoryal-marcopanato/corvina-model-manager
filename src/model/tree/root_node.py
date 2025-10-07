import copy
import dataclasses

from model.tree.root_node_aux import RootNodeAux
from model.tree.tree_node import TreeNode
from utils.corvina_version_utils import version_re


@dataclasses.dataclass(kw_only=True)
class RootNode(TreeNode):
    id: str | None = None
    name: str
    data: RootNodeAux
    deleted: bool | None = None

    def __eq__(self, other):
        return (
            isinstance(other, RootNode) and
            TreeNode.__eq__(self, other) and
            self.id == other.id and
            self.name == other.name and
            self.data == other.data and
            self.deleted == other.deleted
        )

    def get_tree_node_children(self) -> dict[str, 'TreeNode']:
        return {self.name: self.data}  # TODO sure???

    def get_tree_node_name(self) -> str:
        return self.clear_name

    @classmethod
    def from_dict(cls, dikt: dict) -> 'RootNode':
        d = copy.deepcopy(dikt)
        d['data'] = RootNodeAux.from_dict(dikt.get('data') or dikt['json'])
        return RootNode(**cls.remove_extra_fields(d))

    @property
    def clear_name(self):
        m = version_re.match(self.name)
        return m[1] if m else self.name

    def get_deploy_name(self) -> str:
        return self.name.split('-')[0]

    def get_intermediate_elems(self) -> list[str]:
        return self.data.get_intermediate_elems()
