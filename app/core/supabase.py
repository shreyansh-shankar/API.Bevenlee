from supabase import create_client, Client
from app.core.config import settings

supabase: Client = create_client(
    settings.SUPABASE_PROJECT_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,  # IMPORTANT: service role on backend
)
