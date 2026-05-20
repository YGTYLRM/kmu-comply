from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM API
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"

    # ChromaDB — set CHROMA_SERVER_URL to switch from embedded to server mode
    # e.g. CHROMA_SERVER_URL=http://chroma:8001
    # When unset, uses embedded PersistentClient at chroma_persist_dir
    chroma_server_url: str = ""
    chroma_persist_dir: str = "./backend/data/chroma_db"

    # Embedding
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_fallback: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Jobs
    job_ttl_seconds: int = 3600
    max_concurrent_jobs: int = 5

    # Redis + Celery (leave empty to use in-process asyncio fallback)
    redis_url: str = ""                    # e.g. redis://localhost:6379/0
    celery_concurrency: int = 2            # worker processes per Celery worker

    # Documents — persistent vault (separate TTL from jobs)
    document_store_dir: str = "./backend/data/documents"
    document_ttl_seconds: int = 7 * 24 * 3600  # 7 days

    # Email (Resend)
    resend_api_key: str = ""
    contact_email: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_enabled: bool = False

    # Supabase / Database
    supabase_url: str = ""
    supabase_service_role_key: str = ""  # Full admin key — bypasses RLS, never expose to clients
    database_url: str = ""

    # Observability
    sentry_dsn: str = ""   # Set to enable Sentry error tracking

    # Admin API key — required for regulation update approval endpoints
    admin_api_key: str = ""

    # Document encryption (Fernet key for uploaded company files at rest)
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # If unset, an ephemeral key is generated per process (fine for dev; set in production)
    document_encryption_key: str = ""

    # Deployment environment — set to "production" in prod to enable hard startup checks
    environment: str = "development"

    # CORS (comma-separated list of allowed origins)
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"

    # Reverse proxy trusted hosts (comma-separated IPs or "*" for dev)
    # In production, set to your actual proxy IP(s) to prevent X-Forwarded-For spoofing
    proxy_trusted_hosts: str = "*"

    # LLM
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 4

    # PDF generation concurrency limit
    # 2 is the safe default for an 8GB VPS: each Playwright/Chromium render uses ~2GB RAM.
    # 3 concurrent renders = ~6GB, leaving only 2GB for the rest of the stack.
    pdf_concurrency: int = 2


settings = Settings()
