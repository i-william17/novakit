from typing import Callable

def route(method: str, path: str, **options):
    """
    Decorator for controller methods.
    method: "get", "post", "put", "delete", etc.
    path: path under module prefix (e.g. "/login")
    options: passed to router.<method>
    """
    method = method.lower()

    def decorator(func: Callable):
        if not hasattr(func, "_route_info"):
            func._route_info = []
        func._route_info.append((method, path, options))
        return func

    return decorator
