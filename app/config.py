from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_expiration_minutes: int = 30
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
