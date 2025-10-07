import copy
import dataclasses

from model.corvina_datatype import CorvinaDatatype
from model.tree.tree_leaf import TreeLeaf


@dataclasses.dataclass(kw_only=True)
class DataModelLeaf(TreeLeaf):
    version: str | None = None
    type: CorvinaDatatype

    def __eq__(self, other):
        return (
            isinstance(other, DataModelLeaf) and
            TreeLeaf.__eq__(self, other) and
            self.version == other.version and
            self.type == other.type
        )

    def __post_init__(self):
        if self.version is None:
            self.version = '1.0.0'

    @classmethod
    def from_dict(cls, dikt: dict) -> 'DataModelLeaf':
        d = copy.deepcopy(dikt)
        d['type'] = CorvinaDatatype(dikt['type'])
        return DataModelLeaf(**cls.remove_extra_fields(d))
