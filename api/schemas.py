from pydantic import BaseModel
from typing import List, Optional

# Upload transcript
class TranscriptUploadRequest(BaseModel):
    title: str
    raw_text: str

class TranscriptUploadResponse(BaseModel):
    transcript_id: str
    status: str
    message: str

# Job status
class JobStatusResponse(BaseModel):
    transcript_id: str
    total: int
    completed: int
    failed: int
    pending: int

# Individual asset
class AssetResponse(BaseModel):
    asset_type: str   # linkedin, twitter, newsletter, seo
    content: str
    status: str       # pending, processing, complete, failed

# All assets for a transcript
class TranscriptAssetsResponse(BaseModel):
    transcript_id: str
    assets: List[AssetResponse]
