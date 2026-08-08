import importlib
import pkgutil
import processes.telegram.hooks

def register_hooks():
    for module_info in pkgutil.walk_packages(
            processes.telegram.hooks.__path__,
            processes.telegram.hooks.__name__ + "."
    ):
        importlib.import_module(module_info.name)