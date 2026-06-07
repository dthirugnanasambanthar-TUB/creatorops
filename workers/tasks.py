import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from workers.celery_app import celery_app
from pipeline.generator import generate_asset
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@celery_app.task(bind=True, max_retries=3)
def generate_asset_task(self, transcript_id: str, asset_type: str, user_id: str):
    try:
        # Step 1: update asset status to "processing"
        supabase.table("assets")\
            .update({"status": "processing"})\
            .eq("transcript_id", transcript_id)\
            .eq("asset_type", asset_type)\
            .execute()

        # Step 2: fetch transcript
        result = supabase.table("transcripts")\
            .select("raw_text")\
            .eq("id", transcript_id)\
            .execute()
        
        raw_text = result.data[0]["raw_text"]

        # Step 3: fetch brand voice if exists
        voice_result = supabase.table("brand_voices")\
            .select("exemplars")\
            .eq("user_id", user_id)\
            .execute()
        
        exemplars = voice_result.data[0]["exemplars"] if voice_result.data else None

        # Step 4: generate content
        content = generate_asset(raw_text, asset_type, exemplars)

        # Step 5: update asset with content and status complete
        supabase.table("assets")\
            .update({"content": content, "status": "complete"})\
            .eq("transcript_id", transcript_id)\
            .eq("asset_type", asset_type)\
            .execute()

        return {"asset_type": asset_type, "status": "complete"}

    except Exception as e:
        # Update status to failed
        supabase.table("assets")\
            .update({"status": "failed", "content": str(e)})\
            .eq("transcript_id", transcript_id)\
            .eq("asset_type", asset_type)\
            .execute()
        raise self.retry(exc=e, countdown=5)

@celery_app.task
def on_chord_complete(results, transcript_id: str):
    completed = sum(1 for r in results if r and r.get("status") == "complete")
    total = len(results)
    print(f"Chord complete: {completed}/{total} assets generated for {transcript_id}")