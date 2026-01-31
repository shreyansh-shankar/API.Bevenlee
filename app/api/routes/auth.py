from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi import Request

router = APIRouter()

# Request models
class OAuthSigninRequest(BaseModel):
    user_id: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    provider: str


@router.post("/email")
async def email_signin(payload: dict):
    print("=" * 50)
    print("EMAIL SIGNIN")
    print("User ID:", payload.get("user_id"))
    print("Email:", payload.get("email"))
    print("Provider:", payload.get("provider"))
    print("=" * 50)

    # same logic as OAuth:
    # - check if user exists
    # - create if not
    # - link supabase_user_id

    return {"status": "ok"}


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

