import asyncio
import argparse

import configuration
import utils.version_utils
import utils.logging_utils
from corvina_connector.corvina_client import CorvinaClient
from model.corvina_manager import CorvinaManager
from model.datamodel.datamodel_root import DataModelRoot
from model.mapping.mapping_root import MappingRoot
from utils.file_utils import read_json_async


l0 = utils.logging_utils.setup_logging()


def create_arguments_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'op', choices=['sync', 'remove'],
        help=(
            'The operation to perform, where: \n'
            '\t\tsync applies the provided model and mapping\n'
            '\t\tremove deletes model and mapping (name is took from provided files or by the --deploy-name arg)'
        )
    )
    parser.add_argument('-d', '--datamodel', required=False, type=str, help='Path of the datamodel.json file to handle (required when syncing)')
    parser.add_argument('-m', '--mapping', required=False, type=str, help='Path of the mapping.json file to handle (required when syncing)')
    parser.add_argument('--deploy-name', type=str, required=False)
    parser.add_argument('--dry_run', action='store_true', default=False, required=False)

    # TODO manca il device id dove applicare...

    args = parser.parse_args()

    # Validate arguments
    assert args.op != 'sync' or (args.datamodel and args.mapping), 'Datamodel and mapping files must be provided when syncing'
    assert args.op != 'remove' or ((args.datamodel and args.mapping) or args.deploy_name), 'Datamodel and mapping files or deploy-name must be provided when removing'

    return args


async def async_main():
    l0.info(f"Corvina Model Manager {utils.version_utils.get_version_and_date()}")

    configuration.validate_configuration()
    args = create_arguments_parser()

    connector = CorvinaClient(
        org=configuration.corvina_org,
        username=configuration.corvina_username,
        token=configuration.corvina_client_secret,
        corvina_prefix=configuration.corvina_prefix,
        corvina_suffix=configuration.corvina_suffix
    )
    await connector.login()
    manager = CorvinaManager(connector, args.dry_run)

    datamodel: DataModelRoot | None = None
    mapping: MappingRoot | None = None
    deploy_name: str | None = None

    if args.datamodel is not None:
        l0.info(f'Loading datamodel from {args.datamodel}')
        datamodel = DataModelRoot.from_dict(await read_json_async(args.datamodel))
        l0.debug(f'Datamodel deploy name: {datamodel.get_deploy_name()}')
    if args.mapping is not None:
        l0.info(f'Loading mapping from {args.mapping}')
        mapping = MappingRoot.from_dict(await read_json_async(args.mapping))
        l0.debug(f'Mapping deploy name: {mapping.get_deploy_name()}')
    if args.deploy_name is not None:
        l0.info(f'Using deploy name {args.deploy_name} from command line args')
        deploy_name = args.deploy_name

    assert (datamodel is None and mapping is None) or (datamodel is not None and mapping is not None), 'Provide always both datamodel and mapping or nothing, not a single one'
    assert datamodel is None or mapping is None or datamodel.get_deploy_name() == mapping.get_deploy_name(), f'Found different deploy names in loaded file! {datamodel.get_deploy_name()} != {mapping.get_deploy_name()}'

    assert deploy_name is None or datamodel is None or deploy_name == datamodel.get_deploy_name(), 'Provided deploy name does not match the loaded files one'

    if args.op == 'sync':
        l0.info('Syncing')
        await manager.add_deploy_from_files(datamodel, mapping)
    elif args.op == 'remove':
        if deploy_name is not None:
            l0.info(f'Removing deploy {deploy_name}')
            await manager.remove_deploy_by_name(deploy_name)
        else:
            l0.info(f'Removing deploy {mapping.get_deploy_name()} (from files)')
            await manager.remove_deploy_from_files(datamodel, mapping)
    else:
        l0.info('Nothing to do')

    # dm = DataModelRoot.from_dict(await read_json_async('sample_files/datamodel_1.json'))
    # mapping = MappingRoot.from_dict(await read_json_async('sample_files/mapping_1.json'))

    # await add_deploy_from_files(connector, dm, mapping)  # THIS WORKS!
    # await remove_deploy_from_files(connector, dm, mapping)  # ALSO THIS WORKS!

    # Allowed Operations
    # 1. sync
    # 2. delete (release name, only if non-used?)

    # Test 1: model creation
    # new_model_json = orjson.loads('{"name":"prova","data":{"type":"object","instanceOf":"prova","properties":{"a":'
    #                               '{"type":"integer"}},"label":"","unit":"","description":"","tags":[]}}')
    # new_model = DataModelRoot.from_dict(new_model_json)
    # # await connector.create_data_model(new_model)

    # Test 2: model deletion
    # await connector.delete_data_model_by_id('gKhpG9ktLF')

    # Test 3: remove models by name
    # models = await connector.get_datamodels_by_id()
    # for model in models.values():
    #     if (
    #         model.name.startswith('stupefied-galileo') or model.name.startswith('silly-greider') or
    #         model.name.startswith('vigilant-banach') or model.name.startswith('stupefied-traffic')
    #     ):
    #         continue
    #
    #     l0.info(f'Deleting model {model.name}')
    #     await connector.delete_data_model(model)

    # Test 4 Mapping/Preset creation (depends on test 1)
    # new_mapping_json = orjson.loads('{"name":"ProvaMapping","data":{'
    #                                 '"type":"object","instanceOf":"prova:1.0.0","properties":{'
    #                                     '"a":{'
    #                                         '"version":"1.0.0","type":"integer","mode":"R","historyPolicy":{"enabled":true},'
    #                                         '"sendPolicy":{"triggers":[{"changeMask":"value","minIntervalMs":1000,"skipFirstNChanges":0,"type":"onchange"}]}'
    #                                 ',"datalink":{"source":"Ent.S.A.Prova"}}},"label":"","unit":"","description":"","tags":[]}}')
    # new_mapping = MappingRoot.from_dict(new_mapping_json)
    # # await connector.create_preset(new_model, new_mapping)

    # Test 5 Mapping/Preset remove (depends on test 1 + 4)
    # await connector.delete_preset(new_mapping)

    # print(await connector.get_presets_by_id())

    # Every Factory-Modeler deploy has a name-prefix
    # What to do
    # 1. Get a model and a mapping from local files
    # 2. discover if model and mapping are already available in Corvina
    #    3a. new models! simply POST the new files...
    #    3b. compute differences and

    # datamodels = await connector.get_datamodels_by_id()  # TODO store also the corvina id since it is very very important!!!
    # mappings = await connector.get_mappings_by_id()
    # devices = await connector.get_devices_by_id()



    # print(orjson.dumps(datamodels))
    # print(orjson.dumps(mappings))
    # print(orjson.dumps(devices))

    l0.info("Bye")


def main():
    asyncio.new_event_loop().run_until_complete(async_main())


if __name__ == '__main__':
    main()
