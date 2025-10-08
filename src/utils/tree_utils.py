
from model.datamodel.datamodel_leaf import DataModelLeaf
from model.node_diff import NodeDiff, DiffEnum
from model.tree.intermediate_node import IntermediateNode
from model.tree.root_node import RootNode
from model.tree.tree_leaf import TreeLeaf
from model.tree.tree_node import TreeNode
from model.datamodel.datamodel_root import DataModelRoot
from utils.tree_visit_utils import path_append


def go_to_path(root: TreeNode, path: list[str]) -> TreeNode:
    token = path[0]
    return go_to_path(root.get_tree_node_children()[token], path[1:])


def compute_data_model_difference_map(current_model: DataModelRoot, new_model: DataModelRoot) -> dict[str, NodeDiff]:
    assert current_model.clear_name == new_model.clear_name, 'This function is not compatible with models with different name!'

    map_dict: dict[str, NodeDiff] = {}
    if current_model.version != new_model.version:
        map_dict[current_model.name] = NodeDiff(DiffEnum.NODE_CHANGED, new_model, new_model.name)

    _compute_data_model_difference_map_aux(
        map_dict,
        new_model.name,
        new_model.name,
        current_model.data,
        new_model.data
    )

    return map_dict


def _compute_data_model_difference_map_aux(
    map_dict: dict[str, NodeDiff], path: str, current_node_name: str, current_node: TreeNode, new_node: TreeNode
) -> bool:
    current_node_type = get_node_type(current_node)
    new_node_type = get_node_type(new_node)
    if current_node_type != new_node_type:  # Corner case?
        map_dict[path] = NodeDiff(DiffEnum.NODE_CHANGED, new_node, path_append(path, current_node_name))
        return False

    # Leaf base case
    if isinstance(new_node, DataModelLeaf):  # and isinstance(current_node, TreeLeaf): # (redundant since they have the same type)
        if current_node != new_node:
            # map_dict[path_append(path, current_node_name)] = NodeDiff(DiffEnum.LEAF_CHANGED, new_node)  # Useless
            return False
        return True

    # Recursive case
    cur_child_names = set(current_node.get_tree_node_children().keys())
    new_node_child_names = set(new_node.get_tree_node_children().keys())

    common_child_names = new_node_child_names.intersection(cur_child_names)
    removed_child_names = cur_child_names.difference(common_child_names)
    new_child_names = new_node_child_names.difference(common_child_names)

    for removed_child_name in removed_child_names:
        child = current_node.get_tree_node_children()[removed_child_name]
        if not is_leaf(child):
            map_dict[path_append(path, removed_child_name)] = NodeDiff(DiffEnum.DELETED_NODE, child, path_append(path, removed_child_name))
    for new_child_name in new_child_names:
        child = new_node.get_tree_node_children()[new_child_name]
        if not is_leaf(child):
            map_dict[path_append(path, new_child_name)] = NodeDiff(DiffEnum.NEW_NODE, child, path_append(path, new_child_name))

    res = len(common_child_names) == len(new_node_child_names) == len(cur_child_names)  # Start True if children have same names
    for common_child_name in common_child_names:
        res = _compute_data_model_difference_map_aux(
            map_dict,
            path_append(path, common_child_name),
            common_child_name,
            current_node.get_tree_node_children()[common_child_name],
            new_node.get_tree_node_children()[common_child_name]
        ) and res

    if not res:
        map_dict[path] = NodeDiff(DiffEnum.NODE_CHANGED, new_node, path)

    return res


A = """
						TreeNode

IntermediateNode				RootNode                                   TreeLeaf

RootNodeAux                     DataModelRoot               MappingRoot                 DataModelLeaf
 
                                                                                          TreeLeaf
"""

def get_node_type(node: TreeNode) -> str:
    if isinstance(node, RootNode):
        return 'root'
    elif isinstance(node, TreeLeaf):
        return 'leaf'
    elif isinstance(node, IntermediateNode):
        return node.type
    else:
        assert False, f'Unknown node type {node}'


def is_leaf(node: TreeNode) -> bool:
    return get_node_type(node) == 'leaf'
