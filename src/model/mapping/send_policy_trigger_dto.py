import dataclasses

from utils.dataclass_utils import BaseDataClass


@dataclasses.dataclass
class SendPolicyTriggerDto(BaseDataClass):
    changeMask: str
    minIntervalMs: int
    skipFirstNChanges: int
    type: str

    @staticmethod
    def create_default() -> 'SendPolicyTriggerDto':
        return SendPolicyTriggerDto(
            changeMask='value',
            minIntervalMs=1000,
            skipFirstNChanges=0,
            type='onchange'
        )
