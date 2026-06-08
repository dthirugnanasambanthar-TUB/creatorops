from fastapi import FastAPI
from api.routers import transcripts
from api.routers import auth

app = FastAPI(
    title="CreatorOps API",
    description="AI-powered content repurposing engine",
    version="0.1.0"
)

app.include_router(auth.router)
app.include_router(transcripts.router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}