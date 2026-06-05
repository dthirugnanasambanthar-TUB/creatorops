from pydantic import BaseModel
from typing import List
import os
import json
import time
from groq import Groq
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Reuse your existing models
class GroundTruth(BaseModel):
    linkedin: str
    twitter: Optional[str] = None
    newsletter: str
    seo: str

class TranscriptData(BaseModel):
    transcript_id: str
    title: str
    topic: str
    tone: str
    duration_mins: int
    raw_text: str
    key_points: List[str]
    ground_truth: GroundTruth

def estimate_duration(text: str) -> int:
    word_count = len(text.split())
    return max(1, round(word_count / 130))

def truncate_text(text: str, max_words: int = 1500) -> str:
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return text

def label_transcript(transcript_id: str, raw_text: str) -> TranscriptData:
    truncated_text = truncate_text(raw_text)
    prompt = f"""# Using the podcast transcript provided generate a synthetic JSON transcript for a public knowledge platform.
Return ONLY valid JSON. No explanation, no markdown, no code blocks. Just the raw JSON object.

    
    The transcript text is:
    {truncated_text}
    
    Return ONLY valid JSON matching this exact structure:
    {{
        "title": "available in {truncated_text}",
        "topic": "topic that matches the content provided in the {truncated_text}",
        "tone": "tone of the speaker derived from {truncated_text}",
        "key_points": [        "A specific, concrete insight from the transcript",
        "A second distinct insight with a specific example or data point",
        "A third actionable takeaway the audience can apply"],
        "ground_truth": {{"linkedin": "A LinkedIn post of 150-300 words that opens with a hook, shares 3 key insights, ends with a question to drive engagement.",
        "twitter": "A thread of 5 tweets about this topic. Each tweet under 280 characters. Separate tweets with | character.",
"newsletter": "A newsletter intro of 100-200 words that summarises the episode and teases what the reader will learn.",
"seo": "An SEO-optimised article intro of 150-250 words. Include the main keyword naturally 2-3 times. End with a clear thesis statement."}}
    }}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    
    raw_output = response.choices[0].message.content.strip()
    raw_output = raw_output.replace('\n', ' ').replace('\r', '')  # add this
    data = json.loads(raw_output)
    
    print(json.dumps(data["ground_truth"], indent=2))
    
    return TranscriptData(
        transcript_id=transcript_id,
        raw_text=raw_text,
        duration_mins=estimate_duration(raw_text),
        title= data["title"],
        topic= data["topic"],
        tone= data["tone"],
        key_points= data["key_points"],
        ground_truth=GroundTruth(**data["ground_truth"])
    )

if __name__ == "__main__":
    transcripts_dir = "fixtures/transcripts"
    results = []
    
    # Loop through all .txt files in the directory
    for filename in os.listdir(transcripts_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(transcripts_dir, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                transcript_id = filename.replace(".txt", "")
                transcript = label_transcript(filename, raw_text=content)
                results.append(transcript.model_dump())
            pass
    
    output_path = "fixtures/transcripts/labelled_transcripts.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Done. {len(results)} transcripts labelled.")