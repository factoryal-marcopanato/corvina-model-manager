import orjson
import aiofiles


async def read_file_async(path: str) -> str:
    async with aiofiles.open(path, 'r') as fd:
        return await fd.read()


async def read_json_async(path: str) -> dict:
    async with aiofiles.open(path, 'r') as fd:
        return orjson.loads(await fd.read())
