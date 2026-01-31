from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi import Request
from typing import Optional

router = APIRouter()

# Request models
class OAuthSigninRequest(BaseModel):
    user_id: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    provider: str

class EmailSigninRequest(BaseModel):
    user_id: str
    email: EmailStr
    full_name: Optional[str] = None
    provider: str = "email"

@router.post("/email")
async def email_signin(payload: EmailSigninRequest):
    print("=" * 50)
    print("EMAIL SIGNIN")
    print("User ID:", payload.user_id)
    print("Email:", payload.email)
    print("Full Name:", payload.full_name)
    print("Provider:", payload.provider)
    print("=" * 50)

    # 🔒 SAME LOGIC AS OAUTH
    # 1. user = get_user_by_supabase_id(payload.user_id)
    # 2. if not exists -> create user
    # 3. else -> update last_login
    # 4. provider = "email"

    return {
        "status": "ok",
        "user_id": payload.user_id,
        "provider": payload.provider,
    }


@router.post("/oauth")
async def oauth_signin(oauth_data: OAuthSigninRequest):
    print("=" * 50)
    print("OAUTH SIGNIN REQUEST RECEIVED")
    print("User ID:", oauth_data.user_id)
    print("Email:", oauth_data.email)
    print("First Name:", oauth_data.first_name)
    print("Last Name:", oauth_data.last_name)
    print("Provider:", oauth_data.provider)
    print("=" * 50)

    # TODO:
    # 1. Check if user exists (by user_id)
    # 2. If not -> create user
    # 3. Return success

    return {
        "status": "ok",
        "message": "OAuth user accepted",
        "user_id": oauth_data.user_id,
    }

