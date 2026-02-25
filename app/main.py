from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth
from app.api.routes import course
from app.api.routes import user
from app.api.routes import billing

app = FastAPI(title=settings.PROJECT_NAME)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(course.router, prefix="/course", tags=["course"])
app.include_router(user.router, prefix="", tags=["user"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])

@app.get("/")
async def root():
    return {"message": "Welcome to API.Bevenlee"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}