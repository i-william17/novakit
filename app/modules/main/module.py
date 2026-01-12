# from fastapi import FastAPI
#
# class Module:
#     name: str
#
#     def register(self, app: FastAPI):
#         pass
#
#     def migrations_path(self) -> str | None:
#         return None
#
#
# class IAMModule(Module):
#     name = "iam"
#
#     def register(self, app: FastAPI):
#         from .router import router
#         app.include_router(router, prefix="/iam")
#
#     def migrations_path(self):
#         return "app/modules/iam/migrations"
#
#
# def load_modules(app):
#     modules = [
#         IAMModule(),
#         MainModule(),
#     ]
#
#     for module in modules:
#         module.register(app)
class Module:
    name = "main"
    depends_on = []
