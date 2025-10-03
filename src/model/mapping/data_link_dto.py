import dataclasses

from utils.dataclass_utils import BaseDataClass


@dataclasses.dataclass
class DataLinkDto(BaseDataClass):
    source: str
