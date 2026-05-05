from enum import Enum
from typing import Any
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    # Read .env and parse values
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # General information
    APP_NAME: str = "mj-database-2027"
    DESCRIPTION: str = "Polls compatible with majority judgement for french politics"
    CONTACT: dict = {
        "name": "Pierre Puchaud",
        "url": "https://github.com/Ipuch",
        "email": "pierre.puchaud@inria.fr",
    }
    LICENSE_INFO: dict = {
        "name": "The MIT License (MIT)",
        "url": "https://opensource.org/license/mit",
    }

    # Logging information by default
    LOG_LEVEL: LogLevel = LogLevel.INFO

    # timezone
    TZ: str = "UTC"


class RuntimeSettings(Settings):
    # Reads .env (runtime/default)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class TestSettings(Settings):
    # Ignores .env (unit tests)
    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
    )


@lru_cache
def get_settings(*, read_env: bool = True, **overrides: Any) -> Settings:
    """
    Runtime: get_settings()               -> reads .env (cached).
    Tests:   get_settings(read_env=False) -> ignores .env; pass overrides explicitly.
    """
    cls = TestSettings if not read_env else RuntimeSettings
    return cls(**overrides)
