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

    @classmethod
    def from_dict(cls, dikt: dict) -> 'RootNode':
        d = copy.deepcopy(dikt)
        d['data'] = RootNodeAux.from_dict(dikt.get('data') or dikt['json'])
        return RootNode(**cls.remove_extra_fields(d))

    @property
    def clear_name(self):
        m = version_re.match(self.name)
        return m[1] if m else self.name


    def get_intermediate_elems(self) -> list[str]:
        return self.data.get_intermediate_elems()
