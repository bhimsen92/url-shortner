from typing import Any

import yaml
from pathlib import Path

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource
from fastapi.templating import Jinja2Templates


class YamlConfig(PydanticBaseSettingsSource):
    def __init__(self, config_path: Path, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        if not config_path.exists():
            raise ValueError(f"Config file does not exist: {config_path}.")

        self.config_data = yaml.safe_load(config_path.read_text())

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        pass

    def __call__(self, *args, **kwargs) -> dict[str, Any]:
        return self.config_data


class Settings(BaseSettings):
    environment: str
    secret_key: str

    shortner_service: str
    session_cookie: str
    cookie_max_age: int

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            YamlConfig(
                config_path=Path(__file__).parent.parent / "config.yaml",
                settings_cls=settings_cls,
            ),
            file_secret_settings,
        )


settings = Settings()
templates = Jinja2Templates(directory="app/templates")
