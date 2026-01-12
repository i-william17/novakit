import importlib
import pkgutil
import logging
from fastapi import FastAPI

logger = logging.getLogger("router.loader")

def discover_and_register(app: FastAPI, modules_pkg="app.modules"):
    """
    Discover packages under app.modules.* and import controllers subpackages.
    Each controller module should export `router` (APIRouter instance).
    """
    pkg = importlib.import_module(modules_pkg)
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        module_pkg = f"{modules_pkg}.{name}.controllers"
        try:
            controllers_pkg = importlib.import_module(module_pkg)
        except ModuleNotFoundError:
            logger.debug("Module %s has no controllers package; skipping", name)
            continue
        # import each module in controllers package
        if hasattr(controllers_pkg, "__path__"):
            for _, sub_name, _ in pkgutil.iter_modules(controllers_pkg.__path__):
                full = f"{module_pkg}.{sub_name}"
                try:
                    mod = importlib.import_module(full)
                except Exception:
                    logger.exception("Failed to import controller %s", full)
                    continue

                # register router if provided
                router = getattr(mod, "router", None)
                if router:
                    # prefix already baked into module router
                    app.include_router(router)
                    logger.info("Registered router %s -> %s", full, getattr(router, "prefix", "<no-prefix>"))
