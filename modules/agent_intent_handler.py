import requests
import json
from config import PERPLEXITY_API_KEY

API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_PILLARS = ["financial", "news", "market", "adoption", "competitor", "contextual"]


def get_subject_and_focus_from_agent(query: str) -> dict:
    """
    Uses Perplexity Sonar to detect:
    - Whether a query is a direct factual request or a broader analysis
    - Extracts subject, focus, sector, and ticker
    - Includes citations if a direct answer is returned
    """
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that detects whether a query needs analytical breakdown "
                    "(like financial, market, news, competitor analysis, adoption, contextual), or is a factual question that can be directly answered with citations.\n"
                    "Also assign a sector from the following ['Technology', 'Healthcare', 'Financials', 'Consumer Discretionary', 'Industrials', 'Materials', 'Utilities', 'Real Estate', 'Communication Services'].\n"
                    "Also assign a stock ticker to the subject if possible.\n"
                    "Respond ONLY in this strict JSON format:\n"
                    '{ \"type\": \"analysis\" or \"direct_answer\", \"subject\": \"string\", \"focus\": [\"pillar1\", ...], \"sector\": \"string\", \"ticker\": \"string\", \"answer\": \"...\" }\n\n'
                    "Examples:\n"
                    "- \"whats up with nvidia this week\" → {\"type\": \"analysis\", \"subject\": \"Nvidia\", \"focus\": [\"news\", \"market\"], \"sector\": \"Technology\", \"ticker\": \"NVDA\"}\n"
                    "- \"what is the stock price of nvidia?\" → {\"type\": \"direct_answer\", \"subject\": \"Nvidia\", \"focus\": [], \"sector\": \"Technology\", \"ticker\": \"NVDA\", \"answer\": \"Nvidia is trading at $X.XX\"}\n"
                )
            },
            {"role": "user", "content": query}
        ]
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        res.raise_for_status()

        res_data = res.json()
        message = res_data["choices"][0]["message"]
        citations = res_data.get("citations", [])
        content = message.get("content", "").strip()

        # Attempt to extract JSON block from content
        try:
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            parsed = json.loads(content[json_start:json_end])
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[Agent Intent Parsing Error] Failed to parse content: {e}")
            print("Raw content:", content)
            return {
                "type": "analysis",
                "subject": "Unknown",
                "focus": DEFAULT_PILLARS,
                "sector": "",
                "ticker": "",
                "answer": "",
                "citations": citations
            }

        output = {
            "type": parsed.get("type", "analysis"),
            "subject": parsed.get("subject", "Unknown"),
            "focus": [f for f in parsed.get("focus", DEFAULT_PILLARS) if f in DEFAULT_PILLARS],
            "answer": parsed.get("answer", ""),
            "sector": parsed.get("sector", ""),
            "ticker": parsed.get("ticker", "")
        }

        if output["type"] == "analysis" and not output["focus"]:
            output["focus"] = DEFAULT_PILLARS

        output["citations"] = citations

        return output

    except Exception as e:
        print(f"[Agent Intent Parsing Error] {e}")
        return {
            "type": "analysis",
            "subject": "Unknown",
            "focus": DEFAULT_PILLARS,
            "sector": "",
            "ticker": "",
            "answer": "",
            "citations": []
        }
