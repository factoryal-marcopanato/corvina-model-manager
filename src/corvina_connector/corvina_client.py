
import orjson
import aiohttp
import logging

from model.datamodel.datamodel_root import DataModelRoot
from model.device.corvina_device import CorvinaDevice
from model.mapping.mapping_root import MappingRoot

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

    @staticmethod
    async def _merge_pages(session: aiohttp.ClientSession, url: str) -> list[dict]:
        res = []
        cur_page = 0
        is_last_page = False
        while not is_last_page:
            logger.debug(f'GET {url}&page={cur_page}')
            async with session.get(url + f'&page={cur_page}') as req:
                data = await req.text()
                assert req.ok, f'Got {req.status} with body {data} while asking for {url}&page={cur_page}'
                json_data = orjson.loads(data)
                assert 'number' in json_data and 'data' in json_data and 'last' in json_data, f'Got invalid body {json_data}'

                res.extend(json_data['data'])
                is_last_page = json_data['last']
                cur_page += 1

        return res

    @staticmethod
    async def _get_json(session: aiohttp.ClientSession, path: str, **kwargs) -> dict:
        async with session.get(path, params=kwargs) as req:
            data = await req.text()
            assert req.ok, f'Got {req.status} with body {data} while asking for {path}'
            return orjson.loads(data)

    def _session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            headers={'Authorization': self._jwt_token or 'please-login'},
            base_url=f'https://{self._corvina_prefix}corvina{self._corvina_suffix}/svc/mappings/'
        )

    async def _get_paged_obj(self, path: str) -> list[dict]:
        async with self._session() as session:
            return await self._merge_pages(session, path)

    async def get_devices_by_id(self) -> dict[str, CorvinaDevice]:
        logger.info('Querying Devices')
        async with self._session() as s:
            response = await self._get_json(s, 'api/v1/devices', organization=self._org, pageSize=10000)
            logger.debug(f'Got {orjson.dumps(response)}')

        fix_items = [CorvinaDevice.from_dict(i) for i in response['data']]
        return {i.id: i for i in fix_items}

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

    async def get_mappings_by_id(self) -> dict[str, MappingRoot]:
        logger.info('Querying Mappings')

        async with self._session() as s:
            response = await self._get_json(s, 'api/v1/mappings', organization=self._org, pageSize=10000)
            logger.debug(f'Got {orjson.dumps(response)}')

        fix_items = [MappingRoot.from_dict(i) for i in response['data']]
        return {i.id: i for i in fix_items}

        # api = MappingsApi(self._api_client)
        # mappings = await api.search_mapping(organization=self._org, page_size=1000)
        # return {m.id: m for m in mappings.data}


"""
curl ${CURL_ARGS} \
  https://auth.corvina${FACTORYAL_CORVINA_SUFFIX}/auth/realms/${FACTORYAL_CORVINA_ORG}/protocol/openid-connect/token \
  -H "Authorization: Basic $(echo -n ${FACTORYAL_CORVINA_USERNAME}:${FACTORYAL_CORVINA_TOKEN} | base64 -w0)" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=client_credentials&scope=org:${FACTORYAL_CORVINA_ORG}"

"""