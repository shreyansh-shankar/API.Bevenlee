from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Backend"
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Supabase configuration
    SUPABASE_PROJECT_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Creem configuration
    CREEM_API_KEY: str
    CREEM_WEBHOOK_SECRET: str
    CREEM_TEST_MODE: bool = True
    CREEM_API_BASE: str = "https://test-api.creem.io"
    CREEM_PRODUCT_ID_PRO_MONTHLY: str
    CREEM_PRODUCT_ID_PRO_YEARLY: str
    CREEM_PRODUCT_ID_PREMIUM_MONTHLY: str
    CREEM_PRODUCT_ID_PREMIUM_YEARLY: str
    APP_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False  # This allows lowercase env vars to match uppercase field names

settings = Settings()