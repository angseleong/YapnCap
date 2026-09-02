import json
from dataclasses import dataclass
from pydantic import BaseModel, Field
from yapncap.config import YapnCapConfig

@dataclass
class ClaimResult:
    claim: str
    verdict: str
    correction: str
    source: str
    time_start: str
    time_end: str

class ClaimResultSchema(BaseModel):
    claim: str = Field(description="The original claim extracted from the transcript")
    verdict: str = Field(description="Must be exactly one of: NO CAP, CAP, YAPPIN")
    correction: str = Field(description="The actual truth or clarification")
    source: str = Field(description="Trusted, reputable source URL or reference supporting the verdict")
    time_start: str = Field(description="Start timestamp in the video where the claim was made (e.g., '12:34')")
    time_end: str = Field(description="End timestamp in the video where the claim was made (e.g., '12:45')")

class FactCheckResponse(BaseModel):
    claims: list[ClaimResultSchema]

def _get_system_prompt(intensity: str) -> str:
    depth_rule = {
        "lenient": "Only extract major, high-impact claims (numbers, policies, major events). Ignore minor details.",
        "balanced": "Extract all statistics, dates, policy references, and significant factual statements.",
        "strict": "Extract every verifiable detail, including names, minor stats, promises, and tangential claims."
    }.get(intensity, "Extract factual claims.")

    return f"""You are a ruthless, highly accurate fact-checker analyzing a video transcript.
The transcript may be auto-generated. Expect missing punctuation and phonetic spelling errors. Infer the true meaning from context.

Instructions:
1. Ignore subjective opinions, greetings, and filler.
2. {depth_rule}
3. For each claim, determine the verdict:
   - "NO CAP": The claim is factually accurate.
   - "CAP": The claim is false or fabricated.
   - "YAPPIN": The claim is misleading, exaggerated, or lacks critical context.
4. Provide a factual correction/clarification.
5. Provide a trusted, reputable source backing your correction.
"""

def _fact_check_gemini(text: str, config: YapnCapConfig) -> list[ClaimResult]:
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=config.api_key)
    prompt = _get_system_prompt(config.intensity)
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=f"{prompt}\n\nTranscript:\n{text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FactCheckResponse,
            tools=[{"google_search": {}}],
            temperature=0.1
        )
    )
    
    if not response.text:
        return []
    
    data = json.loads(response.text)
    claims = data.get("claims", [])
    return [ClaimResult(**c) for c in claims]

def _fact_check_openai(text: str, config: YapnCapConfig) -> list[ClaimResult]:
    import openai
    
    client = openai.OpenAI(api_key=config.api_key)
    prompt = _get_system_prompt(config.intensity)
    
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Transcript:\n{text}"}
        ],
        response_format=FactCheckResponse,
        temperature=0.1
    )
    
    parsed = response.choices[0].message.parsed
    if not parsed: return []
    return [ClaimResult(**c.model_dump()) for c in parsed.claims]

def _fact_check_groq(text: str, config: YapnCapConfig) -> list[ClaimResult]:
    import groq
    
    client = groq.Groq(api_key=config.api_key)
    prompt = _get_system_prompt(config.intensity)
    
    response = client.chat.completions.create(
        model="groq/compound",
        messages=[
            {"role": "system", "content": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{{'claims': [{{'claim':'...','verdict':'NO CAP|CAP|YAPPIN','correction':'...','source':'...','time_start':'...','time_end':'...'}}]}}"},
            {"role": "user", "content": f"Transcript:\n{text}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    content = response.choices[0].message.content
    if not content: return []
    
    data = json.loads(content)
    return [ClaimResult(**c) for c in data.get("claims", [])]

def fact_check(text: str, config: YapnCapConfig) -> list[ClaimResult]:
    """Routes the fact-checking request to the configured AI provider."""
    if not text or text.startswith("[No CC"):
        return []
        
    if config.provider == "gemini":
        return _fact_check_gemini(text, config)
    elif config.provider == "openai":
        return _fact_check_openai(text, config)
    elif config.provider == "groq":
        return _fact_check_groq(text, config)
    else:
        raise ValueError(f"Unknown AI provider: {config.provider}")
