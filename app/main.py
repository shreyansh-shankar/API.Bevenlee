from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth
from app.api.routes import course

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

@app.get("/")
async def root():
    return {"message": "Welcome to API.Bevenlee"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}