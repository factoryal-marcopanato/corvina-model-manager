import copy
import dataclasses

import orjson

from model.datamodel.datamodel_root import DataModelRoot
from model.tree.root_node import RootNode
from model.tree.root_node_aux import RootNodeAux


@dataclasses.dataclass(kw_only=True)
class MappingRoot(RootNode):
    modelId: str | None = None

    def __eq__(self, other):
        return (
            isinstance(other, MappingRoot) and
            RootNode.__eq__(self, other) and
            self.modelId == other.modelId
        )

    @classmethod
    def from_dict(cls, dikt: dict) -> 'MappingRoot':
        d = copy.deepcopy(dikt)
        d['data'] = RootNodeAux.from_dict(dikt.get('data') or dikt['json'])
        return MappingRoot(**cls.remove_extra_fields(d))

    def get_create_mapping_payload(self, referring_data_model: DataModelRoot) -> dict:
        assert referring_data_model.version is not None

        data = orjson.loads(orjson.dumps(self))  # this removes problems like the CorvinaDatatype enum
        data['data']['instanceOf'] = referring_data_model.clear_name + ':' + referring_data_model.version
        return data

    async def maybe_fetch_id(self, connector: 'CorvinaClient'):
        if self.id is not None:
            return

        # TODO implement the get by name (exists!!)
        mappings: dict[str, MappingRoot] = await connector.get_presets_by_id()
        for mapping_id, m in mappings.items():
            if m.name == self.clear_name and m.data.instanceOf == self.data.instanceOf:
                self.id = mapping_id
                return

        assert False, f'Cannot find mapping {self.name} in model {self.data.instanceOf}'
