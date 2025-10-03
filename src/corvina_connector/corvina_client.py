
import orjson
import aiohttp

from model.datamodel.datamodel_root import DataModelRoot
from model.mapping.mapping_root import MappingRoot


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

        self._jwt_token: str | None = None

    async def login(self):
        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(self._username, self._token)) as session:
            async with session.post(
                url=f'https://auth.corvina{self._corvina_suffix}/auth/realms/{self._org}/protocol/openid-connect/token',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=f'grant_type=client_credentials&scope=org:{self._org}'
            ) as req:
                token = await req.json(loads=orjson.loads)
                assert 'error' not in token, f'Cannot perform Corvina Login! Got {token}'
                self._jwt_token = token['access_token']

    @staticmethod
    async def _merge_pages(session: aiohttp.ClientSession, url: str) -> list[dict]:
        res = []
        cur_page = 0
        is_last_page = False
        while not is_last_page:
            async with session.get(url + f'&page={cur_page}') as req:
                data = await req.text()
                assert req.ok, f'Got {req.status} with body {data} while asking for {url}&page={cur_page}'
                json_data = orjson.loads(data)
                assert 'number' in json_data and 'data' in json_data and 'last' in json_data, f'Got invalid body {json_data}'

                res.extend(json_data['data'])
                is_last_page = json_data['last']
                cur_page += 1

        return res

    async def get_datamodels_by_name(self) -> dict[str, DataModelRoot]:
        async with aiohttp.ClientSession(headers={'Authorization': self._jwt_token or 'please-login'}) as session:
            data = await self._merge_pages(
                session,
                f'https://{self._corvina_prefix}corvina{self._corvina_suffix}/svc/mappings/api/v1/models?organization={self._org}'
            )
            items = [DataModelRoot.from_dict(i) for i in data]

        return {i.name: i for i in items}

    async def get_mappings_by_name(self) -> dict[str, MappingRoot]:
        async with aiohttp.ClientSession(headers={'Authorization': self._jwt_token or 'please-login'}) as session:
            data = await self._merge_pages(
                session,
                f'https://{self._corvina_prefix}corvina{self._corvina_suffix}/svc/mappings/api/v1/mappings?organization={self._org}'
            )
            items = [MappingRoot.from_dict(i) for i in data]

        return {i.name: i for i in items}


"""
curl ${CURL_ARGS} \
  https://auth.corvina${FACTORYAL_CORVINA_SUFFIX}/auth/realms/${FACTORYAL_CORVINA_ORG}/protocol/openid-connect/token \
  -H "Authorization: Basic $(echo -n ${FACTORYAL_CORVINA_USERNAME}:${FACTORYAL_CORVINA_TOKEN} | base64 -w0)" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=client_credentials&scope=org:${FACTORYAL_CORVINA_ORG}"

"""