import copy
import orjson
import dataclasses


# from corvina_connector.corvina_client import CorvinaClient
from model.tree.root_node import RootNode
from model.tree.root_node_aux import RootNodeAux
from utils.corvina_version_utils import version_re


@dataclasses.dataclass(kw_only=True)
class DataModelRoot(RootNode):
    version: str | None = None

    def __post_init__(self):
        if self.version is None:
            self.version = '1.0.0'

    def __eq__(self, other):
        return (
            isinstance(other, DataModelRoot) and
            RootNode.__eq__(self, other) and
            self.version == other.version
        )

    @classmethod
    def from_dict(cls, dikt: dict) -> 'DataModelRoot':
        d = copy.deepcopy(dikt)
        d['data'] = RootNodeAux.from_dict(dikt.get('data') or dikt['json'])
        return DataModelRoot(**cls.remove_extra_fields(d))

    def get_create_model_payload(self) -> dict:
        data = orjson.loads(orjson.dumps(self))  # this removes problems like the CorvinaDatatype enum
        if not version_re.match(data['name']):
            data['name'] = data['name'] + ':1.0.0'
        if not version_re.match(data['data']['instanceOf']):
            data['data']['instanceOf'] = data['data']['instanceOf'] + ':1.0.0'
        return data

    async def maybe_fetch_id(self, connector: 'CorvinaClient'):
        if self.id is not None:
            return

        # TODO implement the get by name (exists!!)
        models: dict[str, DataModelRoot] = await connector.get_datamodels_by_id()
        for model_id, dm in models.items():
            if dm.name == self.clear_name and dm.version == self.version:
                self.id = model_id
                return

        assert False, f'Cannot find model {self.name}:{self.version}'
