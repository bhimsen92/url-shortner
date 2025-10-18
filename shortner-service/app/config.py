import os
from pathlib import Path
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

CONFIG_FILE_PATH: str = Path(os.environ["CONFIG_FILE_PATH"])


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

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # jwt specific
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_duration_minutes: int

    id_counter_key: str
    id_counter_batch_size: int
    hash_id_counter_secret: str
    base_url: str = "http://localhost"

    redis_host: str
    redis_user: str
    redis_password: str
    click_analytics_topic: str
    click_analytics_consumer_group: str
    click_analytics_batch_count: int

    API_V1: str = "/api/v1"

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
                config_path=CONFIG_FILE_PATH,
                settings_cls=settings_cls,
            ),
            file_secret_settings,
        )

    @property
    def sqlalchemy_database_uri(self):
        return (
            f"postgresql+psycopg2://"
            f"{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self):
        return f"redis://{self.redis_user}:{self.redis_password}@{self.redis_host}"


settings: Settings = Settings()
