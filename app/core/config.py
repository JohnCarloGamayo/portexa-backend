from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / '.env'), extra='allow')

    app_name: str = 'Portexa API'
    env: str = 'development'

    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60

    database_url: str

    cors_origins: str = ''

    max_login_attempts: int = 3
    lockout_minutes: int = 30

    # Google OAuth
    google_client_id: str = ''
    google_client_secret: str = ''

    # OpenRouter AI
    openrouter_api_key: str = ''
    openrouter_model: str = 'openai/gpt-4o-mini'
    openrouter_base_url: str = 'https://openrouter.ai/api/v1'
    openrouter_app_url: str = ''
    openrouter_app_name: str = 'Portexa AI'


settings = Settings()
