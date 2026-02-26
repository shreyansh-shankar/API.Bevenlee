from fastapi import Header, HTTPException
from app.core.config import settings
from supabase import create_client

def verify_token(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Ask Supabase to verify the token for us
        supabase = create_client(
            settings.SUPABASE_PROJECT_URL,
            settings.SUPABASE_ANON_KEY
        )
        response = supabase.auth.get_user(token)
        
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        return {"sub": response.user.id, "email": response.user.email}
        
    except HTTPException:
        raise
    except Exception as e:
        print("❌ AUTH ERROR:", repr(e))
        raise HTTPException(status_code=401, detail="Invalid token")