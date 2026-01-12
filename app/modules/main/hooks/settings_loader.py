import os
import importlib
import inspect
import pkgutil
from typing import List, Type, Optional, Dict


SETTINGS_PACKAGE = "app.modules.main.schemas.settings"
BASE_CLASS_NAME = "BaseSettingGroup"


class SettingLoader:
    @staticmethod
    def _get_package_path():
        """Helper to get the filesystem path of the settings package."""
        try:
            module = importlib.import_module(SETTINGS_PACKAGE)
            return module.__path__[0]
        except ImportError:
            return None

    @classmethod
    def list_available(cls) -> List[Dict[str, str]]:
        """
        Scans the directory and returns all available setting modules.
        """
        package_path = cls._get_package_path()
        if not package_path:
            return []

        available = []

        for _, name, _ in pkgutil.iter_modules([package_path]):
            if name in ["base", "__init__"]:
                continue

            #'
            label = name.replace("_", " ").title()
            available.append({"id": name, "label": label})

        return available

    @classmethod
    def get_definition_class(cls, slug: str):

        try:

            module_name = f"{SETTINGS_PACKAGE}.{slug}"
            module = importlib.import_module(module_name)


            for name, obj in inspect.getmembers(module, inspect.isclass):

                if (getattr(obj, "CATEGORY", None)
                        and obj.__module__ == module_name):
                    return obj

        except ImportError:
            return None
        return None