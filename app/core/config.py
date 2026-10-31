
from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Configuration
    app_name: str = "Nagarik AI API"
    app_env: str = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 5000
    secret_key: SecretStr | None = None
    
    # Google OAuth Configuration
    google_client_id: str = ""

    # PostgreSQL Configuration
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_database: str = "nagarik_ai"
    postgres_user: str = "nagarik_user"
    postgres_password: SecretStr | None = None

    # Qdrant Configuration
    qdrant_url: str = ""
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "nagarik_ai_local"

    # OpenAI Configuration
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.2

    # Gemini Configuration
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.2

    # Groq Configuration
    groq_api_key: SecretStr | None = None
    groq_model: str = "gpt-4o-mini"
    groq_temperature: float = 0.2

    # LLM Provider Selection
    llm_provider: str = "groq"
    llm_model_name: str | None = None

    # Embedding Configuration
    embedding_model: str = "intfloat/multilingual-e5-base"

    # Retrieval Configuration
    top_k_results: int = 5

    # Rate Limiting
    rate_limit: int = 100
    rate_limit_period: int = 60

    # CORS Configuration
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"local", "staging", "production", "test"}
        value = value.lower()

        if value not in allowed:
            raise ValueError(
                f"APP_ENV must be one of: {', '.join(sorted(allowed))}"
            )

        return value

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, value: str) -> str:
        value = value.lower()
        allowed = {"openai", "gemini", "groq"}

        if value not in allowed:
            raise ValueError(
                f"LLM_PROVIDER must be one of: {', '.join(sorted(allowed))}"
            )

        return value

    @property
    def database_url(self) -> str:
        """Build a SQLAlchemy PostgreSQL connection URL."""
        from urllib.parse import quote_plus

        if self.postgres_password is None:
            raise ValueError("POSTGRES_PASSWORD must be configured")

        user = quote_plus(self.postgres_user)
        password = quote_plus(
            self.postgres_password.get_secret_value()
        )
        database = quote_plus(self.postgres_database)

        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{database}"
        )

    # Compatibility aliases for the existing service modules.
    @property
    def HOST(self) -> str:
        return self.host

    @property
    def PORT(self) -> int:
        return self.port

    @property
    def DEBUG(self) -> bool:
        return self.debug
    
    @property
    def GOOGLE_CLIENT_ID(self) -> str:
        return self.google_client_id

    @property
    def QDRANT_URL(self) -> str:
        return self.qdrant_url

    @property
    def QDRANT_API_KEY(self) -> str | None:
        return (
            self.qdrant_api_key.get_secret_value()
            if self.qdrant_api_key
            else None
        )

    @property
    def EMBEDDING_MODEL(self) -> str:
        return self.embedding_model

    @property
    def LLM_PROVIDER(self) -> str:
        return self.llm_provider

    @property
    def GROQ_API_KEY(self) -> str | None:
        return (
            self.groq_api_key.get_secret_value()
            if self.groq_api_key
            else None
        )

    @property
    def GROQ_MODEL(self) -> str:
        return self.groq_model

    @property
    def GROQ_TEMPERATURE(self) -> float:
        return self.groq_temperature

    @property
    def GEMINI_API_KEY(self) -> str | None:
        return (
            self.gemini_api_key.get_secret_value()
            if self.gemini_api_key
            else None
        )

    @property
    def GEMINI_MODEL(self) -> str:
        return self.gemini_model

    @property
    def GEMINI_TEMPERATURE(self) -> float:
        return self.gemini_temperature

    @property
    def TOP_K_RESULTS(self) -> int:
        return self.top_k_results

    @property
    def RATE_LIMIT(self) -> int:
        return self.rate_limit

    @property
    def RATE_LIMIT_PERIOD(self) -> int:
        return self.rate_limit_period



@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings()


# Convenient shared instance for existing imports
settings = get_settings()
config = settings
