from model.tree.tree_node import TreeNode
from model.datamodel.datamodel_root import DataModelRoot


def go_to_path(root: TreeNode, path: list[str]) -> TreeNode:
    token = path[0]
    return go_to_path(root.get_tree_node_children()[token], path[1:])


def compute_data_model_difference_tree(current_model: DataModelRoot, new_model: DataModelRoot) -> DataModelRoot:
    pass


def _compute_data_model_difference_tree_aux(current_model: DataModelRoot, new_model: DataModelRoot) -> DataModelRoot:
    pass

A = """
						TreeNode

IntermediateNode				RootNode                                   TreeLeaf

RootNodeAux                     DataModelRoot               MappingRoot                 DataModelLeaf
 
                                                                                          TreeLeaf


"""