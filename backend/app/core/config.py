from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "moonshotai/kimi-k2.6"
    nvidia_fallback_model: str = "meta/llama-3.1-70b-instruct"

    database_url: str = "postgresql+asyncpg://delivery_health:delivery_health@localhost:5432/delivery_health"

    use_mock_data: bool = True

    github_token: str = ""
    github_repo: str = ""

    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""

    cors_origins: str = "http://localhost:5173"

    # Per-IP requests/minute allowed on POST /api/chat. 0 or negative disables the limit.
    chat_rate_limit_per_minute: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
