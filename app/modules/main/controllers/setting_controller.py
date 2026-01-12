from fastapi import APIRouter, Depends, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.sessions import get_db
from app.core.base_controller import BaseController
from app.modules.main.services.setting_service import SettingService
from pydantic import ValidationError
from app.core.__config import config

from app.modules.main.hooks.settings_loader import SettingLoader

class SettingController(BaseController):

    def __init__(self):
        self.router = APIRouter(tags=["Settings"])
        self._register_routes()

    def _register_routes(self):
        r = self.router


        @r.get("/available", summary="List all setting files found in directory")
        async def list_available():
            """
            Scans the schema directory and returns available options.
            """
            available = SettingLoader.list_available()
            return self.payload_response(data=available)


        @r.get("/{category}", summary="Get settings for a specific category")
        async def get_settings(category: str, db: AsyncSession = Depends(get_db)):
            """
            Dynamically loads the class based on the URL slug.
            """

            definition = SettingLoader.get_definition_class(category.lower())

            if not definition:
                return self.error_response(
                    errors="Category not found",
                    message=f"Settings for '{category}' do not exist.",
                    status_code=status.HTTP_404_NOT_FOUND
                )


            service = SettingService(db)
            await service.ensure_settings(definition)
            data = await service.get_formatted_settings(definition.CATEGORY)

            return self.payload_response(data=data)


        @r.post("/{category}", summary="Update settings for a category")
        async def update_settings(
                category: str,
                payload: dict = Body(..., example={"key": "value"}),
                db: AsyncSession = Depends(get_db)
        ):



            definition = SettingLoader.get_definition_class(category.lower())

            if not definition:
                return self.error_response(
                    errors="Category not found",
                    message=f"Settings for '{category}' do not exist.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            service = SettingService(db)
            if hasattr(definition, "VALIDATOR_SCHEMA"):
                try:
                    current_values = await service.get_formatted_settings(definition.CATEGORY)
                    full_validation_data = {**current_values, **payload}
                    validated_data = definition.VALIDATOR_SCHEMA(**full_validation_data)
                except ValidationError as e:
                    errors = self.format_pydantic_errors(e.errors())
                    return self.error_response(
                        errors=errors
                    )
            updated_count = 0
            for key, value in payload.items():
                if await service.update_setting_value(key, value):
                    config.set_manual(key, value)
                    updated_count += 1

            return self.alertify_response(
                message=f"{category} settings updated successfully.",
                theme="success"
            )

controller = SettingController()
router = controller.router