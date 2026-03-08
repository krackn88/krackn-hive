from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/krackn_hive"
    abandonment_ttl_seconds: int = 900
    global_budget_tokens: int = 100
    model_config = SettingsConfigDict(env_prefix="KRACKN_", env_file=".env", extra="ignore")


settings = Settings()
