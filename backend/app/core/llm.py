"""LLM service for analyzing articles and generating trading strategies."""
import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import get_settings
from app.core.resilience import retry_on_exception, with_fallback

logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize OpenAI client
client: Optional[OpenAI] = None
if settings.llm_enabled:
    client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are an equity analyst bot. Extract precise, trade-relevant structure from market news for educational use. Be conservative; if facts are missing, say so. Output ONLY a JSON object with the fields requested."""

SCHEMA_HINT = """
Return JSON with these fields:
{
  "ticker": "<string or empty>",
  "sector": "<string>",
  "catalyst_type": "EARNINGS|FDA|M&A|CONTRACT|GUIDANCE|MACRO|OTHER",
  "stance": "BULLISH|BEARISH|NEUTRAL",
  "thesis": "<1-2 sentences>",
  "key_facts": ["<short>", "<short>"],
  "near_term_window_days": <int>,
  "confidence_0to1": <float>,
  "risks": ["<short>", "<short>"],
  "suggested_setups": [
    {"style":"MOMENTUM|SWING|DCA|PAIRS|AVOID","entry_hint":"<short>","invalidations":"<short>","hold_time_days":<int>}
  ],
  "simple_explanation": "<2-3 sentences in plain English for investing beginners, avoiding jargon like 'swing', 'entry', 'stop-loss'>",
  "summary": "<2-sentence TL;DR suitable for mobile notifications>"
}
"""


def build_user_prompt(article: Dict[str, Any]) -> str:
    """Build the user prompt from article data."""
    return f"""Use this news to produce a structured catalyst and a short-term plan.
Headline: {article.get('title', '')}
Summary: {article.get('summary', '')}
Source: {article.get('source_name', '')} ({article.get('source_url', '')}), Published: {article.get('published_at', '')}
URL: {article.get('url', '')}
My rules scores: catalyst={article.get('rule_catalyst', 0)}, novelty={article.get('rule_novelty', 0)}, credibility={article.get('rule_credibility', 0)}
{SCHEMA_HINT}
Return ONLY JSON, no prose.
"""


@retry_on_exception(max_attempts=3, min_wait=2, max_wait=10)
def analyze_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze an article using OpenAI and return structured trading plan.

    Includes automatic retry logic with exponential backoff for transient failures.

    Args:
        article: Dictionary containing article data (title, summary, url, etc.)

    Returns:
        Dictionary containing the LLM analysis result

    Raises:
        ValueError: If LLM is not enabled
        Exception: If OpenAI API call fails after retries
    """
    if not settings.llm_enabled or not client:
        raise ValueError("LLM analysis is not enabled. Please set OPENAI_API_KEY in .env")

    try:
        logger.info(f"Analyzing article: {article.get('title', 'Unknown')[:50]}...")

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(article)}
            ],
            response_format={"type": "json_object"},  # Ensures JSON object output
            # Note: gpt-5-mini only supports default temperature (1.0)
        )

        # Extract the JSON from the response
        result = json.loads(response.choices[0].message.content)

        logger.info(f"Successfully analyzed article. Ticker: {result.get('ticker', 'N/A')}, Stance: {result.get('stance', 'N/A')}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise Exception(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Error analyzing article with LLM: {e}")
        raise Exception(f"LLM analysis failed: {e}")

