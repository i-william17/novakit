from fastapi import APIRouter
from typing import List, Optional

def create_module_router(module: str, tags: Optional[List[str]] = None) -> APIRouter:
    prefix = f"/v1/{module}"
    return APIRouter(prefix=prefix, tags=tags or [module.capitalize()])
