import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException, Depends
from api.schemas import (
    TranscriptUploadRequest, TranscriptUploadResponse,
    JobStatusResponse, TranscriptAssetsResponse, AssetResponse
)
from supabase import create_client
from dotenv import load_dotenv
from celery import chord
from workers.tasks import generate_asset_task, on_chord_complete

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

router = APIRouter(prefix="/api/v1", tags=["transcripts"])

@router.post("/transcripts", response_model=TranscriptUploadResponse)
async def upload_transcript(
    request: TranscriptUploadRequest,
):
    user_id = "00000000-0000-0000-0000-000000000001"

    
    # Step 1: store transcript in Supabase
    result = supabase.table("transcripts").insert({
        "user_id": user_id,
        "title": request.title,
        "raw_text": request.raw_text,
        "word_count": len(request.raw_text.split())
    }).execute()
    
    transcript_id = result.data[0]["id"]
    
    asset_types = ["linkedin","twitter","newsletter","seo"]
    asset_rows = []
    
    for asset_type in asset_types:
        asset_rows.append({
            "transcript_id": transcript_id,
            "user_id": user_id,
            "asset_type":asset_type,
            "content": "",
            "job_id": "",
            "status" : "pending"
            })
        
    supabase.table("assets").insert(asset_rows).execute()
    
    chord(
        [generate_asset_task.s(transcript_id, asset_type, user_id) 
         for asset_type in asset_types],
        on_chord_complete.s(transcript_id)
    ).apply_async()
    
    
    return TranscriptUploadResponse(
        transcript_id=transcript_id,
        status="queued",
        message=f"Transcript uploaded, generating 4 assets"
    )

@router.get("/transcripts/{transcript_id}/assets", response_model=TranscriptAssetsResponse)
async def get_assets(
    transcript_id: str,
):
    result = supabase.table("assets") \
        .select("*") \
        .eq("transcript_id", transcript_id) \
        .execute()
    
    assets = [AssetResponse(
        asset_type=row["asset_type"],
        content=row["content"],
        status=row["status"]
    ) for row in result.data]
    
    return TranscriptAssetsResponse(
    transcript_id=transcript_id,
    assets=assets
)


@router.get("/transcripts/{transcript_id}/status", response_model=JobStatusResponse)
async def get_status(
    transcript_id: str,
):
    result = supabase.table("assets") \
        .select("*") \
        .eq("transcript_id", transcript_id) \
        .execute()
        
    assets = [AssetResponse(
        asset_type=row["asset_type"],
        content=row["content"],
        status=row["status"]
    ) for row in result.data]
    
    total = len(assets)
    completed = 0
    failed = 0
    pending = 0
    
    for item in assets:
        status = item.status 
        if status == 'complete':
            completed += 1
        elif status == 'failed':
            failed += 1
        elif status == 'pending':
            pending += 1
            
    
    return JobStatusResponse(
    transcript_id=transcript_id,
    total=total,
    completed = completed,
    failed= failed,
    pending= pending
)


