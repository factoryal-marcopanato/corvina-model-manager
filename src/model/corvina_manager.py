import copy
import functools
import logging
import collections.abc

import orjson

import configuration
from corvina_connector.corvina_client import CorvinaClient
from model.datamodel.datamodel_leaf import DataModelLeaf
from model.datamodel.datamodel_root import DataModelRoot
from model.mapping.mapping_root import MappingRoot
from model.node_diff import NodeDiff, DiffEnum
from model.semver_version import SemverVersion
from model.tree.intermediate_node import IntermediateNode
from model.tree.tree_node import TreeNode
from utils.corvina_version_utils import version_re
from utils.tree_utils import compute_data_model_difference_map
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
            # new_data_model = await self._connector.update_data_model(matching_models[0], data_model)
            new_data_model = await self._perform_model_upgrade(matching_models[0], data_model)
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
        logger.info(f'Creating model {model.name} {model.version}')
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
            else:  # return ALL found versions for that name
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

    # @staticmethod
    # def _a(map_dict: dict[str, NodeDiff], node: TreeNode, path: str) -> bool:
    #     if isinstance(node, DataModelRoot):
    #         target_dict[path_append(path, node.get_tree_node_name())] = SemverVersion.from_string(node.version)
    #     elif isinstance(node, IntermediateNode):
    #         target_dict[path_append(path, node.get_tree_node_name())] = SemverVersion.from_instance_of_string(
    #             node.instanceOf)
    #     elif isinstance(node, DataModelLeaf):
    #         target_dict[path_append(path, node.get_tree_node_name())] = SemverVersion.from_string(node.version)
    #     return True

    async def _perform_model_upgrade(self, corvina_current_model: DataModelRoot, new_model: DataModelRoot) -> DataModelRoot:
        if self._all_models_by_id is None:
            self._all_models_by_id = await self._connector.get_datamodels_by_id()

        logger.info('Computing differences between old and new models')
        diff_map = compute_data_model_difference_map(corvina_current_model, new_model)
        logger.debug(orjson.dumps(diff_map))

        logger.info('Sorting differences by inverse depth')
        differences_by_level: dict[int, list[NodeDiff]] = {}
        for idd, diff in diff_map.items():
            depth_index = idd.count(configuration.tree_path_separator_char) + 1
            if depth_index not in differences_by_level: differences_by_level[depth_index] = []
            differences_by_level[depth_index].append(diff)
        logger.debug(orjson.dumps({str(k): v for (k,v) in differences_by_level.items()}))
        diff_depths = sorted(differences_by_level.keys(), reverse=True)

        for depth in diff_depths:
            logger.info(f'Parsing depth {depth}')
            for diff in differences_by_level[depth]:
                logger.debug(f'Parsing diff {orjson.dumps(diff)}')
                if diff.op == DiffEnum.NEW_NODE:
                    assert isinstance(diff.node, IntermediateNode)
                    logger.info(f'Creating model {diff.node.get_tree_node_name()} {diff.node.get_node_version()}')
                    if not self._dry_run:
                        created_model = await self._connector.create_data_model(DataModelRoot.from_intermediate_node(diff.node))
                        diff.new_version = created_model.version
                    else:
                        diff.new_version = '9.9.9'
                elif diff.op == DiffEnum.DELETED_NODE:
                    assert isinstance(diff.node, IntermediateNode)
                    logger.info(f'Deleting model {diff.node.get_tree_node_name()} {diff.node.get_node_version()}')
                    if not self._dry_run:
                        await self._connector.delete_data_model(DataModelRoot.from_intermediate_node(diff.node))
                    # TODO store the created model version in current datamodel...
                    # TODO should check all child elements... HELP!!!
                elif diff.op == DiffEnum.NODE_CHANGED:
                    assert isinstance(diff.node, IntermediateNode)
                    logger.debug(f'Extracting model id from {diff.node.get_tree_node_name()}')
                    old_models = await self._get_datamodels_from_names([diff.node.get_tree_node_name()])
                    assert len(old_models) > 0 and old_models[0].id is not None, f'Cannot find id for {diff.node.get_tree_node_name()}! Found {old_models}'

                    # Fix the node to apply!
                    if depth < len(diff_depths):
                        sublevel_diffs = differences_by_level[depth + 1]
                        cur_node_children = diff.node.get_tree_node_children()
                        for sublevel_diff in sublevel_diffs:
                            if sublevel_diff.new_version is not None:
                                # Set new version!
                                child_name = sublevel_diff.path.split(configuration.tree_path_separator_char)[-1]
                                if child_name not in cur_node_children:
                                    continue
                                child_node = cur_node_children[child_name]
                                assert isinstance(child_node, IntermediateNode)
                                child_node.instanceOf = child_node.get_tree_node_name() + ':' + sublevel_diff.new_version

                    logger.info(f'Upgrading model (id={old_models[0].id}) {diff.node.get_tree_node_name()} {diff.node.get_node_version()}')
                    if not self._dry_run:
                        upgraded_model = await self._connector.update_data_model_by_id(
                            old_models[0].id, DataModelRoot.from_intermediate_node(diff.node)
                        )
                        logger.info(f'New version of {diff.node.get_tree_node_name()} is {upgraded_model.version}!')
                        diff.new_version = upgraded_model.version
                    else:
                        diff.new_version = '9.9.9'
                else:
                    assert False, f'Invalid op? {diff.op}'

        # TODO set the new version of the "new_model" obj

        return new_model
