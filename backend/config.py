from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM API
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_dir: str = "./backend/data/chroma_db"

    # Embedding
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_fallback: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Jobs
    job_ttl_seconds: int = 3600
    max_concurrent_jobs: int = 5

    # Email (Resend)
    resend_api_key: str = ""
    contact_email: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_enabled: bool = False

    # Supabase / Database
    supabase_url: str = ""
    supabase_secret_key: str = ""
    database_url: str = ""

    # LLM
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 2


settings = Settings()
