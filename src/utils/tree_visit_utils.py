import collections.abc

import configuration
from model.tree.tree_node import TreeNode


recursive_fun = collections.abc.Callable[[TreeNode, str], bool]
recursive_fun_async = collections.abc.Callable[[TreeNode, str], collections.abc.Awaitable[bool]]


def path_append(path: str, tail: str) -> str:
    return tail if path == '' else f'{path}{configuration.tree_path_separator_char}{tail}'


def dfs(root: TreeNode, fun: recursive_fun):
    _dfs_aux(root, '', fun)


def _dfs_aux(root: TreeNode, path: str, fun: recursive_fun) -> bool:
    if not fun(root, path):
        return False

    return all(_dfs_aux(c, path_append(path, root.get_tree_node_name()), fun) for c in root.get_tree_node_children().values())


async def dfs_async(root: TreeNode, fun: recursive_fun_async):
    await _dfs_async_aux(root, '', fun)


async def _dfs_async_aux(root: TreeNode, path: str, fun: recursive_fun_async) -> bool:
    if not await fun(root, path):
        return False

    for child in root.get_tree_node_children().values():
        if not await _dfs_async_aux(child, path_append(path, root.get_tree_node_name()), fun):
            return False
    return True


def bfs(root: TreeNode, fun: recursive_fun):
    if not fun(root, ''):
        return

    if not all(fun(child, path_append('', root.get_tree_node_name())) for child in root.get_tree_node_children().values()):
        return
    all(_bfs_aux(child, path_append('', root.get_tree_node_name()), fun) for child in root.get_tree_node_children().values())


def _bfs_aux(root: TreeNode, path: str, fun: recursive_fun) -> bool:
    if not all(fun(child, path_append(path, root.get_tree_node_name())) for child in root.get_tree_node_children().values()):
        return False
    return all(_bfs_aux(child, path_append(path, root.get_tree_node_name()), fun) for child in root.get_tree_node_children().values())


async def bfs_async(root: TreeNode, fun: recursive_fun_async):
    if not await fun(root, ''):
        return

    for child in root.get_tree_node_children().values():
        if not await fun(child, path_append('', root.get_tree_node_name()),):
            return

    for child in root.get_tree_node_children().values():
        if not await _bfs_async_aux(child, path_append('', root.get_tree_node_name()), fun):
            return


async def _bfs_async_aux(root: TreeNode, path: str, fun: recursive_fun_async) -> bool:
    for child in root.get_tree_node_children().values():
        if not await fun(child, path_append(path, root.get_tree_node_name())):
            return False

    for child in root.get_tree_node_children().values():
        if not await _bfs_async_aux(child, path_append(path, root.get_tree_node_name()), fun):
            return False

    return True
