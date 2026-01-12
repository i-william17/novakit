from typing import Callable
from fastapi import APIRouter, Depends

from app.core.router import create_module_router

def route(method: str, path: str, *, auth: bool | None = None, **options):
    """
    Decorator for controller methods.
    """
    method = method.lower()

    def decorator(func: Callable):
        if not hasattr(func, "_route_info"):
            func._route_info = []
        func._route_info.append((method, path, auth, options))
        return func

    return decorator


class BaseController:
    module: str = None
    tags: list[str] | None = None

    router: APIRouter

    def __init__(self):
        if not self.module:
            raise RuntimeError(
                f"{self.__class__.__name__} must define `module`"
            )

        self.router = create_module_router(
            module=self.module,
            tags=self.tags,
        )

        self.register_routes()

    def register_routes(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)

            if callable(attr) and hasattr(attr, "_route_info"):
                for method, path, auth, options in attr._route_info:
                    getattr(self.router, method)(path, **options)(attr)
