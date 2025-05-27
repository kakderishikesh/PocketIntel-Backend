import asyncio
import httpx
from typing import List, Dict, Any
from config import PERPLEXITY_API_KEY

API_URL = "https://api.perplexity.ai/chat/completions"


async def fetch_single_prompt(client: httpx.AsyncClient, prompt: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Be concise and informative. Include sources always."},
            {"role": "user", "content": prompt["prompt"]}
        ],
        "temperature": 0.4,
        "max_tokens": 500,
        "web_search_options": {
            "search_context_size": prompt.get("context_size", "medium")
        }
    }

    if prompt.get("after_date"):
        payload["search_after_date_filter"] = prompt["after_date"]
    if prompt.get("before_date"):
        payload["search_before_date_filter"] = prompt["before_date"]

    try:
        response = await client.post(API_URL, json=payload)
        response.raise_for_status()
        json_data = response.json()
        message = json_data["choices"][0]["message"]
        content = message.get("content", "")
        citations = json_data.get("citations", [])
        return {
            "pillar": prompt["pillar"],
            "content": content,
            "citations": citations
        }
    except Exception as e:
        return {
            "pillar": prompt["pillar"],
            "content": f"[ERROR] {e}",
            "citations": []
        }


async def fetch_sonar_responses(prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        tasks = [fetch_single_prompt(client, p) for p in prompts]
        return await asyncio.gather(*tasks)
