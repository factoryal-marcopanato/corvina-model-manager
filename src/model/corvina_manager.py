
import logging

from corvina_connector.corvina_client import CorvinaClient
from model.datamodel.datamodel_root import DataModelRoot
from model.mapping.mapping_root import MappingRoot

logger = logging.getLogger('app.model_manager')


class CorvinaManager:

    def __init__(self, connector: CorvinaClient):
        self._connector = connector

    async def add_deploy_from_files(self, data_model: DataModelRoot, mapping: MappingRoot):
        logger.info('Creating Deploy from provided files')

        # TODO should check that objs already exists...

        logger.info('Model and mapping not found in Corvina!')

        logger.info(f'Creating model {data_model.name}')
        await self._connector.create_data_model(data_model)

        logger.info(f'Creating mapping {mapping.name} for model {mapping.data.instanceOf}')
        await self._connector.create_preset(data_model, mapping)

    async def remove_deploy_from_files(self, data_model: DataModelRoot, mapping: MappingRoot):
        logger.info('Removing Deploy from provided files')

        all_sub_models = set(data_model.get_intermediate_elems())
        datamodels_to_remove = [data_model]
        datamodels_to_remove.extend(await self._connector.get_datamodels_from_names(all_sub_models))

        logger.info(f'Will remove the following models:  {[m.name for m in datamodels_to_remove]}')
        logger.info(f'Will remove the following mapping: {mapping.name} on model {mapping.data.instanceOf}')

        logger.info(f'Deleting mapping {mapping.name} on model {mapping.data.instanceOf}')
        try:
            await self._connector.delete_preset(mapping)
        except:
            logger.exception(f'Cannot delete mapping {mapping.name} on model {mapping.data.instanceOf}')

        for model in datamodels_to_remove:
            logger.info(f'Deleting model {model.name}:{model.version}')
            try:
                await self._connector.delete_data_model(model)
            except:
                logger.exception(f'Cannot delete model {model.name}:{model.version}')

    async def remove_deploy_by_name(self, deploy_name: str):
        logger.info(f'Removing Deploy {deploy_name}')

        models = await self._connector.get_datamodels_by_id()
        models_to_remove = [m for m in models.values() if m.name.startswith(deploy_name + '-')]

        mappings = await self._connector.get_presets_by_id()
        mappings_to_remove = [m for m in mappings.values() if m.data.instanceOf.startswith(deploy_name + '-')]

        logger.info(f'Will remove the following models:   {[m.name for m in models_to_remove]}')
        # TODO but there is a single mapping.. This should work, but can be optimized
        logger.info(
            f'Will remove the following mappings: {[(m.name + ":" + m.data.instanceOf) for m in mappings_to_remove]}')

        for mapping in mappings_to_remove:
            logger.info(f'Deleting mapping {mapping.name} on model {mapping.data.instanceOf}')
            try:
                await self._connector.delete_preset(mapping)
            except:
                logger.exception(f'Cannot delete mapping {mapping.name} on model {mapping.data.instanceOf}')

        for model in models_to_remove:
            logger.info(f'Deleting model {model.name}:{model.version}')
            try:
                await self._connector.delete_data_model(model)
            except:
                logger.exception(f'Cannot delete model {model.name}:{model.version}')
