import copy
import functools
import logging
import collections.abc

from corvina_connector.corvina_client import CorvinaClient
from model.datamodel.datamodel_leaf import DataModelLeaf
from model.datamodel.datamodel_root import DataModelRoot
from model.mapping.mapping_root import MappingRoot
from model.semver_version import SemverVersion
from model.tree.intermediate_node import IntermediateNode
from model.tree.tree_node import TreeNode
from utils.corvina_version_utils import version_re
from utils.tree_visit_utils import dfs, path_append

logger = logging.getLogger('app.model_manager')


class CorvinaManager:

    def __init__(self, connector: CorvinaClient, dry_run: bool):
        self._connector = connector
        self._dry_run = dry_run
        self._all_models_by_id: dict[str, DataModelRoot] | None = None
        self._all_mappings_by_id: dict[str, MappingRoot] | None = None
        if dry_run:
            logger.warning('Dry Run Mode ON! Nothing on Corvina will be set')

    async def add_deploy_from_files(self, data_model: DataModelRoot, mapping: MappingRoot):
        logger.info('Creating Deploy from provided files')

        self._all_models_by_id = await self._connector.get_datamodels_by_id()
        matching_models = list(filter(lambda m: data_model.clear_name == m.name, self._all_models_by_id.values()))

        if len(matching_models) > 1:
            # TODO this is probably not supported (or not possible?)
            assert False, f'Found more than one already existing models that match provided one... {matching_models}'

        if len(matching_models) > 0:
            logger.info(f'Model found in Corvina (id={matching_models[0].id})! Performing automatic migration')
            # new_data_model = await self._perform_model_upgrade(matching_models[0], data_model)
            if not self._dry_run:
                new_data_model = await self._connector.update_data_model(matching_models[0], data_model)
                # TODO do something also for the mapping part
        else:
            logger.info('Model and mapping not found in Corvina!')
            await self._create_new_model_and_mapping(data_model, mapping)

    async def remove_deploy_from_files(self, data_model: DataModelRoot, mapping: MappingRoot):
        # TODO this is not safe to remove model with a version > 1.0.0 (which is not detected)
        logger.info('Removing Deploy from provided files')

        all_sub_models = set(data_model.get_intermediate_elems())
        datamodels_to_remove = [data_model]
        datamodels_to_remove.extend(await self._get_datamodels_from_names(all_sub_models))

        logger.info(f'Will remove the following models:  {[m.clear_name + ":" + m.version for m in datamodels_to_remove]}')
        logger.info(f'Will remove the following mapping: {mapping.name} on model {mapping.data.instanceOf}')

        logger.info(f'Deleting mapping {mapping.name} on model {mapping.data.instanceOf}')
        if not self._dry_run:
            try:
                await self._connector.delete_preset(mapping)
            except:
                logger.exception(f'Cannot delete mapping {mapping.name} on model {mapping.data.instanceOf}')

        for model in datamodels_to_remove:
            logger.info(f'Deleting model {model.name}:{model.version}')
            if not self._dry_run:
                try:
                    await self._connector.delete_data_model(model)
                except:
                    logger.exception(f'Cannot delete model {model.name}:{model.version}')

    async def remove_deploy_by_name(self, deploy_name: str):
        logger.info(f'Removing Deploy {deploy_name}')

        self._all_models_by_id = await self._connector.get_datamodels_by_id()
        models_to_remove = [m for m in self._all_models_by_id.values() if m.name.startswith(deploy_name + '-')]

        self._all_mappings_by_id = await self._connector.get_presets_by_id()
        mappings_to_remove = [m for m in self._all_mappings_by_id.values() if m.data.instanceOf.startswith(deploy_name + '-')]

        logger.info(f'Will remove the following models:  {[m.clear_name + ":" + m.version for m in models_to_remove]}')
        # TODO but there is a single mapping.. This should work, but can be optimized
        logger.info(f'Will remove the following mappings: {[(m.name + ":" + m.data.instanceOf) for m in mappings_to_remove]}')

        for mapping in mappings_to_remove:
            logger.info(f'Deleting mapping {mapping.name} on model {mapping.data.instanceOf}')
            if not self._dry_run:
                try:
                    await self._connector.delete_preset(mapping)
                except:
                    logger.exception(f'Cannot delete mapping {mapping.name} on model {mapping.data.instanceOf}')

        for model in models_to_remove:
            logger.info(f'Deleting model {model.name}:{model.version}')
            if not self._dry_run:
                try:
                    await self._connector.delete_data_model(model)
                except:
                    logger.exception(f'Cannot delete model {model.name}:{model.version}')

    async def _create_new_model_and_mapping(self, model: DataModelRoot, mapping: MappingRoot):
        logger.info(f'Creating model {model.name}')
        if not self._dry_run:
            await self._connector.create_data_model(model)

        logger.info(f'Creating mapping {mapping.name} for model {mapping.data.instanceOf}')
        if not self._dry_run:
            await self._connector.create_preset(model, mapping)

    async def _get_datamodels_from_names(self, names: collections.abc.Iterable[str]) -> list[DataModelRoot]:
        if self._all_models_by_id is None:
            self._all_models_by_id = await self._connector.get_datamodels_by_id()

        res = []
        for name in names:
            match = version_re.match(name)
            if match is not None: # split model name and version
                m_name = match[1]
                m_version = match[2]
                found_dms = [dm for dm in self._all_models_by_id.values() if dm.name == m_name and dm.version == m_version]
            else:  # remove ALL found versions for that name
                found_dms = [dm for dm in self._all_models_by_id.values() if dm.name == name]

            if len(found_dms) > 0:  # more than one datamodel can be found (e.g. more than one version available)
                res.extend(found_dms)
        return res

    @staticmethod
    def _model_version_dict_builder(target_dict: dict[str, SemverVersion], node: TreeNode, path: str) -> bool:
        if isinstance(node, DataModelRoot):
            target_dict[path_append(path, node.get_tree_node_name())] = SemverVersion.from_string(node.version)
        elif isinstance(node, IntermediateNode):
            target_dict[path_append(path, node.get_tree_node_name())] = SemverVersion.from_instance_of_string(node.instanceOf)
        elif isinstance(node, DataModelLeaf):
            target_dict[path_append(path, node.get_tree_node_name())] = SemverVersion.from_string(node.version)
        return True

    async def _perform_model_upgrade(self, corvina_current_model: DataModelRoot, new_model: DataModelRoot):
        if self._all_models_by_id is None:
            self._all_models_by_id = await self._connector.get_datamodels_by_id()

        models_by_name_and_version: dict[str, DataModelRoot] = {
            f'{m.clear_name}:{m.version}': m for m in self._all_models_by_id.values()
        }

        # Compute Initial State Versions # TODO probably useless
        # corvina_current_model_versions_by_path: dict[str, SemverVersion] = {}
        # dfs(corvina_current_model, functools.partial(self._model_version_dict_builder, corvina_current_model_versions_by_path))
        # original_corvina_current_model_versions_by_path = copy.deepcopy(corvina_current_model_versions_by_path)

        # IDEA: compute the difference graph of the two models, then apply new models using a DFS on the graph
        new_model_copy = copy.deepcopy(new_model)

