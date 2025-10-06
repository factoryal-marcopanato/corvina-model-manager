import asyncio

import configuration
import utils.version_utils
import utils.logging_utils
from corvina_connector.corvina_client import CorvinaClient
from model.datamodel.datamodel_root import DataModelRoot
from model.mapping.mapping_root import MappingRoot
from utils.file_utils import read_json_async

l0 = utils.logging_utils.setup_logging()


async def add_deploy_from_files(connector: CorvinaClient, data_model: DataModelRoot, mapping: MappingRoot):
    l0.info('Creating Deploy from provided files')

    # TODO should check that objs already exists...

    l0.info('Model and mapping not found in Corvina!')

    l0.info(f'Creating model {data_model.name}')
    await connector.create_data_model(data_model)

    l0.info(f'Creating mapping {mapping.name} for model {mapping.data.instanceOf}')
    await connector.create_preset(data_model, mapping)


async def remove_deploy_from_files(connector: CorvinaClient, data_model: DataModelRoot, mapping: MappingRoot):
    l0.info('Removing Deploy from provided files')

    all_sub_models = set(data_model.get_intermediate_elems())
    datamodels_to_remove = [data_model]
    datamodels_to_remove.extend(await connector.get_datamodels_from_names(all_sub_models))

    l0.info(f'Will remove the following models:  {[m.name for m in datamodels_to_remove]}')
    l0.info(f'Will remove the following mapping: {mapping.name} on model {mapping.data.instanceOf}')

    l0.info(f'Deleting mapping {mapping.name} on model {mapping.data.instanceOf}')
    try:
        await connector.delete_preset(mapping)
    except:
        l0.exception(f'Cannot delete mapping {mapping.name} on model {mapping.data.instanceOf}')

    for model in datamodels_to_remove:
        l0.info(f'Deleting model {model.name}:{model.version}')
        try:
            await connector.delete_data_model(model)
        except:
            l0.exception(f'Cannot delete model {model.name}:{model.version}')


async def remove_deploy(connector: CorvinaClient, deploy_name: str):
    l0.info(f'Removing Deploy {deploy_name}')

    models = await connector.get_datamodels_by_id()
    models_to_remove = [m for m in models.values() if m.name.startswith(deploy_name + '-')]

    mappings = await connector.get_presets_by_id()
    mappings_to_remove = [m for m in mappings.values() if m.data.instanceOf.startswith(deploy_name + '-')]

    l0.info(f'Will remove the following models:   {[m.name for m in models_to_remove]}')
    # TODO but there is a single mapping.. This should work, but can be optimized
    l0.info(f'Will remove the following mappings: {[(m.name + ":" + m.data.instanceOf) for m in mappings_to_remove]}')

    for mapping in mappings_to_remove:
        l0.info(f'Deleting mapping {mapping.name} on model {mapping.data.instanceOf}')
        try:
            await connector.delete_preset(mapping)
        except:
            l0.exception(f'Cannot delete mapping {mapping.name} on model {mapping.data.instanceOf}')

    for model in models_to_remove:
        l0.info(f'Deleting model {model.name}:{model.version}')
        try:
            await connector.delete_data_model(model)
        except:
            l0.exception(f'Cannot delete model {model.name}:{model.version}')


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
    # l0.debug('Token ' + connector._jwt_token)

    dm = DataModelRoot.from_dict(await read_json_async('sample_files/datamodel_1.json'))
    mapping = MappingRoot.from_dict(await read_json_async('sample_files/mapping_1.json'))

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
