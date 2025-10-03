import asyncio

import orjson

import configuration
import utils.version_utils
import utils.logging_utils
from corvina_connector.corvina_client import CorvinaClient

l0 = utils.logging_utils.setup_logging()


async def async_main():
    l0.info(f"Corvina Model Manager {utils.version_utils.get_version_and_date()}")

    connector = CorvinaClient(
        org=configuration.corvina_org,
        username=configuration.corvina_username,
        token=configuration.corvina_token,
        corvina_prefix=configuration.corvina_prefix,
        corvina_suffix=configuration.corvina_suffix
    )

    await connector.login()
    l0.info('Token ' + connector._jwt_token)

    datamodels = await connector.get_datamodels_by_name()  # TODO store also the corvina id since it is very very important!!!
    mappings = await connector.get_mappings_by_name()
    print(orjson.dumps(datamodels))
    print(orjson.dumps(mappings))

    # config_file_path = os.environ.get("CONFIG_FILE_PATH", "/app/config/config.yaml")
    # l0.info(f"Loading configuration from {config_file_path}")
    # with open(config_file_path, "r", encoding='utf-8') as fd:
    #     config = yaml.load(fd, utils.yaml_include_loader.Loader)
    #
    # l0.debug("Registering signal handler callback")
    # evt = asyncio.Event()
    # # asyncio.get_running_loop().add_signal_handler(signal.SIGINT, lambda e: e.set(), evt)
    # # asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, lambda e: e.set(), evt)

    # l0.info("Starting app modules")
    # app_core = FactorySchedulerBackendCore(config)
    # assert await app_core.start(), "Core is not started correctly!!!"
    #
    # if configuration.start_compute_on_start:
    #     l0.info("Waiting 1 second then start computing schedule")
    #     await asyncio.sleep(1)
    #     asyncio.create_task(app_core.scheduler.start_computing(app_core.environment.draft_schedule))
    #
    # l0.info("Ready")
    # await evt.wait()
    #
    # l0.info("Stopping modules")
    # await app_core.stop()

    l0.info("Bye")


def main():
    asyncio.new_event_loop().run_until_complete(async_main())


if __name__ == '__main__':
    main()
