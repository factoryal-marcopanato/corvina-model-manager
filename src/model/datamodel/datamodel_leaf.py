import copy
import dataclasses

from model.corvina_datatype import CorvinaDatatype
from utils.dataclass_utils import BaseDataClass


@dataclasses.dataclass
class DataModelLeaf(BaseDataClass):
    version: str
    type: CorvinaDatatype

    @classmethod
    def from_dict(cls, dikt: dict) -> 'DataModelLeaf':
        d = copy.deepcopy(dikt)
        d['type'] = CorvinaDatatype(dikt['type'])
        return DataModelLeaf(**cls.remove_extra_fields(d))
