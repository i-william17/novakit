from fastapi import APIRouter, Depends
from app.core.security.oauth import oauth2_scheme


def create_module_router(
    module: str,
    tags=None,

):
    """
    Creates a router with prefix: /v1/<module>

    protected=True  → adds Authorization: Bearer
    protected=False → public routes
    """

    return APIRouter(
        tags=tags or [module.capitalize()],
    )
