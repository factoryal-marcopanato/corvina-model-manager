import dataclasses

from model.corvina_datatype import CorvinaDatatype
from model.datamodel.datamodel_leaf import DataModelLeaf
from model.mapping.data_link_dto import DataLinkDto
from model.mapping.history_policy_dto import HistoryPolicyDto
from model.mapping.send_policy_dto import SendPolicyDto


@dataclasses.dataclass
class MappingLeaf(DataModelLeaf):
    mode: str
    historyPolicy: HistoryPolicyDto
    sendPolicy: SendPolicyDto
    datalink: DataLinkDto

    @staticmethod
    def create_default(
        source: str,
        datatype: CorvinaDatatype,
        version='1.0.0',
        mode='R',
        history_policy=True,
    ) -> 'MappingLeaf':
        return MappingLeaf(
            version=version,
            type=datatype,
            mode=mode,
            historyPolicy=HistoryPolicyDto(enabled=history_policy),
            sendPolicy=SendPolicyDto.create_default(),
            datalink=DataLinkDto(source)
        )
