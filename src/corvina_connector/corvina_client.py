import collections.abc

import orjson
import aiohttp
import logging

from model.datamodel.datamodel_root import DataModelRoot
from utils.corvina_version_utils import version_re
from model.device.corvina_device import CorvinaDevice
from model.mapping.mapping_root import MappingRoot
from utils.dataclass_utils import BaseDataClass
from utils.dict_utils import remove_nulls

logger = logging.getLogger('app.corvina')


class CorvinaClient:

    def __init__(
        self,
        org: str,
        username: str,
        token: str,
        corvina_suffix: str,
        corvina_prefix: str
    ):
        self._org = org
        self._username = username
        self._token = token
        self._corvina_suffix = corvina_suffix
        self._corvina_prefix = corvina_prefix

        # self._api_client = ApiClient(
        #     configuration=Configuration(
        #         host=f'https://{self._corvina_prefix}corvina{self._corvina_suffix}/svc/mappings',
        #         api_key={'Authorization': ''}
        #     )
        # )

        self._jwt_token: str | None = None

    async def login(self):
        logger.info(f'Logging client {self._username} to corvina {self._corvina_prefix} org {self._org}')
        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(self._username, self._token)) as session:
            async with session.post(
                url=f'https://auth.corvina{self._corvina_suffix}/auth/realms/{self._org}/protocol/openid-connect/token',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=f'grant_type=client_credentials&scope=org:{self._org}'
            ) as req:
                token = await req.json(loads=orjson.loads)
                assert 'error' not in token, f'Cannot perform Corvina Login! Got {token}'
                self._jwt_token = token['access_token']
                # self._api_client.configuration.api_key['Authorization'] = self._jwt_token

    # @staticmethod
    # async def _merge_pages(session: aiohttp.ClientSession, url: str) -> list[dict]:
    #     res = []
    #     cur_page = 0
    #     is_last_page = False
    #     while not is_last_page:
    #         logger.debug(f'GET {url}&page={cur_page}')
    #         async with session.get(url + f'&page={cur_page}') as req:
    #             data = await req.text()
    #             assert req.ok, f'Got {req.status} with body {data} while asking for {url}&page={cur_page}'
    #             json_data = orjson.loads(data)
    #             assert 'number' in json_data and 'data' in json_data and 'last' in json_data, f'Got invalid body {json_data}'
    #
    #             res.extend(json_data['data'])
    #             is_last_page = json_data['last']
    #             cur_page += 1
    #
    #     return res

    @staticmethod
    async def _get_json(session: aiohttp.ClientSession, path: str, **kwargs) -> dict:
        async with session.get(path, params=kwargs) as req:
            data = await req.text()
            assert req.ok, f'Got {req.status} with body {data} while asking for {path}'
            return orjson.loads(data)

    @staticmethod
    async def _delete_json(session: aiohttp.ClientSession, path: str, data: str | bytes | None = None, **kwargs) -> dict:
        async with session.delete(path, data=data, params=kwargs) as req:
            data = await req.text()
            assert req.ok, f'Got {req.status} with body {data} while asking for {path}'
            return orjson.loads(data)

    @staticmethod
    async def _put_json(session: aiohttp.ClientSession, path: str, data: str | bytes, **kwargs) -> dict:
        logger.debug(f'Putting {data} to {path}')
        async with session.put(path, headers={'Content-Type': 'application/json'}, data=data, params=kwargs) as req:
            data = await req.text()
            assert req.ok, f'Got {req.status} with body {data} while posting {data} in {path}'
            return orjson.loads(data)

    @staticmethod
    async def _post_json(session: aiohttp.ClientSession, path: str, data: str | bytes, **kwargs) -> dict:
        logger.debug(f'Posting {data} to {path}')
        async with session.post(path, headers={'Content-Type': 'application/json'}, data=data, params=kwargs) as req:
            data = await req.text()
            assert req.ok, f'Got {req.status} with body {data} while posting {data} in {path}'
            return orjson.loads(data)

    @staticmethod
    def _prepare(obj: dict | BaseDataClass) -> bytes:
        data = orjson.loads(orjson.dumps(obj))  # Not so efficient, but...
        remove_nulls(data)
        return orjson.dumps(data)

    def _session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            headers={'Authorization': self._jwt_token or 'please-login'},
            base_url=f'https://{self._corvina_prefix}corvina{self._corvina_suffix}/svc/mappings/'
        )

    # async def _get_paged_obj(self, path: str) -> list[dict]:
    #     async with self._session() as session:
    #         return await self._merge_pages(session, path)

    # ------------------------------------------------------------------------------------------------------------------
    # Devices Part
    # ------------------------------------------------------------------------------------------------------------------
    async def get_devices_by_id(self) -> dict[str, CorvinaDevice]:
        logger.info('Querying Devices')
        async with self._session() as s:
            response = await self._get_json(s, 'api/v1/devices', organization=self._org, pageSize=10000)
            logger.debug(f'Got {orjson.dumps(response)}')

        fix_items = [CorvinaDevice.from_dict(i) for i in response['data']]
        return {i.id: i for i in fix_items}

    # ------------------------------------------------------------------------------------------------------------------
    # Models Part
    # ------------------------------------------------------------------------------------------------------------------
    async def get_datamodels_by_id(self) -> dict[str, DataModelRoot]:
        logger.info('Querying Models')

        async with self._session() as s:
            response = await self._get_json(s, 'api/v1/models', organization=self._org, pageSize=10000)
            logger.debug(f'Got {orjson.dumps(response)}')

        fix_items = [DataModelRoot.from_dict(i) for i in response['data']]
        return {i.id: i for i in fix_items}

        # api = ModelsApi(self._api_client)
        # models = await api.get_models(organization=self._org, page_size=1000)
        # return {m.id: m for m in models.data}

    async def create_data_model(self, data_model: DataModelRoot):
        async with self._session() as s:
            # Sample Payload
            # {"name":"prova:1.0.0","data":{"type":"object","instanceOf":"prova:1.0.0","properties":{"a":{"type":"integer"}},"label":"","unit":"","description":"","tags":[]}}
            data = await self._post_json(s, 'api/v1/models', self._prepare(data_model.get_create_model_payload()), organization=self._org)
            new_data_model_root = DataModelRoot.from_dict(data)
            logger.debug(f'Got {orjson.dumps(new_data_model_root)}')

            # TODO should check for equality, or better, set ids etc...

    async def update_data_model(self, old_data_model: DataModelRoot, new_data_model: DataModelRoot) -> DataModelRoot:
        async with self._session() as s:
            data = await self._put_json(
                s, f'api/v1/models/{old_data_model.id}',
                self._prepare(new_data_model), organization=self._org
            )
            logger.debug(f'Got {orjson.dumps(data)}')  # TODO dump our object instead of the raw response
            new_data_model_root = DataModelRoot.from_dict(data['value'])
            return new_data_model

    async def delete_data_model(self, data_model: DataModelRoot):
        await data_model.maybe_fetch_id(self)

        async with self._session() as s:
            data = await self._delete_json(s, 'api/v1/models/' + data_model.id, organization=self._org)
            deleted_data_model_root = DataModelRoot.from_dict(data)
            logger.debug(f'Got {orjson.dumps(deleted_data_model_root)}')
            # TODO should check something?

    async def delete_data_model_by_id(self, data_model_id: str):
        async with self._session() as s:
            data = await self._delete_json(s, 'api/v1/models/' + data_model_id, organization=self._org)
            deleted_data_model_root = DataModelRoot.from_dict(data)
            logger.debug(f'Got {orjson.dumps(deleted_data_model_root)}')
            # TODO should check something?

    # ------------------------------------------------------------------------------------------------------------------
    # Mappings Part
    # ------------------------------------------------------------------------------------------------------------------
    # async def get_mappings_by_id(self) -> dict[str, MappingRoot]:
    #     logger.info('Querying Mappings')
    #
    #     async with self._session() as s:
    #         response = await self._get_json(s, 'api/v1/mappings', organization=self._org, pageSize=10000)
    #         logger.debug(f'Got {orjson.dumps(response)}')
    #
    #     fix_items = [MappingRoot.from_dict(i) for i in response['data']]
    #     return {i.id: i for i in fix_items}
    #
    #     # api = MappingsApi(self._api_client)
    #     # mappings = await api.search_mapping(organization=self._org, page_size=1000)
    #     # return {m.id: m for m in mappings.data}
    #
    # async def create_mapping(self, data_model: DataModelRoot, mapping: MappingRoot):
    #     async with self._session() as s:
    #         # Sample Payload
    #         # {"name":"ProvaMapping","data":{"type":"object","instanceOf":"prova:1.0.0","properties":{"a":{"version":"1.0.0","type":"integer","mode":"R","historyPolicy":{"enabled":true},"sendPolicy":{"triggers":[{"changeMask":"value","minIntervalMs":1000,"skipFirstNChanges":0,"type":"onchange"}]},"datalink":{"source":"Ent.S.A.Prova"}}},"label":"","unit":"","description":"","UUID":"z5kn06t96oqqm3fl","tags":[]}}
    #         data = await self._post_json(s, 'api/v1/models', orjson.dumps(mapping.get_create_model_payload()), organization=self._org)
    #         new_data_model_root = DataModelRoot.from_dict(data)
    #         logger.debug(f'Got {orjson.dumps(new_data_model_root)}')
    #
    #         # TODOo should check for equality, or better, set ids etc...

    # ------------------------------------------------------------------------------------------------------------------
    # Preset Part
    # ------------------------------------------------------------------------------------------------------------------
    async def get_presets_by_id(self) -> dict[str, MappingRoot]:
        logger.info('Querying Mappings')

        async with self._session() as s:
            response = await self._get_json(s, 'api/v1/presets', organization=self._org, pageSize=10000)
            logger.debug(f'Got {orjson.dumps(response)}')

        fix_items = [MappingRoot.from_dict(i) for i in response['data']]
        return {i.id: i for i in fix_items}

        # api = MappingsApi(self._api_client)
        # mappings = await api.search_mapping(organization=self._org, page_size=1000)
        # return {m.id: m for m in mappings.data}

    async def create_preset(self, data_model: DataModelRoot, mapping: MappingRoot):
        async with self._session() as s:
            # Sample Payload
            # {"name":"ProvaMapping","data":{"type":"object","instanceOf":"prova:1.0.0","properties":{"a":{"version":"1.0.0","type":"integer","mode":"R","historyPolicy":{"enabled":true},"sendPolicy":{"triggers":[{"changeMask":"value","minIntervalMs":1000,"skipFirstNChanges":0,"type":"onchange"}]},"datalink":{"source":"Ent.S.A.Prova"}}},"label":"","unit":"","description":"","UUID":"z5kn06t96oqqm3fl","tags":[]}}
            data = await self._post_json(
                s, 'api/v1/presets', self._prepare(mapping.get_create_mapping_payload(data_model)), organization=self._org
            )
            new_mapping = MappingRoot.from_dict(data)
            logger.debug(f'Got {orjson.dumps(new_mapping)}')

            # TODO should check for equality, or better, set ids etc...

    async def delete_preset(self, mapping: MappingRoot):
        await mapping.maybe_fetch_id(self)

        async with self._session() as s:
            data = await self._delete_json(s, 'api/v1/presets/' + mapping.id, organization=self._org)
            deleted_mapping = MappingRoot.from_dict(data)
            logger.debug(f'Got {orjson.dumps(deleted_mapping)}')

            # TODO should check for equality, or better, set ids etc...

    async def delete_preset_by_id(self, mapping_id: str):
        async with self._session() as s:
            data = await self._delete_json(s, 'api/v1/presets/' + mapping_id, organization=self._org)
            deleted_mapping = MappingRoot.from_dict(data)
            logger.debug(f'Got {orjson.dumps(deleted_mapping)}')

            # TODO should check for equality, or better, set ids etc...


"""
curl ${CURL_ARGS} \
  https://auth.corvina${FACTORYAL_CORVINA_SUFFIX}/auth/realms/${FACTORYAL_CORVINA_ORG}/protocol/openid-connect/token \
  -H "Authorization: Basic $(echo -n ${FACTORYAL_CORVINA_USERNAME}:${FACTORYAL_CORVINA_TOKEN} | base64 -w0)" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=client_credentials&scope=org:${FACTORYAL_CORVINA_ORG}"

"""