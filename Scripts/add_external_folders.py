import os
import sys

plugin_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
ext_paths = [
    os.path.join(plugin_root, "external_modules"),
    os.path.join(plugin_root, "ExternalModules", "Python3"),
    os.path.join(os.path.dirname(__file__), "UserInterfaces"),
    os.path.dirname(__file__),
]

for p in ext_paths:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
