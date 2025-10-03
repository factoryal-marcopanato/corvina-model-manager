import copy
import dataclasses

from model.mapping.send_policy_trigger_dto import SendPolicyTriggerDto
from utils.dataclass_utils import BaseDataClass


@dataclasses.dataclass
class SendPolicyDto(BaseDataClass):
    triggers: list[SendPolicyTriggerDto]

    @staticmethod
    def create_default() -> 'SendPolicyDto':
        return SendPolicyDto(
            triggers=[SendPolicyTriggerDto.create_default()]
        )

    @classmethod
    def from_dict(cls, dikt: dict) -> 'SendPolicyDto':
        d = copy.deepcopy(dikt)
        d['triggers'] = [SendPolicyTriggerDto.from_dict(t) for t in dikt['triggers']]
        return SendPolicyDto(**cls.remove_extra_fields(d))
