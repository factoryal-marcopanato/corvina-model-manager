import dataclasses
import typing

from utils.dataclass_utils import BaseDataClass


@dataclasses.dataclass
class CorvinaDevice(BaseDataClass):
    id: str
    deviceId: str
    realmId: str  # ovvio
    deleted: bool
    orgResourceId: str  # ovvio
    label: str

    creationDate: int
    updatedAt: int
    lastConnUpdateAt: int
    lastConfigUpdateAt: int

    configurationApplied: bool
    configurationSent: bool
    configurationError: str

    connected: bool

    modelId: str
    modelVersion: str
    modelName: str

    presetName: str
    presetId: str

    attributes: dict[str, typing.Any] = dataclasses.field(default_factory=dict)
    tags: list[str] = dataclasses.field(default_factory=list)
    groups: list[typing.Any] = dataclasses.field(default_factory=list)
