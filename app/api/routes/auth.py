from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi import Request
from typing import Optional
from app.services.user_service import upsert_user

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

    try:
        user = upsert_user(
            user_id=payload.user_id,
            email=payload.email,
            full_name=payload.full_name,
        )

        return {
            "status": "ok",
            "provider": payload.provider,
            "user": user,
        }

    except Exception as e:
        print("❌ AUTH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Auth failed")


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

    try:
        full_name = " ".join(
            name for name in [oauth_data.first_name, oauth_data.last_name] if name
        )

        user = upsert_user(
            user_id=oauth_data.user_id,
            email=oauth_data.email,
            full_name=full_name or None,
        )

        return {
            "status": "ok",
            "provider": oauth_data.provider,
            "user": user,
        }

    except Exception as e:
        print("❌ AUTH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Auth failed")

