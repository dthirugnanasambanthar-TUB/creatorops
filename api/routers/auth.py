import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.auth import hash_password, verify_password, create_token
from supabase import create_client

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(request: RegisterRequest):
    existing = supabase.table("users") \
        .select("id") \
        .eq("email", request.email) \
        .execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hash_password(request.password)
    supabase.table("users").insert({
        "email": request.email,
        "hashed_password": hashed
    }).execute()
    
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(request: LoginRequest):
    result = supabase.table("users") \
        .select("*") \
        .eq("email", request.email) \
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = result.data[0]
    
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token({"sub": user["id"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer"}