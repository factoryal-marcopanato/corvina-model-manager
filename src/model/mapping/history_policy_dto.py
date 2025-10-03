import dataclasses

from utils.dataclass_utils import BaseDataClass


@dataclasses.dataclass
class HistoryPolicyDto(BaseDataClass):
    enabled: bool
