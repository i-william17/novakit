from pydantic_settings import BaseSettings


class ConsoleConfig(BaseSettings):
    """
    Yii2-inspired console configuration for NovaKit.
    Handles CLI commands, cron jobs, workers, migrations etc.
    """

    # ----------------------------
    # ENVIRONMENT (from .env)
    # ----------------------------
    ENVIRONMENT: str = "local"

    # ----------------------------
    # CONTROLLERS (Yii2 style)
    # ----------------------------
    CONTROLLER_NAMESPACE: str = "app.console.controllers"

    CONTROLLER_MAP: dict = {
        "nova.py": {
            "class": "app.console.controllers.NovaController",
            "migration_path": "app/migrations",
            "template_file": "app/templates/migration.py",
        },
        "ws": {
            "class": "app.console.controllers.WebsocketServerController",
        },
        "jobs": {
            "class": "app.console.controllers.JobController",
        },
        "backup": {
            "class": "app.console.controllers.BackupController",
        },
    }

    # ----------------------------
    # COMPONENTS (Yii2-like)
    # ----------------------------
    COMPONENTS: dict = {
        "backup": {
            "class": "app.core.BackupService",
            "backup_dir": "app/providers/bin",
            "compression": "zip",
            "databases": ["default"],
        }
    }

    # ----------------------------
    # PARAMS
    # ----------------------------
    PARAMS_PATH: str = "app/core/config/params.py"

    # ----------------------------
    # ENVIRONMENT OVERRIDES
    # ----------------------------
    def environment_overrides(self):
        """
        Yii2-style behavior, injects env-based tweaks.
        """
        if self.ENVIRONMENT == "development":
            return {
                "enable_reloader": True,
                "debug_cli": True,
            }
        return {}

    
