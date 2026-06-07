import json
from pipeline.generator import generate_asset

with open(r"fixtures\transcripts\labelled_transcripts.json") as f:
    transcripts = json.load(f)

transcript = transcripts[0]
result = generate_asset(transcript["raw_text"], "twitter")
print(result)