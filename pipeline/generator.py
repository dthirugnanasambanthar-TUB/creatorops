import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ASSET_PROMPTS = {
    "linkedin": "Write a LinkedIn post of 150-300 words. Open with a hook, share 3 key insights, end with a question to drive engagement. Use line breaks for readability.",
    "twitter": "Write a Twitter thread of 5 tweets. Each tweet under 280 characters. Separate tweets with | character. Start each with the tweet number e.g. 1/5:",
    "newsletter": "Write a newsletter intro of 100-200 words that summarises the episode and teases what the reader will learn.",
    "seo": "Write an SEO-optimised article intro of 150-250 words. Include the main keyword naturally 2-3 times. End with a clear thesis statement."
}

def generate_asset(
    raw_text: str,
    asset_type: str,
    brand_voice_exemplars: list[str] = None
) -> str:
    
    style_instruction = ""
    if brand_voice_exemplars:
        examples = "\n\n".join(brand_voice_exemplars)
        style_instruction = f"""
Write in this person's style. Here are examples of their writing:

{examples}

Match their tone, vocabulary, and sentence structure.
"""

    prompt = f"""You are a content repurposing assistant.

{style_instruction}

Based on this transcript:
{raw_text[:2000]}

{ASSET_PROMPTS[asset_type]}

Return only the content. No explanation, no preamble."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()