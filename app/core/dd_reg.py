import importlib
import pkgutil
from fastapi import APIRouter
from config.config import settings

def register_routes(app):
    base_package = "app.modules"

    # /v1 prefix
    api_router = APIRouter(prefix=settings.API_V1_STR)

    package = importlib.import_module(base_package)

    for module_info in pkgutil.iter_modules(package.__path__):
        module_name = module_info.name
        module_path = f"{base_package}.{module_name}"

        try:
            submodule = importlib.import_module(f"{module_path}.controllers.http")
        except ModuleNotFoundError:
            continue

        for controller_info in pkgutil.iter_modules(submodule.__path__):
            ctrl_name = controller_info.name

            # example: user_controller, role_controller
            ctrl_path = f"{module_path}.controllers.http.{ctrl_name}"

            try:
                ctrl_module = importlib.import_module(ctrl_path)
            except Exception as e:
                print(f"Failed loading controller {ctrl_path}: {e}")
                continue

            # It must expose "router"
            router = getattr(ctrl_module, "router", None)
            if router:
                tag_name = module_name.upper()  # IAM, BILLING, BOOKINGS

                # Auto-apply tag to all routes
                for route in router.routes:
                    if not route.tags:
                        route.tags = [tag_name]

                # Mount under /v1/iam/
                api_router.include_router(
                    router, prefix=f"/{module_name}"
                )
                print(f"Loaded: /{module_name} from {ctrl_path}")

    # Add whole API router to app
    app.include_router(api_router)
