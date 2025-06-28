import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = Field(default=5432, ge=1024, le=65535)

    REDIS_PASSWORD: str

    TELEGRAM_BOT_TOKEN: str
    TWO_CAPTCHA_KEY: str

    EUR_RATE: float = Field(default=94.04, gt=0)
    KRW_RATE: float = Field(default=0.06058, gt=0)

    ADMIN_IDS: List[int] = Field(default_factory=list)

    LOG_CHAT_ID: int
    STATEMENT_CHAT_ID: int
    STATISTICS_CHAT_ID: int

    LOG_LEVEL: str = Field(default='INFO')

    @field_validator('ADMIN_IDS', mode='before')
    def parse_admin_ids(cls, value: Union[str, int, List[int]]) -> List[int]:
        if isinstance(value, list):
            return value
        if isinstance(value, int):
            return [value]
        if not value:
            return []

        return json.loads(value)

    @property
    def DATABASE_URL(self) -> str:
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:5432/{self.POSTGRES_DB}'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True
    )


settings = Settings()
