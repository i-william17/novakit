from fastapi import APIRouter

class BaseController:
    router: APIRouter

    def register_routes(self) -> None:
        """
        Find methods with `_route_info` and register them to self.router.
        The decorated method still receives `self` when called by FastAPI,
        so route function must be async and accept (self, ...).
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_route_info"):
                for method, path, options in getattr(attr, "_route_info"):
                    # bind method to router
                    router_method = getattr(self.router, method)
                    # attach the function directly; FastAPI will call it and pass self implicitly
                    router_method(path, **options)(attr)
