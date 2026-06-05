from pydantic import BaseModel
from typing import List
import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TRANSCRIPT_TEMPLATES = [
    {"topic": "remote work productivity", "tone": "casual", "duration_mins": 15},
    {"topic": "personal finance for millennials", "tone": "educational", "duration_mins": 20},
    {"topic": "climate change solutions", "tone": "urgent", "duration_mins": 25},
    {"topic": "startup fundraising mistakes", "tone": "storytelling", "duration_mins": 30},
    {"topic": "mental health in the workplace", "tone": "empathetic", "duration_mins": 20},
    {"topic": "future of artificial intelligence", "tone": "analytical", "duration_mins": 35},
    {"topic": "sustainable living tips", "tone": "casual", "duration_mins": 15},
    {"topic": "leadership lessons from failure", "tone": "storytelling", "duration_mins": 25},
]

class GroundTruth(BaseModel):
    linkedin: str
    twitter: str
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

def generate_single_transcript(note_number: int, template: dict) -> TranscriptData:
    prompt = f"""Generate a realistic synthetic podcast transcript for a public knowledge platform.
Return ONLY valid JSON. No explanation, no markdown, no code blocks. Just the raw JSON object.

You MUST use these details:
- Topic: {template['topic']}
- Tone: {template['tone']}
- Duration: approximately {template['duration_mins']} minutes of spoken content

The JSON must match this exact structure:
{{
    "transcript_id": "transcript_{note_number:03d}",
    "title": "A specific, compelling title about {template['topic']}",
    "topic": "{template['topic']}",
    "tone": "{template['tone']}",
    "duration_mins": {template['duration_mins']},
    "raw_text": "A realistic podcast transcript of at least 400 words. Use natural speech patterns, include specific examples, data points, and actionable insights about {template['topic']}. Write in a {template['tone']} tone. Include filler words like 'you know', 'right', 'so' to make it feel real.",
    "key_points": [
        "A specific, concrete insight from the transcript",
        "A second distinct insight with a specific example or data point",
        "A third actionable takeaway the audience can apply"
    ],
    "ground_truth": {{
        "linkedin": "A {template['tone']} LinkedIn post of 150-300 words that opens with a hook, shares the 3 key insights from the transcript, and ends with a question to drive engagement. Use line breaks for readability.",
        "twitter": "Tweet 1/5: Hook tweet under 280 chars\\nTweet 2/5: First insight under 280 chars\\nTweet 3/5: Second insight under 280 chars\\nTweet 4/5: Third insight under 280 chars\\nTweet 5/5: CTA tweet under 280 chars",
        "newsletter": "A {template['tone']} newsletter intro of 100-200 words that summarises the episode and teases what the reader will learn. Written for an engaged subscriber audience.",
        "seo": "An SEO-optimised article intro of 150-250 words about {template['topic']}. Include the main keyword naturally 2-3 times. End with a clear thesis statement for the article."
    }}
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )

    raw_output = response.choices[0].message.content.strip()
    raw_output = raw_output.replace('\n', ' ').replace('\r', '')  # add this
    data = json.loads(raw_output)
    transcript = TranscriptData(**data)
    transcript.transcript_id = f"transcript_{note_number:03d}"
    return transcript

if __name__ == "__main__":
    transcripts = []
    total = len(TRANSCRIPT_TEMPLATES)

    for i, template in enumerate(TRANSCRIPT_TEMPLATES, start=1):
        print(f"Generating transcript {i}/{total} ({template['topic']})...", end=" ")
        try:
            transcript = generate_single_transcript(i, template)
            transcripts.append(transcript.model_dump())
            print("✓")
        except Exception as e:
            print(f"✗ failed: {e}")
        time.sleep(1)

    output_path = "fixtures/transcripts/synthetic_transcripts.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(transcripts, f, indent=2)

    print(f"\nDone. {len(transcripts)} transcripts saved to {output_path}")