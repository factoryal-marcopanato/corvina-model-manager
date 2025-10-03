# import os
# import platform
# import re
# import zipfile
#
# import yaml
# 
# linux_path = re.compile(r"/mnt/([a-z])/(.*)")
# windows_path = re.compile(r"([a-zA-Z]):[/\\](.*)")
# var_to_replace_splitter = re.compile(r"(\${[A-Za-z][A-Za-z0-9_]*})")
# var_to_replace_pattern = re.compile(r"\${([A-Za-z][A-Za-z0-9_]*)}")
#
#
# class Loader(yaml.SafeLoader):
#     def __init__(self, stream):
#         self._root = os.path.split(stream.name)[0]
#         super(Loader, self).__init__(stream)
#
#     def _fix_filepath(self, filename: str):
#         platform_sys = platform.system()
#         if platform_sys == "Windows":
#             # when using /mnt/x/ on windows fix automatically
#             match = linux_path.match(filename)
#             return f"{match.groups()[0]}:/{match.groups()[1]}" if match else filename
#         elif platform_sys == "Linux":
#             # when using c:\ on linux and is a wsl environment
#             match = windows_path.match(filename)
#             if match:
#                 return (
#                     f"/mnt/{match.groups()[0]}/{match.groups()[1]}"
#                     if os.path.isdir(f"/mnt/{match.groups()[0]}")
#                     else filename
#                 )
#
#         return filename
#
#     def include(self, node):
#         filename = os.path.join(self._root, self.construct_scalar(node))
#         filename = self._fix_filepath(filename)
#         with open(filename, "r") as f:
#             return yaml.load(f, Loader)
#
#     def include_zip(self, node):
#         filepath = os.path.join(self._root, self.construct_scalar(node))
#         filepath = self._fix_filepath(filepath)
#         filename = os.path.basename(filepath)
#         assert filename.endswith('.zip'), "Cannot include zip that contains more than one file!"
#         with zipfile.ZipFile(filepath) as fzip:
#             with fzip.open(filename[:-4]) as f:
#                 return yaml.load(f, Loader)
#
#     def env(self, node):
#         return os.environ[self.construct_scalar(node)]
#
#     def env_strip(self, node):
#         return os.environ[self.construct_scalar(node)].strip(' \n')
#
#     def int_env(self, node):
#         return int(os.environ[self.construct_scalar(node)])
#
#     def to_bytes(self, node):
#         return self.construct_scalar(node).encode()
#
#     def include_as_bytes(self, node):
#         filename = os.path.join(self._root, self.construct_scalar(node))
#         filename = self._fix_filepath(filename)
#         with open(filename, "r") as f:
#             return f.read().encode()
#
#     def include_as_str(self, node):
#         filename = os.path.join(self._root, self.construct_scalar(node))
#         filename = self._fix_filepath(filename)
#         with open(filename, "r") as f:
#             return f.read()
#
#     def include_multiple(self, node):
#         files_to_read = [self._fix_filepath(os.path.join(self._root, f)) for f in self.construct_scalar(node).split(' ')]
#         res = ''
#         for f in files_to_read:
#             if f.endswith('.zip'):
#                 with zipfile.ZipFile(f) as fzip:
#                     filename = os.path.basename(f)
#                     with fzip.open(filename[:-4]) as fd:
#                         res += fd.read().decode() + '\n'
#             else:
#                 with open(f, "r") as fd:
#                     res += fd.read() +'\n'
#         return yaml.load(res, yaml.SafeLoader)
#
#     def replace_env(self, node):
#         raw_string = self.construct_scalar(node)
#         tokens = var_to_replace_splitter.split(raw_string)
#         replaced_tokens = []
#         for token in tokens:
#             match = var_to_replace_pattern.match(token)
#             replaced_tokens.append(os.environ[match.group(1)] if match is not None else token)
#
#         return "".join(replaced_tokens)
#
#
# Loader.add_constructor("!include", Loader.include)
# Loader.add_constructor("!include_zip", Loader.include_zip)
# Loader.add_constructor("!env", Loader.env)
# Loader.add_constructor("!env_strip", Loader.env_strip)
# Loader.add_constructor("!int_env", Loader.int_env)
# Loader.add_constructor("!to_bytes", Loader.to_bytes)
# Loader.add_constructor("!include_as_bytes", Loader.include_as_bytes)
# Loader.add_constructor("!include_as_str", Loader.include_as_str)
# Loader.add_constructor("!include_multiple", Loader.include_multiple)
# Loader.add_constructor("!replace_env", Loader.replace_env)